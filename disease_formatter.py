"""
disease_formatter.py
====================
Utility module for standardizing, formatting, and presenting plant pathology
diagnosis labels, crop names, pathogen classifications, and scientific names.

Converts raw directory or class names like:
 - "Tomato Tomato mosaic virus" -> Crop: Tomato, Disease: Tomato Mosaic Virus, Pathogen: Viral
 - "Orange Haunglongbing Citrus greening" -> Crop: Citrus / Orange, Disease: Huanglongbing (Citrus Greening), Pathogen: Bacterial
 - "corn crop" -> Crop: Corn (Maize), Disease: Healthy Foliage / Baseline Specimen
 - "potassium deficiency in plant" -> Crop: Multi-Crop, Disease: Potassium (K) Deficiency, Pathogen: Abiotic
 - "Apple Cedar apple rust" -> Crop: Apple, Disease: Cedar Apple Rust, Pathogen: Fungal
"""

import re

# Comprehensive registry of canonical plant pathology metadata
DISEASE_METADATA_MAP = {
    "apple apple scab": {
        "crop": "Apple",
        "disease": "Apple Scab",
        "scientific_name": "Venturia inaequalis",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Seb Ka Khapra Rog (Apple Scab)"
    },
    "apple black rot": {
        "crop": "Apple",
        "disease": "Black Rot",
        "scientific_name": "Botryosphaeria obtusa",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Apple Frog-Eye Spot & Black Rot"
    },
    "apple cedar apple rust": {
        "crop": "Apple",
        "disease": "Cedar Apple Rust",
        "scientific_name": "Gymnosporangium juniperi-virginianae",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Cedar Rust"
    },
    "apple healthy": {
        "crop": "Apple",
        "disease": "Healthy Specimen",
        "scientific_name": "Malus domestica",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Vigorous Healthy Apple Foliage"
    },
    "bacterial leaf blight in rice leaf": {
        "crop": "Rice (Paddy)",
        "disease": "Bacterial Leaf Blight (BLB)",
        "scientific_name": "Xanthomonas oryzae pv. oryzae",
        "pathogen_type": "Bacterial",
        "badge_class": "badge-bacterial",
        "common_name": "Dhan Ka Jivanu Patta Jhulsa Rog"
    },
    "blight in corn leaf": {
        "crop": "Corn (Maize)",
        "disease": "Northern Corn Leaf Blight",
        "scientific_name": "Exserohilum turcicum",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Turcicum Leaf Blight"
    },
    "blueberry healthy": {
        "crop": "Blueberry",
        "disease": "Healthy Specimen",
        "scientific_name": "Cyanococcus",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Blueberry"
    },
    "brown spot in rice leaf": {
        "crop": "Rice (Paddy)",
        "disease": "Brown Spot Disease",
        "scientific_name": "Bipolaris oryzae / Cochliobolus miyabeanus",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Dhan Ka Bhura Dhabba Rog"
    },
    "cercospora leaf spot": {
        "crop": "Multi-Crop",
        "disease": "Cercospora Leaf Spot",
        "scientific_name": "Cercospora spp.",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tikko Rog / Cercospora Spot"
    },
    "cherry (including sour) powdery mildew": {
        "crop": "Cherry",
        "disease": "Powdery Mildew",
        "scientific_name": "Podosphaera clandestina",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "White Powdery Mildew"
    },
    "cherry (including_sour) healthy": {
        "crop": "Cherry",
        "disease": "Healthy Specimen",
        "scientific_name": "Prunus cerasus",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Cherry Foliage"
    },
    "common rust in corn leaf": {
        "crop": "Corn (Maize)",
        "disease": "Common Leaf Rust",
        "scientific_name": "Puccinia sorghi",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Makka Ka Gerui Rog"
    },
    "corn (maize) healthy": {
        "crop": "Corn (Maize)",
        "disease": "Healthy Specimen",
        "scientific_name": "Zea mays",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Maize Crop"
    },
    "corn crop": {
        "crop": "Corn (Maize)",
        "disease": "Healthy Maize Specimen",
        "scientific_name": "Zea mays",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Corn Foliage"
    },
    "garlic": {
        "crop": "Garlic",
        "disease": "Healthy Garlic Specimen",
        "scientific_name": "Allium sativum",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Lahsun Crop Specimen"
    },
    "grape black rot": {
        "crop": "Grape",
        "disease": "Black Rot",
        "scientific_name": "Guignardia bidwellii",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Angoor Ka Kala Sadhan Rog"
    },
    "grape esca black measles": {
        "crop": "Grape",
        "disease": "Esca (Black Measles)",
        "scientific_name": "Phaeomoniella chlamydospora",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Grapevine Trunk Disease (Esca)"
    },
    "grape leaf blight isariopsis leaf spot": {
        "crop": "Grape",
        "disease": "Isariopsis Leaf Spot / Blight",
        "scientific_name": "Pseudocercospora cladosporioides",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Grape Foliar Blight"
    },
    "grape healthy": {
        "crop": "Grape",
        "disease": "Healthy Specimen",
        "scientific_name": "Vitis vinifera",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Grapevine Leaf"
    },
    "gray leaf spot in corn leaf": {
        "crop": "Corn (Maize)",
        "disease": "Gray Leaf Spot (GLS)",
        "scientific_name": "Cercospora zeae-maydis",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Corn Gray Spot"
    },
    "leaf smut in rice leaf": {
        "crop": "Rice (Paddy)",
        "disease": "Leaf Smut",
        "scientific_name": "Entyloma oryzae",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Dhan Ka Kandva Rog"
    },
    "orange haunglongbing citrus greening": {
        "crop": "Orange (Citrus)",
        "disease": "Huanglongbing (Citrus Greening)",
        "scientific_name": "Candidatus Liberibacter asiaticus",
        "pathogen_type": "Bacterial",
        "badge_class": "badge-bacterial",
        "common_name": "Citrus Greening / Yellow Shoot Disease"
    },
    "peach healthy": {
        "crop": "Peach",
        "disease": "Healthy Specimen",
        "scientific_name": "Prunus persica",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Peach Leaf"
    },
    "pepper bell bacterial spot": {
        "crop": "Bell Pepper (Capsicum)",
        "disease": "Bacterial Spot",
        "scientific_name": "Xanthomonas campestris pv. vesicatoria",
        "pathogen_type": "Bacterial",
        "badge_class": "badge-bacterial",
        "common_name": "Shimla Mirch Jivanu Spot"
    },
    "pepper bell healthy": {
        "crop": "Bell Pepper (Capsicum)",
        "disease": "Healthy Specimen",
        "scientific_name": "Capsicum annuum",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Capsicum Foliage"
    },
    "potato early blight": {
        "crop": "Potato",
        "disease": "Early Blight (Target Spot)",
        "scientific_name": "Alternaria solani",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Aloo Ka Ageti Jhulsa Rog"
    },
    "potato late blight": {
        "crop": "Potato",
        "disease": "Late Blight",
        "scientific_name": "Phytophthora infestans",
        "pathogen_type": "Fungal / Oomycete",
        "badge_class": "badge-fungal",
        "common_name": "Aloo Ka Pachheti Jhulsa Rog"
    },
    "potato healthy": {
        "crop": "Potato",
        "disease": "Healthy Specimen",
        "scientific_name": "Solanum tuberosum",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Potato Crop"
    },
    "potato crop": {
        "crop": "Potato",
        "disease": "Healthy Specimen",
        "scientific_name": "Solanum tuberosum",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Potato Plant"
    },
    "potato hollow heart": {
        "crop": "Potato",
        "disease": "Hollow Heart (Physiological Disorder)",
        "scientific_name": "Physiological abiotic stress",
        "pathogen_type": "Abiotic",
        "badge_class": "badge-abiotic",
        "common_name": "Tuber Cavitation / Hollow Heart"
    },
    "raspberry healthy": {
        "crop": "Raspberry",
        "disease": "Healthy Specimen",
        "scientific_name": "Rubus idaeus",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Raspberry"
    },
    "sogatella rice": {
        "crop": "Rice (Paddy)",
        "disease": "White-Backed Planthopper (WBPH)",
        "scientific_name": "Sogatella furcifera",
        "pathogen_type": "Pest / Insect",
        "badge_class": "badge-pest",
        "common_name": "Safed Peeth Wala Fudka (WBPH)"
    },
    "soybean healthy": {
        "crop": "Soybean",
        "disease": "Healthy Specimen",
        "scientific_name": "Glycine max",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Soybean Crop"
    },
    "strawberry leaf scorch": {
        "crop": "Strawberry",
        "disease": "Leaf Scorch",
        "scientific_name": "Diplocarpon earlianum",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Strawberry Scorch Spot"
    },
    "strawberry healthy": {
        "crop": "Strawberry",
        "disease": "Healthy Specimen",
        "scientific_name": "Fragaria × ananassa",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Strawberry"
    },
    "tomato bacterial spot": {
        "crop": "Tomato",
        "disease": "Bacterial Spot",
        "scientific_name": "Xanthomonas vesicatoria",
        "pathogen_type": "Bacterial",
        "badge_class": "badge-bacterial",
        "common_name": "Tamatar Ka Jivanu Dhabba Rog"
    },
    "tomato early blight": {
        "crop": "Tomato",
        "disease": "Early Blight (Target Spot)",
        "scientific_name": "Alternaria solani",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tamatar Ka Ageti Jhulsa Rog"
    },
    "tomato late blight": {
        "crop": "Tomato",
        "disease": "Late Blight",
        "scientific_name": "Phytophthora infestans",
        "pathogen_type": "Fungal / Oomycete",
        "badge_class": "badge-fungal",
        "common_name": "Tamatar Ka Pachheti Jhulsa Rog"
    },
    "tomato leaf mold": {
        "crop": "Tomato",
        "disease": "Leaf Mold",
        "scientific_name": "Passalora fulva / Cladosporium fulvum",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tamatar Ki Fafundi (Leaf Mold)"
    },
    "tomato septoria leaf spot": {
        "crop": "Tomato",
        "disease": "Septoria Leaf Spot",
        "scientific_name": "Septoria lycopersici",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Septoria Spot"
    },
    "tomato spider mites two spotted spider mite": {
        "crop": "Tomato",
        "disease": "Two-Spotted Spider Mite",
        "scientific_name": "Tetranychus urticae",
        "pathogen_type": "Pest / Mite",
        "badge_class": "badge-pest",
        "common_name": "Lal Makdi / Spider Mite Infestation"
    },
    "tomato target spot": {
        "crop": "Tomato",
        "disease": "Target Spot",
        "scientific_name": "Corynespora cassiicola",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Corynespora Target Spot"
    },
    "tomato tomato mosaic virus": {
        "crop": "Tomato",
        "disease": "Tomato Mosaic Virus (ToMV)",
        "scientific_name": "Tobamovirus",
        "pathogen_type": "Viral",
        "badge_class": "badge-viral",
        "common_name": "Tamatar Ka Mosaic Virus"
    },
    "tomato healthy": {
        "crop": "Tomato",
        "disease": "Healthy Specimen",
        "scientific_name": "Solanum lycopersicum",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Vigorous Healthy Tomato Plant"
    },
    "tomato canker": {
        "crop": "Tomato",
        "disease": "Bacterial Canker",
        "scientific_name": "Clavibacter michiganensis",
        "pathogen_type": "Bacterial",
        "badge_class": "badge-bacterial",
        "common_name": "Bacterial Canker & Systemic Wilt"
    },
    "lemon canker": {
        "crop": "Lemon / Citrus",
        "disease": "Citrus Canker",
        "scientific_name": "Xanthomonas axonopodis pv. citri",
        "pathogen_type": "Bacterial",
        "badge_class": "badge-bacterial",
        "common_name": "Nimbu Ka Canker Rog"
    },
    "algal leaf in tea": {
        "crop": "Tea (Chai)",
        "disease": "Red Rust (Algal Leaf Spot)",
        "scientific_name": "Cephaleuros virescens",
        "pathogen_type": "Algal / Epiphytic",
        "badge_class": "badge-algal",
        "common_name": "Chai Ki Lal Gerui (Red Rust)"
    },
    "anthracnose in tea": {
        "crop": "Tea (Chai)",
        "disease": "Anthracnose / Brown Dieback",
        "scientific_name": "Colletotrichum camelliae",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tea Anthracnose Spot"
    },
    "bird eye spot in tea": {
        "crop": "Tea (Chai)",
        "disease": "Bird's Eye Spot",
        "scientific_name": "Cercospora theae",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tea Bird's Eye Spot"
    },
    "brown blight in tea": {
        "crop": "Tea (Chai)",
        "disease": "Brown Blight",
        "scientific_name": "Glomerella cingulata",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tea Brown Blight"
    },
    "cabbage looper": {
        "crop": "Cabbage / Cole Crops",
        "disease": "Cabbage Looper Caterpillar",
        "scientific_name": "Trichoplusia ni",
        "pathogen_type": "Pest / Insect",
        "badge_class": "badge-pest",
        "common_name": "Patta Gobi Ki Sundi (Looper)"
    },
    "ginger": {
        "crop": "Ginger",
        "disease": "Healthy Ginger Specimen",
        "scientific_name": "Zingiber officinale",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Adrak Specimen"
    },
    "healthy tea leaf": {
        "crop": "Tea (Chai)",
        "disease": "Healthy Specimen",
        "scientific_name": "Camellia sinensis",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Healthy Green Tea Leaf"
    },
    "onion": {
        "crop": "Onion",
        "disease": "Healthy Onion Specimen",
        "scientific_name": "Allium cepa",
        "pathogen_type": "Healthy",
        "badge_class": "badge-healthy",
        "common_name": "Pyaaz Crop Specimen"
    },
    "potassium deficiency in plant": {
        "crop": "Multi-Crop / Nutrient",
        "disease": "Potassium (K) Potash Deficiency",
        "scientific_name": "Nutritional K+ Ion Stress",
        "pathogen_type": "Abiotic Deficiency",
        "badge_class": "badge-abiotic",
        "common_name": "Potash Ki Kami (Marginal Leaf Scorch)"
    },
    "red leaf spot in tea": {
        "crop": "Tea (Chai)",
        "disease": "Red Leaf Spot",
        "scientific_name": "Phoma theicola",
        "pathogen_type": "Fungal",
        "badge_class": "badge-fungal",
        "common_name": "Tea Red Spot"
    }
}


def clean_raw_class_name(raw_name: str) -> str:
    """Normalize raw class strings by stripping underscores and extra spaces."""
    if not raw_name:
        return "healthy"
    s = raw_name.lower().replace("___", " ").replace("__", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def format_disease_prediction(raw_name: str, confidence: float = 0.0) -> dict:
    """
    Parses and produces clear, human-readable, and scientific pathology metadata.
    
    Returns:
      {
         "crop": "Tomato",
         "disease_name": "Early Blight (Target Spot)",
         "full_display": "Tomato — Early Blight (Target Spot)",
         "scientific_name": "Alternaria solani",
         "pathogen_type": "Fungal",
         "badge_class": "badge-fungal",
         "common_regional_name": "Tamatar Ka Ageti Jhulsa Rog",
         "is_healthy": False,
         "confidence": 98.4
      }
    """
    cleaned = clean_raw_class_name(raw_name)
    
    # 1. Exact match in metadata map
    if cleaned in DISEASE_METADATA_MAP:
        meta = DISEASE_METADATA_MAP[cleaned]
        is_h = meta["pathogen_type"] == "Healthy"
        return {
            "raw_name": raw_name,
            "crop": meta["crop"],
            "disease_name": meta["disease"],
            "full_display": f"{meta['crop']} - {meta['disease']}" if not is_h else f"{meta['crop']} (Healthy)",
            "scientific_name": meta["scientific_name"],
            "pathogen_type": meta["pathogen_type"],
            "badge_class": meta["badge_class"],
            "common_regional_name": meta.get("common_name", ""),
            "is_healthy": is_h,
            "confidence": round(confidence, 1)
        }
    
    # 2. Heuristic parsing for unmapped classes
    is_healthy = "healthy" in cleaned
    
    # Extract crop candidate
    known_crops = [
        "tomato", "potato", "apple", "rice", "corn", "maize", "grape", "cherry",
        "citrus", "orange", "lemon", "peach", "pepper", "strawberry", "tea",
        "soybean", "cotton", "wheat", "sugarcane", "onion", "garlic", "ginger",
        "cabbage", "blueberry", "raspberry"
    ]
    detected_crop = "Foliar Specimen"
    for c in known_crops:
        if c in cleaned:
            detected_crop = c.title()
            break
            
    # Determine Pathogen Category
    if is_healthy:
        path_type = "Healthy"
        badge_cls = "badge-healthy"
    elif "bacteri" in cleaned or "canker" in cleaned:
        path_type = "Bacterial"
        badge_cls = "badge-bacterial"
    elif "virus" in cleaned or "mosaic" in cleaned:
        path_type = "Viral"
        badge_cls = "badge-viral"
    elif "deficiency" in cleaned:
        path_type = "Abiotic Deficiency"
        badge_cls = "badge-abiotic"
    elif "mite" in cleaned or "looper" in cleaned or "sogatella" in cleaned:
        path_type = "Pest / Insect"
        badge_cls = "badge-pest"
    else:
        path_type = "Fungal"
        badge_cls = "badge-fungal"

    # Beautify disease name: remove duplicate crop names
    words = cleaned.split()
    cleaned_words = []
    crop_word_seen = False
    for w in words:
        if w.lower() == detected_crop.lower() and not crop_word_seen:
            crop_word_seen = True
            continue
        cleaned_words.append(w.capitalize())
        
    disease_title = " ".join(cleaned_words)
    if not disease_title or is_healthy:
        disease_title = "Healthy Foliage"

    return {
        "raw_name": raw_name,
        "crop": detected_crop,
        "disease_name": disease_title,
        "full_display": f"{detected_crop} - {disease_title}",
        "scientific_name": "Pathological Specimen",
        "pathogen_type": path_type,
        "badge_class": badge_cls,
        "common_regional_name": "",
        "is_healthy": is_healthy,
        "confidence": round(confidence, 1)
    }
