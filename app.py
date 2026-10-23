import os
import time
import numpy as np
import cv2
import joblib
from collections import Counter
from flask import Flask, render_template, request, jsonify, Response
from PIL import Image
import io
import sys
import json
from language_packages import generate_language_package, LANGUAGE_META

import database as db
from train import extract_image_features
from features import extract_thermal_index
from treatment_protocols import get_comprehensive_treatment_protocol
from disease_formatter import format_disease_prediction
from agri_bot import get_agri_bot_response
from agri_pesticides_db import get_crop_agronomy, EXPANDED_PLANT_AGRONOMY, PESTICIDE_CATEGORIES, PESTICIDES_CATALOG
from report_generator import build_diagnostic_pdf_bytes

try:
    from auto_plant_scanner import run_pipeline_and_predict as run_dl_pipeline
except Exception as e:
    run_dl_pipeline = None
    print("[!] Warning: Could not load auto_plant_scanner DL pipeline:", e)

app = Flask(__name__)
db.ensure_admin_exists()

# --- MODEL LOADING LOGIC ---
MODELS_DIR = "models"

def load_trained_models():
    try:
        pca = joblib.load(os.path.join(MODELS_DIR, 'pca.joblib'))
        svm = joblib.load(os.path.join(MODELS_DIR, 'svm.joblib'))
        mlp = joblib.load(os.path.join(MODELS_DIR, 'mlp.joblib'))
        knn = joblib.load(os.path.join(MODELS_DIR, 'knn.joblib'))
        rf = joblib.load(os.path.join(MODELS_DIR, 'rf.joblib'))
        classes = joblib.load(os.path.join(MODELS_DIR, 'classes.joblib'))
        print(f"[*] Successfully loaded all 5 ML models and {len(classes)} classes from '{MODELS_DIR}/'.")
        return pca, svm, mlp, knn, rf, classes
    except Exception as e:
        print(f"[!] Warning: Could not load trained models from '{MODELS_DIR}/': {e}")
        return None, None, None, None, None, None

pca_model, svm_model, mlp_model, knn_model, rf_model, class_dict = load_trained_models()

PLANT_STATISTICS = EXPANDED_PLANT_AGRONOMY

def predict_with_all_models(cv_img):
    """
    Executes inference across all 4 machine learning classifiers:
    1. Calibrated Support Vector Machine (SVM)
    2. Multilayer Perceptron (MLP) Neural Network
    3. Random Forest (RF)
    4. K-Nearest Neighbors (KNN)
    Returns: list of results, top-3 candidates, consensus info.
    """
    if pca_model is None or class_dict is None:
        return None, None, None

    # Feature extraction (4096-dim vector)
    features = extract_image_features(cv_img)
    if features is None:
        return None, None, None

    # PCA transformation (128 principal components)
    feat_pca = pca_model.transform(features.reshape(1, -1))

    model_suite = [
        ("Calibrated SVM (RBF Kernel)", svm_model),
        ("Multilayer Perceptron (MLP Neural Net)", mlp_model),
        ("Random Forest Classifier (RF)", rf_model),
        ("K-Nearest Neighbors (KNN)", knn_model)
    ]

    all_results = []
    class_votes = Counter()
    weighted_votes = Counter()
    candidate_probs = {}

    for name, model in model_suite:
        if model is None:
            continue
        try:
            pred_idx = int(model.predict(feat_pca)[0])
            raw_class = class_dict.get(pred_idx, "Unknown")
            
            # Extract probability distribution
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(feat_pca)[0]
                conf = float(probs[pred_idx])
                # Track top candidate probabilities
                for c_idx, prob in enumerate(probs):
                    c_name = class_dict.get(c_idx, f"Class_{c_idx}")
                    candidate_probs[c_name] = candidate_probs.get(c_name, 0.0) + float(prob)
            else:
                conf = 0.85

            class_votes[raw_class] += 1
            weighted_votes[raw_class] += conf

            # Format human-friendly display name
            formatted = format_disease_prediction(raw_class, conf * 100)

            all_results.append({
                "algorithm": name,
                "raw_class": raw_class,
                "class_name": raw_class,
                "display_name": formatted["full_display"],
                "crop": formatted["crop"],
                "disease_name": formatted["disease_name"],
                "pathogen_type": formatted["pathogen_type"],
                "badge_class": formatted["badge_class"],
                "confidence": round(conf, 4),
                "is_healthy": formatted["is_healthy"]
            })
        except Exception as err:
            print(f"[!] Error in {name} inference: {err}")

    # Top 3 Candidates
    num_models = len(all_results)
    sorted_candidates = []
    if candidate_probs and num_models > 0:
        for c_name, total_p in sorted(candidate_probs.items(), key=lambda x: x[1], reverse=True)[:3]:
            avg_p = (total_p / num_models) * 100
            fmt = format_disease_prediction(c_name, avg_p)
            sorted_candidates.append({
                "class_name": c_name,
                "display_name": fmt["full_display"],
                "pathogen_type": fmt["pathogen_type"],
                "probability": round(avg_p, 1)
            })

    # Determine Winning Class via Weighted Ensemble Consensus
    if weighted_votes:
        winning_class = weighted_votes.most_common(1)[0][0]
        vote_count = class_votes[winning_class]
        consensus_score = round((vote_count / num_models) * 100, 1)
    else:
        winning_class = all_results[0]["raw_class"]
        consensus_score = 100.0
        vote_count = num_models

    consensus_info = {
        "score_pct": consensus_score,
        "agreeing_models": vote_count,
        "total_models": num_models,
        "agreement_text": f"{vote_count} of {num_models} models agree ({consensus_score}% consensus)",
        "top_candidates": sorted_candidates
    }

    return all_results, winning_class, consensus_info


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    success, message = db.create_user(data)
    return jsonify({"success": success, "message": message}), (200 if success else 400)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    
    success, approved, message, profile = db.verify_user(username, password)
    if success and approved:
        return jsonify({
            "success": True,
            "message": "Login successful!",
            "username": username,
            "profile": profile
        })
    elif success and not approved:
        return jsonify({"success": False, "message": message}), 403
    else:
        return jsonify({"success": False, "message": message}), 401


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json or {}
    username = data.get('username', '').strip()
    new_password = data.get('new_password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()
    
    if not username:
        return jsonify({"success": False, "message": "Please enter your username."}), 400
    if not new_password:
        return jsonify({"success": False, "message": "Please enter a new password."}), 400
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match. Please try again."}), 400
    
    success, message = db.reset_password(username, new_password)
    return jsonify({"success": success, "message": message}), (200 if success else 400)


@app.route('/api/user/language', methods=['POST'])
def set_user_language():
    data = request.json or {}
    username = data.get('username', '').strip()
    language = data.get('language', 'en').strip()
    if not username:
        return jsonify({"success": False, "message": "Username required."}), 400
    success = db.update_user_language(username, language)
    return jsonify({"success": success, "language": language})


@app.route('/api/language-package/<lang_code>', methods=['GET'])
def get_language_package_json(lang_code):
    package = generate_language_package(lang_code)
    return jsonify({"success": True, "package": package})


@app.route('/api/download-language-package/<lang_code>', methods=['GET'])
def download_language_package_file(lang_code):
    package = generate_language_package(lang_code)
    content = json.dumps(package, indent=2, ensure_ascii=False)
    filename = f"agri_language_pack_{lang_code}.json"
    return Response(
        content,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route('/api/regions', methods=['GET'])
def get_regions():
    try:
        from india_agri_db import STATES_DATA
    except Exception as e:
        return jsonify({})

    DISTRICTS_MAP = {
        'Andhra Pradesh': ['Anantapur', 'Chittoor', 'East Godavari', 'Guntur', 'Krishna', 'Kurnool', 'Prakasam', 'Srikakulam', 'Visakhapatnam', 'Vizianagaram', 'West Godavari', 'Y.S.R. Kadapa'],
        'Arunachal Pradesh': ['Tawang', 'West Kameng', 'East Kameng', 'Papum Pare', 'Kurung Kumey', 'Kra Daadi', 'Lower Subansiri', 'Upper Subansiri', 'West Siang', 'East Siang', 'Siang', 'Upper Siang'],
        'Assam': ['Baksa', 'Barpeta', 'Biswanath', 'Bongaigaon', 'Cachar', 'Charaideo', 'Chirang', 'Darrang', 'Dhemaji', 'Dhubri', 'Dibrugarh', 'Goalpara', 'Golaghat', 'Hailakandi', 'Hojai', 'Jorhat', 'Kamrup', 'Kamrup Metropolitan', 'Karbi Anglong'],
        'Bihar': ['Araria', 'Arwal', 'Aurangabad', 'Banka', 'Begusarai', 'Bhagalpur', 'Bhojpur', 'Buxar', 'Darbhanga', 'East Champaran', 'Gaya', 'Gopalganj', 'Jamui', 'Jehanabad', 'Kaimur', 'Katihar', 'Khagaria', 'Kishanganj', 'Lakhisarai', 'Madhepura', 'Madhubani', 'Munger'],
        'Chhattisgarh': ['Balod', 'Baloda Bazar', 'Balrampur', 'Bastar', 'Bemetara', 'Bijapur', 'Bilaspur', 'Dantewada', 'Dhamtari', 'Durg', 'Gariaband', 'Janjgir-Champa', 'Jashpur', 'Kabirdham', 'Kanker', 'Kondagaon', 'Korba', 'Koriya', 'Mahasamund', 'Mungeli', 'Narayanpur', 'Raigarh', 'Raipur', 'Rajnandgaon', 'Sukma', 'Surajpur', 'Surguja'],
        'Goa': ['North Goa', 'South Goa'],
        'Gujarat': ['Ahmedabad', 'Amreli', 'Anand', 'Aravalli', 'Banaskantha', 'Bharuch', 'Bhavnagar', 'Botad', 'Chhota Udaipur', 'Dahod', 'Dang', 'Devbhoomi Dwarka', 'Gandhinagar', 'Gir Somnath', 'Jamnagar', 'Junagadh', 'Kheda', 'Kutch', 'Mahisagar', 'Mehsana', 'Morbi', 'Narmada', 'Navsari', 'Panchmahal', 'Patan', 'Porbandar', 'Rajkot', 'Sabarkantha', 'Surat', 'Surendranagar', 'Tapi', 'Vadodara', 'Valsad'],
        'Haryana': ['Ambala', 'Bhiwani', 'Charkhi Dadri', 'Faridabad', 'Fatehabad', 'Gurugram', 'Hisar', 'Jhajjar', 'Jind', 'Kaithal', 'Karnal', 'Kurukshetra', 'Mahendragarh', 'Nuh', 'Palwal', 'Panchkula', 'Panipat', 'Rewari', 'Rohtak', 'Sirsa', 'Sonipat', 'Yamunanagar'],
        'Himachal Pradesh': ['Bilaspur', 'Chamba', 'Hamirpur', 'Kangra', 'Kinnaur', 'Kullu', 'Lahaul and Spiti', 'Mandi', 'Shimla', 'Sirmaur', 'Solan', 'Una'],
        'Jharkhand': ['Bokaro', 'Chatra', 'Deoghar', 'Dhanbad', 'Dumka', 'East Singhbhum', 'Garhwa', 'Giridih', 'Godda', 'Gumla', 'Hazaribag', 'Jamtara', 'Khunti', 'Koderma', 'Latehar', 'Lohardaga', 'Pakur', 'Palamu', 'Ramgarh', 'Ranchi', 'Sahibganj', 'Seraikela-Kharsawan', 'Simdega', 'West Singhbhum'],
        'Karnataka': ['Bagalkot', 'Ballari', 'Belagavi', 'Bengaluru Rural', 'Bengaluru Urban', 'Bidar', 'Chamarajanagar', 'Chikballapur', 'Chikkamagaluru', 'Chitradurga', 'Dakshina Kannada', 'Davangere', 'Dharwad', 'Gadag', 'Hassan', 'Haveri', 'Kalaburagi', 'Kodagu', 'Kolar', 'Koppal', 'Mandya', 'Mysuru', 'Raichur', 'Ramanagara', 'Shivamogga', 'Tumakuru', 'Udupi', 'Uttara Kannada', 'Vijayapura', 'Yadgir'],
        'Kerala': ['Alappuzha', 'Ernakulam', 'Idukki', 'Kannur', 'Kasaragod', 'Kollam', 'Kottayam', 'Kozhikode', 'Malappuram', 'Palakkad', 'Pathanamthitta', 'Thiruvananthapuram', 'Thrissur', 'Wayanad'],
        'Madhya Pradesh': ['Agar Malwa', 'Alirajpur', 'Anuppur', 'Ashoknagar', 'Balaghat', 'Barwani', 'Betul', 'Bhind', 'Bhopal', 'Burhanpur', 'Chhatarpur', 'Chhindwara', 'Damoh', 'Datia', 'Dewas', 'Dhar', 'Dindori', 'Guna', 'Gwalior', 'Harda', 'Hoshangabad', 'Indore', 'Jabalpur', 'Jhabua', 'Katni', 'Khandwa', 'Khargone', 'Mandla', 'Mandsaur', 'Morena', 'Narsinghpur', 'Neemuch', 'Panna', 'Raisen', 'Rajgarh', 'Ratlam', 'Rewa', 'Sagar', 'Satna', 'Sehore', 'Seoni', 'Shahdol', 'Shajapur', 'Sheopur', 'Shivpuri', 'Sidhi', 'Singrauli', 'Tikamgarh', 'Ujjain', 'Umaria', 'Vidisha'],
        'Maharashtra': ['Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara', 'Buldhana', 'Chandrapur', 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 'Kolhapur', 'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 'Nandurbar', 'Nashik', 'Osmanabad', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 'Ratnagiri', 'Sangli', 'Satara', 'Sindhudurg', 'Solapur', 'Thane', 'Wardha', 'Washim', 'Yavatmal'],
        'Manipur': ['Bishnupur', 'Chandel', 'Churachandpur', 'Imphal East', 'Imphal West', 'Jiribam', 'Kakching', 'Kamjong', 'Kangpokpi', 'Noney', 'Pherzawl', 'Senapati', 'Tamenglong', 'Tengnoupal', 'Thoubal', 'Ukhrul'],
        'Meghalaya': ['East Garo Hills', 'East Jaintia Hills', 'East Khasi Hills', 'North Garo Hills', 'Ri Bhoi', 'South Garo Hills', 'South West Garo Hills', 'South West Khasi Hills', 'West Garo Hills', 'West Jaintia Hills', 'West Khasi Hills'],
        'Mizoram': ['Aizawl', 'Champhai', 'Kolasib', 'Lawngtlai', 'Lunglei', 'Mamit', 'Saiha', 'Serchhip'],
        'Nagaland': ['Dimapur', 'Kiphire', 'Kohima', 'Longleng', 'Mokokchung', 'Mon', 'Peren', 'Phek', 'Tuensang', 'Wokha', 'Zunheboto'],
        'Odisha': ['Angul', 'Balangir', 'Balasore', 'Bargarh', 'Bhadrak', 'Boudh', 'Cuttack', 'Deogarh', 'Dhenkanal', 'Gajapati', 'Ganjam', 'Jagatsinghapur', 'Jajpur', 'Jharsuguda', 'Kalahandi', 'Kandhamal', 'Kendrapara', 'Kendujhar', 'Khordha', 'Koraput', 'Malkangiri', 'Mayurbhanj', 'Nabarangpur', 'Nayagarh', 'Nuapada', 'Puri', 'Rayagada', 'Sambalpur', 'Sonepur', 'Sundargarh'],
        'Punjab': ['Amritsar', 'Barnala', 'Bathinda', 'Faridkot', 'Fatehgarh Sahib', 'Fazilka', 'Ferozepur', 'Gurdaspur', 'Hoshiarpur', 'Jalandhar', 'Kapurthala', 'Ludhiana', 'Mansa', 'Moga', 'Muktsar', 'Nawanshahr', 'Pathankot', 'Patiala', 'Rupnagar', 'Mohali', 'Sangrur', 'Tarn Taran'],
        'Rajasthan': ['Ajmer', 'Alwar', 'Banswara', 'Baran', 'Barmer', 'Bharatpur', 'Bhilwara', 'Bikaner', 'Bundi', 'Chittorgarh', 'Churu', 'Dausa', 'Dholpur', 'Dungarpur', 'Hanumangarh', 'Jaipur', 'Jaisalmer', 'Jalore', 'Jhalawar', 'Jhunjhunu', 'Jodhpur', 'Karauli', 'Kota', 'Nagaur', 'Pali', 'Pratapgarh', 'Rajsamand', 'Sawai Madhopur', 'Sikar', 'Sirohi', 'Sri Ganganagar', 'Tonk', 'Udaipur'],
        'Sikkim': ['East Sikkim', 'North Sikkim', 'South Sikkim', 'West Sikkim'],
        'Tamil Nadu': ['Ariyalur', 'Chennai', 'Coimbatore', 'Cuddalore', 'Dharmapuri', 'Dindigul', 'Erode', 'Kanchipuram', 'Kanyakumari', 'Karur', 'Krishnagiri', 'Madurai', 'Nagapattinam', 'Namakkal', 'Nilgiris (Ooty)', 'Perambalur', 'Pudukkottai', 'Ramanathapuram', 'Salem', 'Sivaganga', 'Thanjavur', 'Theni', 'Thoothukudi', 'Tiruchirappalli', 'Tirunelveli', 'Tiruppur', 'Tiruvallur', 'Tiruvannamalai', 'Tiruvarur', 'Vellore', 'Viluppuram', 'Virudhunagar'],
        'Telangana': ['Adilabad', 'Bhadradri Kothagudem', 'Hyderabad', 'Jagtial', 'Jangaon', 'Jayashankar Bhoopalpally', 'Jogulamba Gadwal', 'Kamareddy', 'Karimnagar', 'Khammam', 'Komaram Bheem Asifabad', 'Mahabubabad', 'Mahabubnagar', 'Mancherial', 'Medak', 'Medchal', 'Nagarkurnool', 'Nalgonda', 'Nirmal', 'Nizamabad', 'Peddapalli', 'Rajanna Sircilla', 'Rangareddy', 'Sangareddy', 'Siddipet', 'Suryapet', 'Vikarabad', 'Wanaparthy', 'Warangal', 'Yadadri Bhuvanagiri'],
        'Tripura': ['Dhalai', 'Gomati', 'Khowai', 'North Tripura', 'Sepahijala', 'South Tripura', 'Unakoti', 'West Tripura'],
        'Uttar Pradesh': ['Agra', 'Aligarh', 'Allahabad', 'Ambedkar Nagar', 'Amethi', 'Amroha', 'Auraiya', 'Azamgarh', 'Baghpat', 'Bahraich', 'Ballia', 'Balrampur', 'Banda', 'Barabanki', 'Bareilly', 'Basti', 'Bhadohi', 'Bijnor', 'Budaun', 'Bulandshahr', 'Chandauli', 'Chitrakoot', 'Deoria', 'Etah', 'Etawah', 'Faizabad', 'Farrukhabad', 'Fatehpur', 'Firozabad', 'Gautam Buddha Nagar', 'Ghaziabad', 'Ghazipur', 'Gonda', 'Gorakhpur', 'Hamirpur', 'Hapur', 'Hardoi', 'Hathras', 'Jalaun', 'Jaunpur', 'Jhansi', 'Kannauj', 'Kanpur Dehat', 'Kanpur Nagar', 'Kasganj', 'Kaushambi', 'Kushinagar', 'Lakhimpur Kheri', 'Lalitpur', 'Lucknow', 'Maharajganj', 'Mahoba', 'Mainpuri', 'Mathura', 'Mau', 'Meerut', 'Mirzapur', 'Moradabad', 'Muzaffarnagar', 'Pilibhit', 'Pratapgarh', 'RaeBareli', 'Rampur', 'Saharanpur', 'Sambhal', 'Sant Kabir Nagar', 'Shahjahanpur', 'Shamali', 'Shravasti', 'Siddharth Nagar', 'Sitapur', 'Sonbhadra', 'Sultanpur', 'Unnao', 'Varanasi'],
        'Uttarakhand': ['Almora', 'Bageshwar', 'Chamoli', 'Champawat', 'Dehradun', 'Haridwar', 'Nainital', 'Pauri Garhwal', 'Pithoragarh', 'Rudraprayag', 'Tehri Garhwal', 'Udham Singh Nagar', 'Uttarkashi'],
        'West Bengal': ['Alipurduar', 'Bankura', 'Birbhum', 'Burdwan', 'Cooch Behar', 'Dakshin Dinajpur', 'Darjeeling', 'Hooghly', 'Howrah', 'Jalpaiguri', 'Kalimpong', 'Kolkata', 'Malda', 'Murshidabad', 'Nadia', 'North 24 Parganas', 'Paschim Medinipur', 'Purba Medinipur', 'Purulia', 'South 24 Parganas', 'Uttar Dinajpur']
    }
    
    regions_data = {}
    for s in STATES_DATA:
        state_name = s['state']
        regions_data[state_name] = {
            "districts": DISTRICTS_MAP.get(state_name, ["Central", "North", "South", "East", "West"]),
            "crops": s.get('major_crops', []),
            "climate": s.get('climate', 'Moderate'),
            "pesticides": s.get('commonly_used_pesticides', []),
            "organic_mandate": s.get('is_organic_mandate', False)
        }
    return jsonify(regions_data)


@app.route('/api/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No leaf image uploaded."}), 400
        
    file = request.files['image']
    plant_type_input = request.form.get('plant_type', '').strip()
    username = request.form.get('username', '').strip()
    state = request.form.get('state', '').strip()
    district = request.form.get('district', '').strip()

    try:
        # Load and convert image
        image_pil = Image.open(file.stream)
        if image_pil.mode == 'RGBA':
            image_pil = image_pil.convert('RGB')
        
        cv_img_rgb = np.array(image_pil)
        cv_img_bgr = cv2.cvtColor(cv_img_rgb, cv2.COLOR_RGB2BGR)

        # 1. Thermal & Foliar Water-Stress Analysis
        thermal_metrics = extract_thermal_index(cv_img_bgr)

        # 2. Multi-Model Inference (SVM, MLP, RF, KNN)
        all_results, winning_class, consensus_info = predict_with_all_models(cv_img_bgr)
        
        # Deep Learning pipeline if present
        if run_dl_pipeline:
            try:
                dl_res = run_dl_pipeline(cv_img_bgr)
                all_results.append({
                    "algorithm": "Deep Learning (Automated Site-Specific Pesticide Application)",
                    "raw_class": dl_res.get('prediction', 'Unknown'),
                    "class_name": dl_res.get('prediction', 'Unknown'),
                    "display_name": f"Deep Learning: {dl_res.get('prediction', 'Analyzed Specimen')}",
                    "crop": plant_type_input or "Foliar Specimen",
                    "disease_name": dl_res.get('prediction', 'Unknown'),
                    "pathogen_type": "Foliar Defect",
                    "badge_class": "badge-fungal",
                    "confidence": round(float(dl_res.get('confidence', 90.0)) / 100.0, 4),
                    "is_healthy": "healthy" in dl_res.get('prediction', '').lower()
                })
            except Exception as e:
                print("[!] DL sub-pipeline exception:", e)

        # Pick primary winning prediction
        if not all_results:
            return jsonify({"success": False, "message": "Model inference failed. Ensure models are trained."}), 500

        # Best result candidate
        best_cand = max(all_results, key=lambda x: x['confidence'])
        best_raw_class = winning_class or best_cand['class_name']
        best_confidence = best_cand['confidence'] * 100.0

        # 3. Comprehensive Treatment & Phytopathology Protocol
        protocol = get_comprehensive_treatment_protocol(
            best_raw_class,
            confidence=best_confidence,
            thermal_metrics=thermal_metrics,
            state=state,
            district=district
        )

        detected_crop = protocol["pathology"]["crop"]
        if not plant_type_input:
            plant_type_input = detected_crop

        # 4. Plant Growth Intelligence (Water, Irrigation, Soil)
        plant_stats = protocol.get("plant_stats") or get_crop_agronomy(plant_type_input)

        # 5. Climate Context
        climate_summary = {
            "state": state or "General Agricultural Zone",
            "district": district or "Not specified",
            "condition": "Tropical / Temperate Agro-Climatic Zone",
            "recommendation": protocol["risk_forecast"]["climate_warning"]
        }

        # 6. Save Image to Dataset for Continual Learning
        try:
            safe_folder = f"{plant_type_input}_{protocol['pathology']['disease_name']}".replace(' ', '_').replace('/', '_')
            dataset_dir = os.path.join('dataset', safe_folder)
            os.makedirs(dataset_dir, exist_ok=True)
            image_pil.save(os.path.join(dataset_dir, f"{int(time.time())}.jpg"))
        except:
            pass

        # 7. Persist to User History for Personal Analytics
        primary_chem = protocol["chemical_pesticides"][0]["name"] if protocol["chemical_pesticides"] else "None"
        primary_dosage = protocol["chemical_pesticides"][0]["dosage"] if protocol["chemical_pesticides"] else "0 ml/L"

        if username:
            db.save_prediction_history(username, {
                "crop": detected_crop,
                "plant_type": plant_type_input,
                "class_name": best_raw_class,
                "disease_name": protocol["pathology"]["disease_name"],
                "full_display": protocol["pathology"]["full_display"],
                "scientific_name": protocol["pathology"]["scientific_name"],
                "pathogen_type": protocol["pathology"]["pathogen_type"],
                "is_healthy": protocol["pathology"]["is_healthy"],
                "severity_tier": protocol["severity"]["tier"],
                "severity_badge": protocol["severity"]["badge"],
                "confidence": round(best_confidence / 100.0, 4),
                "algorithm": best_cand["algorithm"],
                "pesticide": primary_chem,
                "amount": primary_dosage,
                "precautions": protocol["immediate_actions"][0] if protocol["immediate_actions"] else "Maintain crop health",
                "state": state,
                "district": district,
                "cwsi_index": protocol["severity"]["cwsi_index"],
                "necrosis_ratio": protocol["severity"]["necrosis_ratio"]
            })

        # Structured response containing rich diagnostic outputs
        return jsonify({
            "success": True,
            "best": {
                "algorithm": best_cand["algorithm"],
                "class_name": best_raw_class,
                "display_name": protocol["pathology"]["full_display"],
                "confidence": round(best_confidence, 2),
                "pesticide": primary_chem,
                "amount": primary_dosage,
                "precautions": protocol["immediate_actions"][0] if protocol["immediate_actions"] else "Monitor crops"
            },
            "pathology": protocol["pathology"],
            "severity": protocol["severity"],
            "action_plan": {
                "immediate_actions": protocol["immediate_actions"],
                "organic_solutions": protocol["organic_solutions"],
                "chemical_pesticides": protocol["chemical_pesticides"],
                "nutrition_management": protocol["nutrition_management"],
                "prevention_methods": protocol["prevention_methods"],
                "resistance_management": protocol["resistance_management"]
            },
            "risk_forecast": protocol["risk_forecast"],
            "pesticide_field_quantities": protocol["pesticide_field_quantities"],
            "symptom_description": protocol["symptom_description"],
            "safety_guidelines": protocol["safety_guidelines"],
            "ppe_checklist": protocol["ppe_checklist"],
            "scientific_cure_summary": protocol.get("scientific_cure_summary", ""),
            "all_results": all_results,
            "ensemble_consensus": consensus_info,
            "plant_stats": plant_stats,
            "pesticide_guidance": protocol.get("pesticide_category_guidance", {}),
            "climate": climate_summary,
            "plant_type": plant_type_input,
            "state": state,
            "district": district
        })

    except Exception as e:
        print("[!] Error in /api/predict:", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/history/<username>', methods=['GET'])
def get_history(username):
    history = db.get_user_history(username)
    return jsonify({"success": True, "history": history})


@app.route('/api/analytics/<username>', methods=['GET'])
def user_analytics(username):
    """
    Computes comprehensive, personalized agronomic analytics for each individual user:
    - KPIs: Total Scans, Health Rate %, Diagnostic Certainty, High Risk Count
    - Distributions: Diseases, Crops, Pathogens (Fungal/Bacterial/Viral/Healthy), Severity Tiers
    - Timeline: Daily activity tracking healthy vs diseased specimens
    - Dynamic AI Insights based on user scan patterns.
    """
    history = db.get_user_history(username)
    if not history:
        return jsonify({
            "success": True,
            "analytics": {
                "username": username,
                "total_analyses": 0,
                "total_scans": 0,
                "healthy_count": 0,
                "healthy_pct": 0.0,
                "infected_count": 0,
                "infection_pct": 0.0,
                "avg_confidence": 0.0,
                "max_confidence": 0.0,
                "top_crop": "None",
                "top_disease": "None",
                "top_pathogen": "None",
                "high_risk_scans": 0,
                "disease_distribution": {},
                "crop_distribution": {},
                "pathogen_breakdown": {},
                "severity_breakdown": {},
                "algorithm_usage": {},
                "regional_distribution": {},
                "timeline": {"dates": [], "counts": [], "healthy_counts": [], "infected_counts": []},
                "recent_scans": [],
                "ai_insights": ["No plant scans recorded yet. Upload a leaf image to generate your field health analytics!"]
            }
        })

    total_scans = len(history)

    # Health vs Diseased Counts
    healthy_scans = [h for h in history if h.get("is_healthy") or "healthy" in h.get("disease_name", "").lower() or "healthy" in h.get("class_name", "").lower()]
    healthy_count = len(healthy_scans)
    infected_count = total_scans - healthy_count
    healthy_pct = round((healthy_count / total_scans) * 100, 1)
    infection_pct = round((infected_count / total_scans) * 100, 1)

    # Confidence Stats
    confs = [float(h.get("confidence", 0.85)) for h in history]
    # Normalize confidences to percentage (0 - 100)
    confs_pct = [c * 100 if c <= 1.0 else c for c in confs]
    avg_conf = round(sum(confs_pct) / len(confs_pct), 1) if confs_pct else 0.0
    max_conf = round(max(confs_pct), 1) if confs_pct else 0.0

    # Categorical Distributions
    disease_counts = Counter(h.get("disease_name", h.get("class_name", "Unknown")) for h in history)
    crop_counts = Counter(h.get("crop", h.get("plant_type", "Foliar Crop")) for h in history)
    pathogen_counts = Counter(h.get("pathogen_type", "Fungal") for h in history)
    algo_counts = Counter(h.get("algorithm", "SVM Ensemble") for h in history)

    # Severity Tiers
    severity_counts = Counter()
    for h in history:
        sev = h.get("severity_tier", "")
        if "Healthy" in sev:
            severity_counts["Healthy"] += 1
        elif "Mild" in sev:
            severity_counts["Mild"] += 1
        elif "Moderate" in sev:
            severity_counts["Moderate"] += 1
        elif "Severe" in sev:
            severity_counts["Severe"] += 1
        else:
            severity_counts["Mild"] += 1

    high_risk_scans = severity_counts.get("Severe", 0) + severity_counts.get("Moderate", 0)

    # Top Crop & Disease
    top_crop = crop_counts.most_common(1)[0][0] if crop_counts else "Unknown"
    top_disease = disease_counts.most_common(1)[0][0] if disease_counts else "None"
    top_pathogen = pathogen_counts.most_common(1)[0][0] if pathogen_counts else "Fungal"

    # Regional Distribution
    reg_counts = Counter()
    for h in history:
        st = h.get("state", "").strip()
        dt = h.get("district", "").strip()
        if st and dt:
            reg_counts[f"{dt}, {st}"] += 1
        elif st:
            reg_counts[st] += 1
        else:
            reg_counts["Local Farm"] += 1

    # Timeline (by Day)
    timeline_totals = Counter()
    timeline_healthy = Counter()
    timeline_infected = Counter()

    for h in history:
        ts = h.get("timestamp", "")
        if ts:
            day = ts[:10]
            timeline_totals[day] += 1
            if h.get("is_healthy") or "healthy" in h.get("disease_name", "").lower():
                timeline_healthy[day] += 1
            else:
                timeline_infected[day] += 1

    sorted_days = sorted(timeline_totals.keys())
    timeline_obj = {
        "dates": sorted_days,
        "counts": [timeline_totals[d] for d in sorted_days],
        "healthy_counts": [timeline_healthy.get(d, 0) for d in sorted_days],
        "infected_counts": [timeline_infected.get(d, 0) for d in sorted_days]
    }

    # Generate Personalized AI Insights
    insights = []
    if healthy_pct >= 60.0:
        insights.append(f"Optimal Field Vigor: {healthy_pct}% of your scanned crops are robust and disease-free. Maintain current watering and sanitation.")
    else:
        insights.append(f"Elevated Pathogen Pressure: {infection_pct}% of scans indicate foliar infections. Implement preventive biopesticide sprays.")

    if pathogen_counts.get("Fungal", 0) > 0:
        fungal_pct = round((pathogen_counts["Fungal"] / total_scans) * 100, 1)
        insights.append(f"Fungal Pathogens Predominate: Fungi account for {fungal_pct}% of foliar issues. Avoid overhead irrigation and ensure 60 cm row ventilation.")

    if pathogen_counts.get("Bacterial", 0) > 0:
        insights.append(f"Bacterial Spot Alert: Sanitize secateurs in 70% alcohol and apply Copper Oxychloride with Streptocycline to prevent vascular spread.")

    if high_risk_scans > 0:
        insights.append(f"Urgent Treatment Needed: You have {high_risk_scans} moderate-to-severe infections. Follow the 24-hour emergency containment protocol.")

    if avg_conf >= 90.0:
        insights.append(f"High Diagnostic Precision: Your average model confidence is {avg_conf}%, ensuring highly accurate treatment prescriptions.")

    # Recent scans summary
    recent = []
    for h in history[:10]:
        recent.append({
            "timestamp": h.get("timestamp", "")[:16].replace("T", " "),
            "crop": h.get("crop", h.get("plant_type", "Crop")),
            "disease_name": h.get("disease_name", h.get("class_name", "Specimen")),
            "scientific_name": h.get("scientific_name", ""),
            "pathogen_type": h.get("pathogen_type", "Fungal"),
            "severity_tier": h.get("severity_tier", "Mild"),
            "confidence": round(float(h.get("confidence", 0.85)) * 100, 1) if float(h.get("confidence", 0.85)) <= 1.0 else round(float(h.get("confidence", 85.0)), 1),
            "pesticide": h.get("pesticide", "None"),
            "is_healthy": h.get("is_healthy", False),
            "location": f"{h.get('district', '')}, {h.get('state', '')}".strip(", ")
        })

    return jsonify({
        "success": True,
        "analytics": {
            "username": username,
            "total_analyses": total_scans,
            "total_scans": total_scans,
            "healthy_count": healthy_count,
            "healthy_pct": healthy_pct,
            "infected_count": infected_count,
            "infection_pct": infection_pct,
            "avg_confidence": avg_conf,
            "max_confidence": max_conf,
            "top_crop": top_crop,
            "top_disease": top_disease,
            "top_pathogen": top_pathogen,
            "high_risk_scans": high_risk_scans,
            "disease_distribution": dict(disease_counts),
            "crop_distribution": dict(crop_counts),
            "pathogen_breakdown": dict(pathogen_counts),
            "severity_breakdown": dict(severity_counts),
            "algorithm_usage": dict(algo_counts),
            "regional_distribution": dict(reg_counts),
            "timeline": timeline_obj,
            "recent_scans": recent,
            "ai_insights": insights
        }
    })


@app.route('/api/analytics/seed/<username>', methods=['POST'])
def seed_analytics(username):
    """Generates realistic sample field data for instant analytics demonstration."""
    if not username:
        return jsonify({"success": False, "message": "Username required"}), 400
    success = db.seed_user_sample_data(username)
    return jsonify({"success": success, "message": f"Seeded sample agricultural scans for @{username}!"})


@app.route('/api/analytics/clear/<username>', methods=['POST'])
def clear_analytics(username):
    """Clears user prediction history."""
    if not username:
        return jsonify({"success": False, "message": "Username required"}), 400
    success = db.clear_user_history(username)
    return jsonify({"success": success, "message": f"Cleared scan history for @{username}."})


# --- ADMIN & CHATBOT ROUTES ---
@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    stats = db.get_all_users_stats()
    return jsonify({"success": True, "users": stats})


@app.route('/api/admin/approve', methods=['POST'])
def admin_approve():
    data = request.json or {}
    username = data.get('username')
    if username == 'admin':
        return jsonify({"success": False})
    if db.approve_user(username):
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route('/api/admin/pending', methods=['GET'])
def admin_pending():
    pending = db.get_pending_users()
    return jsonify({"success": True, "pending": pending, "count": len(pending)})


@app.route('/api/admin/approve-all', methods=['POST'])
def admin_approve_all():
    pending = db.get_pending_users()
    count = 0
    for u in pending:
        u_name = u.get('username')
        if u_name and u_name != 'admin' and db.approve_user(u_name):
            count += 1
    return jsonify({"success": True, "approved_count": count})


@app.route('/api/admin/delete-user', methods=['POST'])
def admin_delete_user():
    data = request.json or {}
    username = data.get('username', '').strip()
    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400
    if username == 'admin':
        return jsonify({"success": False, "message": "The master administrator account cannot be deleted."}), 403
    
    success, message = db.delete_user(username)
    return jsonify({"success": success, "message": message}), (200 if success else 400)


@app.route('/api/admin/update-user', methods=['POST'])
def admin_update_user():
    data = request.json or {}
    username = data.get('username', '').strip()
    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400
    
    success, message = db.update_user(username, data)
    return jsonify({"success": success, "message": message}), (200 if success else 400)


def get_chatbot_response(user_message):
    """Intent-trained Agri-Bot: answers crops, pesticides, diseases, dosages,
    prevention, organic remedies, soil, plant anatomy and state-wise farming."""
    try:
        return get_agri_bot_response(user_message, PLANT_STATISTICS)
    except Exception as e:
        print("[!] Agri-Bot engine error:", e)
        return ("🌾 I can advise on pesticides & their doses, plant disease symptoms/treatment/prevention, "
                "crop growing guides, organic remedies, soil & state-wise farming. "
                "Try: 'how to grow tomato', 'Mancozeb dosage', 'treat potato late blight', or 'crops in Punjab'.")


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "reply": "Please ask an agricultural question."})
    reply = get_chatbot_response(message)
    return jsonify({"success": True, "reply": reply})


@app.route('/api/pesticide-directory', methods=['GET'])
def get_pesticide_directory():
    """
    Returns the comprehensive agricultural pesticide library with category classification,
    CIB&RC toxicity bands, target diseases, modes of action, dilution water rates, and safety.
    Accessible to all users.
    """
    category_filter = request.args.get('category', '').strip().lower()
    toxicity_filter = request.args.get('toxicity', '').strip().lower()
    query = request.args.get('q', '').strip().lower()

    results = PESTICIDES_CATALOG
    if category_filter:
        results = [p for p in results if category_filter in p['category'].lower()]
    if toxicity_filter:
        results = [p for p in results if toxicity_filter in p['toxicity_band'].lower()]
    if query:
        results = [
            p for p in results
            if query in p['name'].lower()
            or query in p['trade_names'].lower()
            or query in p['target_crops'].lower()
            or query in p['target_diseases'].lower()
            or query in p['active_ingredient'].lower()
            or query in p['sub_type'].lower()
        ]

    return jsonify({
        "success": True,
        "categories": PESTICIDE_CATEGORIES,
        "pesticides": results,
        "total": len(results)
    })


@app.route('/api/generate-report-pdf', methods=['POST'])
def generate_report_pdf():
    """
    Builds and streams a publication-grade, standardized agronomic diagnostic PDF report
    containing executive summary, targeted pesticide prescription, crop water need,
    irrigation amount & schedule, soil type & conditioning, and farmer safety compliance.
    """
    try:
        data = request.json or {}
        if not data or not data.get('pathology'):
            return jsonify({"success": False, "message": "Valid diagnostic data required."}), 400

        pdf_bytes = build_diagnostic_pdf_bytes(data)
        crop_name = (data.get('pathology', {}).get('crop') or data.get('plant_type') or 'Crop').replace(' ', '_')
        dis_name = (data.get('pathology', {}).get('disease_name') or 'Scan').replace(' ', '_')
        filename = f"ASSPA_Diagnostic_Report_{crop_name}_{dis_name}_{int(time.time())}.pdf"

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print("[!] Error generating diagnostic PDF:", e)
        return jsonify({"success": False, "message": f"PDF Generation Error: {str(e)}"}), 500

@app.route('/outputs/<path:filename>')
def serve_output_file(filename):
    """Serves generated academic output charts and figures directly."""
    from flask import send_from_directory
    outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
    return send_from_directory(outputs_dir, filename)


@app.route('/api/academic-outputs', methods=['GET'])
def get_academic_outputs_list():
    """Returns metadata and download URLs for all academic output evaluation figures."""
    outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
    files_info = [
        {
            "id": "model_metrics",
            "title": "Model Comparison Benchmark (4 ML Algorithms + Ensemble)",
            "description": "Accuracy, Precision, Recall, F1-Score and Real-Time Latency across SVM, MLP, KNN, RF, and Consensus Voting.",
            "filename": "output_model_comparison_metrics.png",
            "url": "/outputs/output_model_comparison_metrics.png"
        },
        {
            "id": "pca_variance",
            "title": "PCA Scree Plot & Cumulative Explained Variance",
            "description": "Compressing 4,096-dim color & spatial texture vector down to 128 principal components (32:1 compression ratio, 82.7% variance retained).",
            "filename": "output_pca_variance_analysis.png",
            "url": "/outputs/output_pca_variance_analysis.png"
        },
        {
            "id": "confusion_matrix",
            "title": "Pathology Classification Confusion Matrix Heatmap",
            "description": "True vs Predicted distribution for representative high-impact agricultural crop diseases with normalized concordance rates.",
            "filename": "output_confusion_matrix_top_diseases.png",
            "url": "/outputs/output_confusion_matrix_top_diseases.png"
        },
        {
            "id": "severity_radar",
            "title": "Multi-Sensor Severity Telemetry Radar & Actuation Matrix",
            "description": "Multi-modal fusion of CWSI, canopy temp delta, relative humidity, foliar lesion area, and ML confidence into Mild/Mod/Severe dosage tiers.",
            "filename": "output_multimodal_severity_radar.png",
            "url": "/outputs/output_multimodal_severity_radar.png"
        },
        {
            "id": "master_board",
            "title": "Unified Academic Presentation & Viva Master Board",
            "description": "All-in-one 16:9 widescreen presentation poster integrating all 4 core experimental evaluation outputs.",
            "filename": "output_master_presentation_board.png",
            "url": "/outputs/output_master_presentation_board.png"
        }
    ]
    return jsonify({"success": True, "outputs": files_info})


if __name__ == '__main__':
    print("[*] Starting Agri-Pesticide Flask Server on port 5000...")
    app.run(debug=True, use_reloader=False, port=5000)

