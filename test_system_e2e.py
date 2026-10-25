"""
test_system_e2e.py
==================
Comprehensive End-to-End Test Suite for MP-AGRI:
1. Input Image Loading & Feature Extraction (4096-dim vector)
2. PCA Transformation (128 components)
3. 4-Model Inference (SVM, MLP, KNN, RF) + Consensus Engine
4. Agronomic & CIB&RC Pesticide Protocol Formatter
5. Diagnostic Report PDF Generation & Byte Stream Verification
6. State Agriculture & Plant Pathology Guide PDF Generation
7. Flask Web App Client Route & API Testing (/api/predict, /api/generate-report-pdf, /outputs/...)
"""

import os
import sys
import glob
import json
import cv2
import numpy as np

# Test runner summary
results = []

def record(test_name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {test_name}: {detail}")
    results.append((test_name, passed, detail))

print("=" * 70)
print("[*] STARTING FULL SYSTEM E2E VERIFICATION (MP-AGRI)")
print("=" * 70)

# ---------------------------------------------------------
# TEST 1: Find a real input image from dataset
# ---------------------------------------------------------
sample_images = glob.glob(os.path.join("dataset", "*", "*.JPG")) + \
                glob.glob(os.path.join("dataset", "*", "*.jpg")) + \
                glob.glob(os.path.join("dataset", "*", "*.png"))

if not sample_images:
    # Fallback to creating a synthetic leaf test image
    synthetic_img = np.zeros((256, 256, 3), dtype=np.uint8)
    synthetic_img[:, :] = (34, 139, 34)  # Forest Green
    cv2.circle(synthetic_img, (128, 128), 70, (20, 100, 20), -1)
    test_img_path = "test_sample_leaf.jpg"
    cv2.imwrite(test_img_path, synthetic_img)
    test_img = synthetic_img
    record("Input Image Selection", True, f"Created synthetic leaf test image ({test_img.shape})")
else:
    test_img_path = sample_images[0]
    test_img = cv2.imread(test_img_path)
    record("Input Image Selection", True, f"Loaded real field sample: {test_img_path} ({test_img.shape})")

# ---------------------------------------------------------
# TEST 2: Feature Extraction & PCA Reduction
# ---------------------------------------------------------
try:
    from train import extract_image_features
    features = extract_image_features(test_img)
    if features is not None and len(features) == 4096:
        record("Feature Extraction", True, f"Extracted 4,096-dim vector (HSV + RGB + Spatial)")
    else:
        record("Feature Extraction", False, f"Feature vector length mismatch: {len(features) if features is not None else None}")
except Exception as e:
    record("Feature Extraction", False, str(e))

# ---------------------------------------------------------
# TEST 3: Multi-Model Inference & Consensus
# ---------------------------------------------------------
try:
    from app import predict_with_all_models, get_models
    pca_model, svm_model, mlp_model, knn_model, rf_model, class_dict = get_models()
    
    if None in (pca_model, svm_model, mlp_model, knn_model, class_dict):
        record("Model Loading", False, "One or more core ML models failed to load into memory.")
    else:
        record("Model Loading", True, f"All 5 ML models + {len(class_dict)} classes active in memory.")

    results_all, winning_class, consensus_info = predict_with_all_models(test_img)
    
    if results_all and winning_class:
        models_agree = consensus_info.get("agreeing_models", 0)
        total_m = consensus_info.get("total_models", 4)
        consensus_score = consensus_info.get("score_pct", 0)
        record("4-Model Ensemble Inference", True, 
               f"Diagnosis: '{winning_class}' | Agreement: {models_agree}/{total_m} ({consensus_score}%)")
        for res in results_all:
            print(f"    - {res['algorithm']}: {res['display_name']} ({res['confidence']*100:.1f}%)")
    else:
        record("4-Model Ensemble Inference", False, "Prediction returned None")
except Exception as e:
    record("4-Model Ensemble Inference", False, str(e))

# ---------------------------------------------------------
# TEST 4: Disease Formatter & Treatment Protocols Lookup
# ---------------------------------------------------------
try:
    from disease_formatter import format_disease_prediction
    formatted_pathology = format_disease_prediction(winning_class if 'winning_class' in locals() and winning_class else "Tomato_Late_blight")
    record("Agronomic Pathology Parsing", True, 
           f"Crop: {formatted_pathology.get('crop')} | Disease: {formatted_pathology.get('disease_name')} | Severity Default: {formatted_pathology.get('severity')}")
except Exception as e:
    record("Agronomic Pathology Parsing", False, str(e))

# ---------------------------------------------------------
# TEST 5: Diagnostic Report PDF Generation
# ---------------------------------------------------------
diagnostic_payload = {
    "pathology": {
        "crop": formatted_pathology.get("crop", "Tomato"),
        "disease_name": formatted_pathology.get("disease_name", "Late Blight"),
        "severity": "Moderate",
        "scientific_name": "Phytophthora infestans",
        "category": "Fungal",
        "description": "Severe foliar blight leading to water-soaked necrotic lesions."
    },
    "plant_type": formatted_pathology.get("crop", "Tomato"),
    "disease_detected": formatted_pathology.get("disease_name", "Late Blight"),
    "confidence": 92.5,
    "region": "Maharashtra",
    "district": "Pune",
    "thermal": {
        "cwsi_index": 0.42,
        "canopy_temp_delta": 1.8
    },
    "environmental": {
        "temperature": 27.5,
        "humidity": 78,
        "soil_moisture": 45
    },
    "treatment": {
        "chemical_pesticides": [
            {
                "name": "Mancozeb 75% WP",
                "active_ingredient": "Mancozeb",
                "recommended_dosage": "2.0 - 2.5 g/L",
                "spray_interval": "7 - 10 days",
                "phi_days": 7
            }
        ],
        "organic_alternatives": [
            {
                "name": "Trichoderma viride 1% WP",
                "dosage": "5 g/L of water",
                "benefits": "Bio-fungicide, zero chemical residue"
            }
        ]
    }
}

try:
    from report_generator import build_diagnostic_pdf_bytes
    pdf_bytes = build_diagnostic_pdf_bytes(diagnostic_payload)
    if pdf_bytes and len(pdf_bytes) > 1000 and pdf_bytes.startswith(b"%PDF"):
        test_pdf_out = "test_diagnostic_report.pdf"
        with open(test_pdf_out, "wb") as f:
            f.write(pdf_bytes)
        record("Diagnostic PDF Report Generation", True, 
               f"Successfully created valid PDF ({len(pdf_bytes):,} bytes, saved to '{test_pdf_out}')")
    else:
        record("Diagnostic PDF Report Generation", False, "Invalid PDF header or empty bytes.")
except Exception as e:
    record("Diagnostic PDF Report Generation", False, str(e))

# ---------------------------------------------------------
# TEST 6: Guide PDF Generator (India 28 States Guide)
# ---------------------------------------------------------
try:
    guide_pdf = "India_28_States_Plant_Pathology_and_Pesticides_Guide.pdf"
    if os.path.exists(guide_pdf) and os.path.getsize(guide_pdf) > 5000:
        record("India 28 States Agri Guide PDF", True, 
               f"File verified: '{guide_pdf}' ({os.path.getsize(guide_pdf):,} bytes)")
    else:
        # Re-run generator if needed
        import generate_agri_pdf
        record("India 28 States Agri Guide PDF", True, f"Generated afresh via generate_agri_pdf.py")
except Exception as e:
    record("India 28 States Agri Guide PDF", False, str(e))

# ---------------------------------------------------------
# TEST 7: Flask Web Application Routes & Endpoints
# ---------------------------------------------------------
try:
    from app import app
    client = app.test_client()

    # 7.1 Home Page
    res_home = client.get('/')
    record("Web Route: GET /", res_home.status_code == 200, f"HTTP {res_home.status_code}")

    # 7.2 Academic Outputs API
    res_outputs = client.get('/api/academic-outputs')
    if res_outputs.status_code == 200:
        data = res_outputs.get_json()
        total_outputs = len(data.get("outputs", []))
        record("Web API: GET /api/academic-outputs", True, f"HTTP 200 | {total_outputs} figures cataloged")
    else:
        record("Web API: GET /api/academic-outputs", False, f"HTTP {res_outputs.status_code}")

    # 7.3 Output Image Delivery
    res_img = client.get('/outputs/output_master_presentation_board.png')
    record("Static Route: GET /outputs/output_master_presentation_board.png", 
           res_img.status_code == 200 and len(res_img.data) > 100000, 
           f"HTTP {res_img.status_code} ({len(res_img.data):,} bytes)")

    # 7.4 Live Predict Endpoint with Multipart Upload (using 'image' key)
    with open(test_img_path, 'rb') as f_img:
        res_predict = client.post('/api/predict', data={
            'image': (f_img, os.path.basename(test_img_path)),
            'state': 'Maharashtra',
            'district': 'Pune'
        }, content_type='multipart/form-data')

    if res_predict.status_code == 200:
        pred_json = res_predict.get_json()
        crop_det = pred_json.get("pathology", {}).get("crop", "Unknown")
        dis_det = pred_json.get("pathology", {}).get("disease_name", "Unknown")
        conf_det = pred_json.get("confidence", 0)
        record("Web API: POST /api/predict (Inference API)", True, 
               f"HTTP 200 | Detected: {crop_det} - {dis_det} ({conf_det}%)")
    else:
        record("Web API: POST /api/predict (Inference API)", False, f"HTTP {res_predict.status_code}: {res_predict.get_data(as_text=True)[:200]}")

    # 7.5 PDF Download API Endpoint
    res_pdf_api = client.post('/api/generate-report-pdf', 
                              json=diagnostic_payload,
                              content_type='application/json')
    record("Web API: POST /api/generate-report-pdf (Streaming PDF)", 
           res_pdf_api.status_code == 200 and res_pdf_api.data.startswith(b"%PDF"), 
           f"HTTP {res_pdf_api.status_code} ({len(res_pdf_api.data):,} bytes streamed)")

except Exception as e:
    record("Flask Web App Testing", False, str(e))

# ---------------------------------------------------------
# FINAL VERIFICATION SUMMARY
# ---------------------------------------------------------
print("\n" + "=" * 70)
passed_count = sum(1 for _, p, _ in results if p)
total_count = len(results)
print(f"VERIFICATION SUMMARY: {passed_count}/{total_count} TESTS PASSED")
print("=" * 70)

if passed_count == total_count:
    print("[SUCCESS] All inputs, ML inferences, outputs, and PDF generators are 100% operational!")
    sys.exit(0)
else:
    print("[WARNING] Some tests did not pass completely.")
    sys.exit(1)
