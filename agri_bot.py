"""
agri_bot.py
===========
Intelligent, intent-trained Agri-Bot conversational engine.

Answers the full spectrum of agriculture questions - pesticides, crops, plants,
diseases, dosages, prevention, organic/bio-alternatives, banned chemicals,
state/regional agriculture, soil, irrigation, nutrition, plant anatomy, and
basic agri-glossary definitions - by routing every query through a weighted
intent classifier and pulling answers from the existing knowledge bases:

  * india_agri_db.INDIA_AGRI_DB  (states, crops, pesticides, banned, safety, search)
  * india_agri_db seed lists      (STATES_DATA, CROPS_DATA, PESTICIDES_LIBRARY, ...)
  * data/cure.json                (disease treatment texts)
  * data/disease_names.json       (crop + category + symptom description)
  * disease_formatter             (pathology metadata)
  * treatment_protocols           (curated protocols, prevention, symptoms, safety)

Design: rule-based NLU with synonym expansion + fuzzy entity matching, so that
even loosely-worded "basic" questions are understood.
"""

import os
import re
import json
from difflib import SequenceMatcher

from india_agri_db import (
    INDIA_AGRI_DB, STATES_DATA, CROPS_DATA,
    PESTICIDES_LIBRARY, BANNED_PESTICIDES_DATA, PLANT_STRUCTURES_DATA,
)
from disease_formatter import format_disease_prediction

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── LOAD STATIC DISEASE KNOWLEDGE ──────────────────────────────────────────────
def _load_json(rel, default):
    try:
        with open(os.path.join(BASE_DIR, rel), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

CURE_DB = _load_json(os.path.join("data", "cure.json"), {})
DISEASE_LIST = _load_json(os.path.join("data", "disease_names.json"), [])

DISEASE_BY_KEY = {}
for d in DISEASE_LIST:
    nm = (d.get("name") or "").strip()
    if nm:
        DISEASE_BY_KEY[nm.lower()] = d
for k, v in CURE_DB.items():
    DISEASE_BY_KEY.setdefault(k.lower(), {"name": k, "crop": "", "category": "Fungal", "desc": v})

CROP_ALIASES = {
    "paddy": "rice", "rice": "rice", "dhan": "rice", "dhana": "rice",
    "wheat": "wheat", "gehun": "wheat",
    "maize": "corn (maize)", "corn": "corn (maize)",
    "tomato": "tomato", "tamatar": "tomato",
    "potato": "potato", "aloo": "potato", "alu": "potato",
    "brinjal": "brinjal", "eggplant": "brinjal", "baingan": "brinjal",
    "cotton": "cotton", "kapas": "cotton",
    "sugarcane": "sugarcane", "ganna": "sugarcane",
    "chilli": "chilli", "chili": "chilli", "mirchi": "chilli", "pepper": "chilli",
    "onion": "onion", "pyaaz": "onion", "pyaz": "onion",
    "garlic": "garlic", "lahsun": "garlic",
    "ginger": "ginger", "adrak": "ginger",
    "turmeric": "turmeric", "haldi": "turmeric",
    "tea": "tea", "chai": "tea",
    "coffee": "coffee",
    "banana": "banana", "kela": "banana",
    "mango": "mango", "aam": "mango",
    "apple": "apple", "seb": "apple",
    "orange": "orange", "grape": "grape", "angoor": "grape",
    "soybean": "soybean", "soya": "soybean",
    "mustard": "mustard", "sarson": "mustard", "rai": "mustard",
    "groundnut": "groundnut", "peanut": "groundnut", "moongfali": "groundnut",
    "sunflower": "sunflower", "suraj mukhi": "sunflower",
    "jute": "jute", "cardamom": "cardamom", "elaichi": "cardamom",
    "coconut": "coconut", "nariyal": "coconut",
    "rubber": "rubber", "cashew": "cashew", "pineapple": "pineapple",
    "strawberry": "strawberry", "blueberry": "blueberry", "raspberry": "raspberry",
    "peach": "peach", "cherry": "cherry", "grapes": "grape", "lemon": "lemon",
    "cabbage": "cabbage", "cauliflower": "cauliflower", "squash": "squash",
    "chickpea": "chickpea", "gram": "chickpea", "pigeon pea": "pigeon pea",
    "tur": "pigeon pea", "arhar": "pigeon pea", "red gram": "pigeon pea",
    "green gram": "green gram", "moong": "green gram", "black gram": "black gram",
    "urad": "black gram", "lentil": "lentil", "dal": "lentil",
}


# ── TEXT UTILITIES ─────────────────────────────────────────────────────────────
def norm(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _best_fuzzy(query_tokens, candidates, min_score=0.72):
    """Return the best fuzzy-matching candidate key for a short query."""
    q = " ".join(query_tokens)
    best, best_score = None, 0.0
    for name, val in candidates.items():
        score = _ratio(q, name)
        if name in q or q in name:
            score = max(score, 0.9)
        if score > best_score:
            best, best_score = name, score
    return (val if best else None), best_score, best


# ── ENTITY EXTRACTION ──────────────────────────────────────────────────────────
def find_state(msg: str):
    for s in STATES_DATA:
        nm = s["state"].lower()
        if nm in msg:
            return s["state"]
    return None


def find_crop(msg: str):
    for alias, canon in CROP_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", msg):
            return canon
    for c in CROPS_DATA:
        if c["name"].lower().split(" (")[0] in msg:
            return c["name"]
    return None


def find_disease(msg: str):
    best, best_score = None, 0.0
    for key, info in DISEASE_BY_KEY.items():
        # strip crop prefix words for a tighter match
        core = key
        if core in msg:
            score = 0.95 + len(core) / 1000.0
        else:
            score = _ratio(msg, core)
        if score > best_score and score >= 0.62:
            best, best_score = info, score
    return best if best_score >= 0.62 else None


CHEM_TOKENS = set()
for p in PESTICIDES_LIBRARY:
    CHEM_TOKENS.add(p["name"].lower())
    CHEM_TOKENS.add(p["name"].lower().split(" ")[0])
for b in BANNED_PESTICIDES_DATA:
    CHEM_TOKENS.add(b["name"].lower())
COMMON_ACTIVES = [
    "neem", "nimba", "mancozeb", "copper oxychloride", "carbendazim", "imidacloprid",
    "chlorpyrifos", "endosulfan", "phorate", "malathion", "dimethoate", "tricyclazole",
    "azoxystrobin", "difenoconazole", "tebuconazole", "propiconazole", "myclobutanil",
    "captan", "ziram", "streptocycline", "bordeaux", "spinetoram", "fipronil",
    "thiamethoxam", "acetamiprid", "chlorantraniliprole", "emamectin", "btk",
    "bacillus", "trichoderma", "pseudomonas", "beauveria", "carbosulfan",
    "monocrotophos", "dichlorvos", "methyl parathion", "carbofuran", "alachlor",
    "sulphur", "sulfur", "urea", "dap", "mop", "potash", "npk", "vermicompost",
    "neem oil", "nske", "panchagavya", "jeevamrutham", "ammonium sulphate",
]
for a in COMMON_ACTIVES:
    CHEM_TOKENS.add(a)


def find_chemical(msg: str):
    for tok in sorted(CHEM_TOKENS, key=len, reverse=True):
        if tok and tok in msg:
            # resolve to a full library name if possible
            for p in PESTICIDES_LIBRARY:
                if tok in p["name"].lower():
                    return p["name"]
            for b in BANNED_PESTICIDES_DATA:
                if tok in b["name"].lower():
                    return b["name"]
            return tok
    return None


def get_pesticide_record(name: str):
    low = (name or "").lower()
    for p in PESTICIDES_LIBRARY:
        if low in p["name"].lower() or p["name"].lower() in low:
            return p
    # fuzzy
    best, score = None, 0.0
    for p in PESTICIDES_LIBRARY:
        r = _ratio(low, p["name"].lower())
        if r > score:
            best, score = p, r
    return best if score >= 0.6 else None


# ── TOPIC / INTENT DETECTION ───────────────────────────────────────────────────
TOPIC_RULES = [
    ("greeting", ["hi", "hello", "hey", "namaste", "good morning", "good evening", "good afternoon", "yo"]),
    ("thanks", ["thank", "thanks", "thnx", "thankyou", "shukriya", "dhanyawad"]),
    ("bye", ["bye", "goodbye", "see you", "tata", "alvida"]),
    ("identity", ["who are you", "your name", "what are you", "about you", "which ai", "introduce yourself"]),
    ("capabilities", ["what can you do", "help", "how can you help", "features", "command", "options", "what do you know"]),
    ("dosage", ["dose", "dosage", "how much", "quantity", "dilute", "mix", "per liter", "per litre", "ml per", "g per", "spray rate", "concentration", "tank mix"]),
    ("banned", ["banned", "ban", "prohibited", "illegal", "restricted", "banned in india", "not allowed", "hazard", "toxic"]),
    ("organic", ["organic", "bio pesticide", "biopesticide", "bio-agent", "botanical", "neem", "natural", "chemical free", "pesticide free", "vermicompost", "trichoderma", "biological"]),
    ("types_pesticide", ["type of pesticide", "types of pesticide", "what is pesticide", "define pesticide", "classification of pesticide", "kind of pesticide", "kinds of pesticide", "what are pesticides", "pesticide mean"]),
    ("fungicide", ["fungicide", "anti fungal", "antifungal", "fungal medicine", "rust", "smut"]),
    ("insecticide", ["insecticide", "for insect", "kill insect", "bug control", "borer", "worm", "caterpillar", "beetle"]),
    ("herbicide", ["herbicide", "weedicide", "kill weed", "weed control", "weed management", "weeds", "doob", "grass in field"]),
    ("symptoms", ["symptom", "symptoms", "identify", "how to know", "signs", "recognition", "appear like", "look like"]),
    ("treatment", ["treat", "treatment", "cure", "medicine", "medication", "control", "manage", "remedy", "what to do", "solution", "how to save", "get rid"]),
    ("prevention", ["prevent", "prevention", "avoid", "protection", "secure", "safeguard", "stop disease", "before infection", "prophylactic"]),
    ("disease_info", ["disease", "infection", "pathogen", "rot", "wilt", "blight", "mildew", "scab", "canker", "mosaic", "curl"]),
    ("grow", ["grow", "growing", "cultivate", "cultivation", "plant", "sow", "sowing", "raise", "husbandry", "farm", "farming", "how to cultivate"]),
    ("irrigation", ["irrigation", "water", "watering", "how often water", "moisture", "sprinkler", "drip"]),
    ("nutrition", ["fertilizer", "fertiliser", "nutrient", "npk", "deficiency", "nutrition", "compost", "manure", "urea", "dap", "potash", "zinc", "iron", "calcium"]),
    ("harvest", ["harvest", "harvesting", "maturity", "when to pick", "yield", "produce per acre"]),
    ("soil", ["soil", "ph level", "loam", "clay soil", "sandy", "soil type", "soil health"]),
    ("seed", ["seed", "seeds", "seed treatment", "seedling", "nursery", "transplant"]),
    ("climate", ["climate", "weather", "rain", "rainfall", "humidity", "temperature", "season", "rabi", "kharif", "zaid"]),
    ("plant_anatomy", ["root", "stem", "leaf", "leaves", "photosynthesis", "plant part", "anatomy", "xylem", "phloem", "chlorophyll"]),
    ("crop_diseases", ["diseases of", "common disease", "which disease", "pests and disease"]),
    ("region", ["crop in", "crops in", "grow in", "agriculture in", "farming in", "pesticide in", "state", "district"]),
    ("crop_info", ["about crop", "tell me about", "what is crop", "crop info"]),
]


def detect_topics(msg: str):
    scores = {}
    for topic, kws in TOPIC_RULES:
        sc = 0
        for kw in kws:
            if " " in kw:
                if kw in msg:
                    sc += 2
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", msg):
                    sc += 1
        if sc:
            scores[topic] = sc
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ── GENERAL AGRI GLOSSARY (basic definition answers) ────────────────────────────
GLOSSARY = {
    "pesticide": (
        "🧪 PESTICIDE - Definition\n"
        "A pesticide is a chemical or biological agent used to destroy or repel pests that harm crops "
        "(insects, fungi, weeds, mites, nematodes, rodents).\n\n"
        "Main types by target:\n"
        "• Insecticide - kills insects (e.g. Imidacloprid, Neem oil)\n"
        "• Fungicide - kills fungi (e.g. Mancozeb, Copper Oxychloride)\n"
        "• Herbicide - kills weeds (e.g. Glyphosate, 2,4-D)\n"
        "• Acaricide - kills mites (e.g. Spiromesifen)\n"
        "• Biopesticide - living microbes / botanicals (e.g. Trichoderma, Bacillus thuringiensis)\n\n"
        "Always follow the CIB&RC-approved dose, Pre-Harvest Interval (PHI) and PPE."
    ),
    "insecticide": "🐛 INSECTICIDE: A pesticide that targets insects. Contact types hit the insect body; systemic types are absorbed by the plant and kill sucking/chewing pests. Examples - Imidacloprid 200 SL (0.3 ml/L), Chlorantraniliprole 18.5 SC (0.3 ml/L), Neem Oil (Azadirachtin, 3-5 ml/L). Rotate IRAC classes to avoid resistance.",
    "fungicide": "🍄 FUNGICIDE: A pesticide that controls fungal diseases. Protectants (Mancozeb 75% WP 2.5 g/L, Copper Oxychloride 2.5-3 g/L) shield healthy tissue; systemic curatives (Tebuconazole, Azoxystrobin, Carbendazim) cure inside the leaf. Spray before infection for protectants and at first symptom for systemics.",
    "herbicide": "🌿 HERBICIDE: A pesticide that kills or suppresses weeds. Pre-emergent (applied before weeds sprout - e.g. Pendimethalin) vs post-emergent (on growing weeds - e.g. Glyphosate 3-4 L/ha, 2,4-D). Apply with a weed-free window and protect the crop.",
    "biopesticide": "🌱 BIOPESTICIDE: Pest control agents from natural materials - microbes or botanicals. Examples: Trichoderma viride (root rot), Bacillus thuringiensis/Bt (caterpillars), Beauveria bassiana (whitefly), Pseudomonas fluorescens (wilts), Neem/Azadirachtin. Safer, organic-approved and slow-acting - use preventively.",
    "organic farming": "🌾 ORGANIC FARMING: Cultivation without synthetic chemicals, using natural inputs - compost/vermicompost, green manure, biopesticides (Neem, Trichoderma, Panchagavya, Jeevamrutham), crop rotation, mulching and biological pest control. Improves soil health and premium market value. (Sikkim is India's 100% organic state.)",
    "ipm": "🐞 INTEGRATED PEST MANAGEMENT (IPM): An eco strategy combining cultural, biological and chemical tactics with Economic Threshold Levels (ETL) so you spray only when needed. Steps: scout → set ETL → use resistant varieties/natural enemies → botanical sprays → chemicals only as last resort, rotating chemistry.",
    "photosynthesis": "🌞 PHOTOSYNTHESIS: How green leaves make food. Chlorophyll captures sunlight and converts CO2 (from air) + water (from roots) into glucose + oxygen: 6CO2 + 6H2O + light → C6H12O6 + 6O2. It powers growth and yield - keep leaves healthy and unshaded for maximum rate.",
    "npk": "🧮 NPK RATIO: The 3 primary nutrients in fertilizers - Nitrogen (N, leafy growth), Phosphorus (P, roots & flowers), Potassium (K, overall vigor & disease resistance). Numbers like 10-26-26 mean % of N-P-K. Balance NPK to the soil health card; excess N invites pests and lodging.",
    "crop rotation": "🔄 CROP ROTATION: Growing different crop species in sequence on the same field (e.g. rice → mustard → legume). It breaks pest/disease cycles, restores nutrients (legumes fix nitrogen), improves soil structure and cuts chemical dependence.",
    "seed treatment": "🌰 SEED TREATMENT: Protecting seed with fungicide/insecticide/bio-agent before sowing to stop soil & seed-borne disease. Common: Carbendazim 2 g + Thiram 2 g per kg seed, or Trichoderma/Pseudomonas bio-slurry. Hot-water treatment (50°C, 25-30 min) for bacterial-free seed.",
    "ph level": "🧪 SOIL pH: Acidity/alkalinity (0-14 scale). Most crops like 6.0-7.5. Below 5.5 (acidic) apply lime/gypsum; above 8 (alkaline) add gypsum/organic matter & sulphur. Wrong pH locks out nutrients (iron/zinc chlorosis even if present).",
    "mulching": "🍂 MULCHING: Covering soil with straw, plastic or organic matter to conserve moisture, suppress weeds, moderate soil temperature and reduce fruit rot. Adds hummus as organic mulch decomposes.",
    "fertilizer": "🌾 FERTILIZER: Substance added to supply plant nutrients. Organic (compost, vermicompost, FYM, Panchagavya) improve soil; inorganic (Urea 46%N, DAP 18:46:0, MOP 60%K2O) give quick nutrition. Apply per soil test and at correct growth stages.",
    "soil health card": "🗂️ SOIL HEALTH CARD (SHC): An Indian Govt. soil-testing report giving N-P-K-S, micronutrients, pH, EC & organic carbon for your plot with fertilizer recommendations. Always test before heavy fertilization to save cost and prevent nutrient burn.",
}

GLOSSARY_KEYS = {
    "types_pesticide": "pesticide",
}


# ── ANSWER BUILDERS ────────────────────────────────────────────────────────────
def answer_state(state: str) -> str:
    prof = INDIA_AGRI_DB.get_state_profile(state)
    if not prof:
        return ""
    org = "Yes - this state promotes organic/natural farming." if prof["is_organic_mandate"] else "No statewide organic mandate (conventional + IPM)."
    return (
        f"🌾 AGRICULTURE OF {prof['state']} ({prof['zone']} Zone)\n"
        f"Climate: {prof['climate']}\n"
        f"Major crops: {', '.join(prof['major_crops'])}\n"
        f"Commonly used pesticides: {', '.join(prof['commonly_used_pesticides'])}\n"
        f"Organist focus: {org}\n"
        f"Note: {prof['notes']}"
    )


def answer_crop(crop_name: str, plant_stats: dict) -> str:
    rec = None
    for c in CROPS_DATA:
        if c["name"].lower().startswith(crop_name.lower().split(" (")[0]):
            rec = c
            break
    stats = (plant_stats or {}).get(crop_name.lower().split(" (")[0]) or (plant_stats or {}).get(crop_name.lower())
    lines = [f"🌱 CROP GUIDE - {crop_name.title()}"]
    if rec:
        lines.append(f"Category: {rec['category']}   |   Hindi: {rec['hindi_name']}")
        lines.append(f"Root system: {rec['root_system']}")
        lines.append(f"Stem type: {rec['stem_type']}")
        lines.append(f"Grown mainly in: {rec['major_states']}")
        lines.append(f"Key diseases/pests: {rec['primary_diseases']}")
    if stats:
        lines.append("\n💧 Cultivation & care:")
        lines.append(f"  Water: {stats.get('water_used','-')}")
        lines.append(f"  Soil type: {stats.get('soil_type','-')}")
        lines.append(f"  pH: {stats.get('pH_level','-')}   |   Temperature: {stats.get('temperature','-')}")
        lines.append(f"  Fertilizer: {stats.get('fertilizer','-')}")
        lines.append(f"  Harvest time: {stats.get('harvest_time','-')}")
    if not rec and not stats:
        return (
            f"🌱 {crop_name.title()} - General Cultivation Guide\n"
            f"• Choose a well-drained fertile plot and certified disease-free seed/transplants.\n"
            f"• Maintain steady moisture (avoid waterlogging), balanced NPK + organic manure.\n"
            f"• Ensure spacing for airflow; scout twice a week for pests & leaf spots.\n"
            f"• Rotate with a non-host crop and use neem/bio sprays preventively.\n"
            f"Ask me about its watering schedule, fertilizers, or common diseases for more detail."
        )
    return "\n".join(lines)


def answer_crop_diseases(crop_name: str) -> str:
    rel = [d for k, d in DISEASE_BY_KEY.items() if (d.get("crop", "").lower() == crop_name.lower().split(" (")[0] or crop_name.lower().split(" (")[0] in k)]
    rec = next((c for c in CROPS_DATA if c["name"].lower().startswith(crop_name.lower().split(" (")[0])), None)
    out = [f"🦠 DISEASES & PESTS OF {crop_name.title()}"]
    if rec:
        out.append(f"Major field problems: {rec['primary_diseases']}")
    if rel:
        names = []
        seen = set()
        for d in rel[:12]:
            if d["name"] not in seen:
                seen.add(d["name"])
                names.append(f"• {d['name']} ({d.get('category','')})")
        out.append("Known pathology:\n" + "\n".join(names))
    if len(out) == 1:
        return ""
    out.append("\nAsk me the symptoms, treatment or prevention of any of these.")
    return "\n".join(out)


def answer_disease(disease: dict, topic: str) -> str:
    name = disease.get("name", "This disease")
    cat = _pathogen_category(name, disease.get("category", ""))
    crop = disease.get("crop", "")
    desc = disease.get("desc", "")
    cure = CURE_DB.get(name, desc)

    if topic == "symptoms":
        return f"🔬 SYMPTOMS - {name}\n{cure[:700]}\n\nPathogen category: {cat}."
    if topic == "prevention":
        methods = _prevention_for_category(cat)
        return f"🛡️ PREVENTION OF {name}\n" + "\n".join(f"• {m}" for m in methods)
    # treatment / default
    chem, org = _curated_for(name, cat)
    head = f"💊 TREATMENT - {name} ({cat}{', ' + crop if crop else ''})\n"
    body = f"Diagnosis notes: {cure[:350]}...\n" if cure and len(cure) > 350 else (f"Diagnosis notes: {cure}\n" if cure else "")
    out = head + body
    if org:
        out += "\n🍃 Organic / bio control:\n" + "\n".join(f"• {o}" for o in org)
    if chem:
        out += "\n\n🧪 Chemical prescription:\n" + "\n".join(
            f"• {c['name']} - dose {c['dosage']}, interval {c['interval']}, PHI {c['phi_days']}" for c in chem)
    out += "\n\n🚨 Immediate: sanitize tools, rogue out badly infected plants, and improve canopy airflow & drainage."
    return out


def _pathogen_category(name: str, stored: str = "") -> str:
    """Trust curated disease_formatter metadata over the raw JSON 'category' field."""
    try:
        meta = format_disease_prediction(name or "")
        pt = (meta.get("pathogen_type") or "").strip()
        if pt and pt.lower() not in ("healthy",):
            return pt
    except Exception:
        pass
    return stored or "Fungal"


def _category_from_words(msg: str):
    """Detect a general pathogen category from loose words in the message."""
    if re.search(r"\bfungal\b|\bfungus\b|\bmildew\b|\brust\b|\brot\b", msg):
        return "Fungal"
    if re.search(r"\bbacteri\w*\b", msg):
        return "Bacterial"
    if re.search(r"\bvirus\b|\bviral\b|\bmosaic\b|\bcurl\b", msg):
        return "Viral"
    if re.search(r"\bpest\b|\binsect\b|\bmites?\b|\bworm\b|\borer\b|\baphid\w*\b|\bwhitefl\w*\b", msg):
        return "Pest / Insect"
    return None


def answer_category(topic: str, cat: str) -> str:
    """General guidance for a whole pathogen category (no specific disease named)."""
    label = cat
    if topic == "prevention":
        methods = _prevention_for_category(cat)
        return f"🛡️ GENERAL PREVENTION - {label} Problems\n" + "\n".join(f"• {m}" for m in methods)
    try:
        from treatment_protocols import SYMPTOM_PROFILES
    except Exception:
        SYMPTOM_PROFILES = {}
    key = "Fungal"
    cl = cat.lower()
    if "bacteri" in cl: key = "Bacterial"
    elif "vir" in cl: key = "Viral"
    elif "pest" in cl or "insect" in cl: key = "Pest / Insect"
    if topic == "symptoms":
        return f"🔬 TYPICAL {label.upper()} SYMPTOMS\n{SYMPTOM_PROFILES.get(key, SYMPTOM_PROFILES.get('Fungal'))}"
    methods = _prevention_for_category(cat)
    return (f"💡 MANAGING {label.upper()} PROBLEMS (general IPM)\n"
            + "\n".join(f"• {m}" for m in methods[:6])
            + "\n\nName the exact disease or crop for a precise prescription.")


def _prevention_for_category(cat: str):
    c = (cat or "").lower()
    try:
        from treatment_protocols import PREVENTION_ROADMAPS
    except Exception:
        return []
    key = "Fungal"
    if "healthy" in c:
        key = "Healthy"
    elif "bacteri" in c:
        key = "Bacterial"
    elif "vir" in c:
        key = "Viral"
    elif "pest" in c or "insect" in c or "mite" in c:
        key = "Pest / Insect"
    return PREVENTION_ROADMAPS.get(key, [])


def _curated_for(name: str, cat: str):
    try:
        from treatment_protocols import CURATED_TREATMENTS, build_generic_protocol
    except Exception:
        return [], []
    key = name.lower().replace("___", "_").replace("__", "_").replace(" ", "_")
    for k, v in CURATED_TREATMENTS.items():
        if k in key or key in k:
            return v.get("chemical", []), v.get("organic", [])
    g = build_generic_protocol("", name, cat, False)
    return g["chemical"], g["organic"]


def answer_chemical(name: str, topic: str) -> str:
    rec = get_pesticide_record(name)
    safety = INDIA_AGRI_DB.validate_pesticide_safety(name)
    banned = next((b for b in BANNED_PESTICIDES_DATA if b["name"].lower() in name.lower() or name.lower() in b["name"].lower()), None)
    if banned:
        return (
            f"⛔ {banned['name']} - {banned['status']}\n"
            f"Legal basis: {banned['legal_basis']}\n"
            f"Hazard class: {banned['hazard_class']}\n"
            f"Why: {banned['hazard_reason']}\n"
            f"✅ Approved alternative: {banned['organic_alternative']}"
        )
    if rec:
        head = f"🧪 {rec['name']}\n"
        if topic == "dosage":
            return head + (
                f"Category: {rec['category']}\n"
                f"⚗️ Dosage: {rec['dosage']}\n"
                f"Target: {rec['target_diseases']}\n"
                f"Applied to: {rec['target_part']}\n"
                f"Nature: {rec['organic_status']}   | CIB&RC: {rec['cibrc_status']}\n\n"
                f"💡 Mix into a clean knapsack tank; maintain label PHI before harvest."
            )
        return head + (
            f"Category: {rec['category']}   |   Type: {rec['type']}\n"
            f"Controls: {rec['target_diseases']}\n"
            f"Target part: {rec['target_part']}\n"
            f"Dosage: {rec['dosage']}\n"
            f"Organic status: {rec['organic_status']}   |   CIB&RC: {rec['cibrc_status']}"
        )
    if safety and not safety.get("is_safe", True):
        return (
            f"⛔ {safety['chemical']} is {safety['status']}.\n"
            f"Reason: {safety.get('hazard_reason','')}\n"
            f"✅ Use instead: {safety.get('recommended_organic_alternative','')}"
        )
    return f"🧪 {name}: " + (
        safety.get("recommended_organic_alternative") and f"CIB&RC status {safety['status']}. A safer bio option is {safety['recommended_organic_alternative']}." or f"Status: {safety['status']}."
    )


def answer_organic() -> str:
    bios = [p for p in PESTICIDES_LIBRARY if "organic" in p.get("cibrc_status", "").lower() or "bio" in p.get("category", "").lower()]
    out = ["🌿 ORGANIC & BIOPESTICIDE OPTIONS"]
    for b in bios:
        out.append(f"• {b['name']} ({b['category']}) - {b['dosage']}\n   Controls: {b['target_diseases']}")
    out.append("\nGeneral: Neem oil (3-5 ml/L), Trichoderma viride (2.5 kg/ha soil), Pseudomonas fluorescens (5 g/L), "
               "Bordeaux mixture 1%, Panchagavya 3%, Bt for caterpillars, Beauveria for whitefly.")
    return "\n".join(out)


def answer_anatomy(term: str) -> str:
    t = term.lower()
    tier = None
    for ps in PLANT_STRUCTURES_DATA:
        if any(part.lower() in t for part in ps["anatomical_parts"].split(",")) or ps["tier_name"].lower().split(" ")[0] in t:
            tier = ps
            break
    if "photosynthesis" in t:
        return GLOSSARY["photosynthesis"]
    if not tier:
        return ""
    return (
        f"🌿 {tier['tier_name']}\n"
        f"Parts: {tier['anatomical_parts']}\n"
        f"Function: {tier['primary_function']}\n"
        f"Diseases it catches: {tier['vulnerable_pathogens']}\n"
        f"Best spray method: {tier['optimal_actuator']}\n"
        f"Note: {tier['notes']}"
    )


def answer_glossary(msg: str):
    for key in ["pesticide", "insecticide", "fungicide", "herbicide", "biopesticide",
                "organic farming", "ipm", "photosynthesis", "npk", "crop rotation",
                "seed treatment", "ph level", "mulching", "fertilizer", "soil health card"]:
        if key in msg or (key == "ph level" and ("ph" in msg and "soil" in msg)) or (key == "npk" and re.search(r"\bnpk\b", msg)):
            return GLOSSARY[key]
    return ""


# ── CONVERSATIONAL ─────────────────────────────────────────────────────────────
def answer_meta(topic: str) -> str:
    if topic == "greeting":
        return "🙏 Namaste! I'm your AI Agri-Bot. Ask me about crops, pesticides & their doses, plant diseases, organic remedies, prevention, soil, irrigation or state-wise farming in India!"
    if topic == "thanks":
        return "😊 You're welcome! Keep your crops healthy. Ask me anytime about pesticides, diseases or cultivation."
    if topic == "bye":
        return "🌾 Happy farming! Come back with any crop or pesticide question. Goodbye!"
    if topic == "identity":
        return "🤖 I'm the Agri-Bot, a plant-pathology & agrochemical assistant built for Indian farmers. I use CIB&RC/ICAR knowledge to advise on pesticides, diseases and crop care."
    if topic == "capabilities":
        return (
            "✅ Here's what I can help with:\n"
            "• Pesticides - what they are, types, doses (e.g. 'Mancozeb dosage')\n"
            "• Banned chemicals (e.g. 'is Endosulfan banned?')\n"
            "• Organic / biopesticide alternatives\n"
            "• Crop guides - how to grow, water, fertilize, harvest\n"
            "• Disease symptoms, treatment & prevention\n"
            "• Soil, pH, irrigation, seeds, fertilizers (NPK)\n"
            "• Plant anatomy & photosynthesis\n"
            "• State-wise crops & pesticides\n\n"
            "Try: 'how to grow tomato', 'treat potato late blight', 'neem oil dosage', 'crops in Punjab'."
        )
    return ""


# ── MAIN ENTRY ─────────────────────────────────────────────────────────────────
def get_agri_bot_response(message: str, plant_stats: dict = None) -> str:
    raw = (message or "").strip()
    msg = norm(raw)
    if not msg:
        return "Please type an agriculture question - crops, pesticides, diseases, soil or farming tips."

    topics = detect_topics(msg)
    top_topic = topics[0][0] if topics else ""

    # 1) Pure conversational / meta intents
    if top_topic in ("greeting", "thanks", "bye", "identity", "capabilities") and len(msg.split()) <= 5:
        return answer_meta(top_topic)

    # 2) Entities
    state = find_state(msg)
    chemical = find_chemical(msg)
    disease = find_disease(msg)
    crop = find_crop(msg)
    if disease and not crop:
        crop = (disease.get("crop") or "").lower() or None

    # 3) Topic + entity routing
    if top_topic in ("types_pesticide",) and not chemical:
        g = answer_glossary(msg) or GLOSSARY["pesticide"]
        return g

    # Dosage / chemical queries
    if chemical and top_topic in ("dosage", "fungicide", "insecticide", "banned"):
        return answer_chemical(chemical, "dosage" if top_topic != "banned" else "banned")

    if top_topic == "banned":
        if chemical:
            return answer_chemical(chemical, "banned")
        names = ", ".join(b["name"] for b in BANNED_PESTICIDES_DATA)
        return f"⛔ BANNED/RESTRICTED IN INDIA (CIB&RC): {names}.\nThese are hazardous - switch to Neem, Trichoderma, Bt or Panchagavya. Ask me about a specific one."

    if top_topic == "organic":
        return answer_organic()

    # Disease topics (symptoms / treatment / prevention / info)
    if disease and top_topic in ("symptoms", "treatment", "prevention", "disease_info"):
        return answer_disease(disease, top_topic)

    # General pathogen-category guidance when no specific disease is named
    if (not disease) and top_topic in ("symptoms", "treatment", "prevention", "disease_info", "fungicide", "insecticide"):
        cat = _category_from_words(msg)
        if cat:
            topic = top_topic if top_topic in ("prevention", "symptoms") else "treatment"
            return answer_category(topic, cat)

    # Crop cultivation / nutrition / irrigation / harvest / grow
    if crop and top_topic in ("grow", "nutrition", "irrigation", "harvest", "crop_info", "seed"):
        full = answer_crop(crop, plant_stats)
        if full:
            return full

    if crop and top_topic == "crop_diseases":
        d = answer_crop_diseases(crop)
        if d:
            return d

    # Region / state
    if state and top_topic == "region":
        return answer_state(state)

    # Plant anatomy
    if top_topic == "plant_anatomy":
        a = answer_anatomy(raw)
        if a:
            return a

    # Generic glossary for single-word "what is X" style basics
    if top_topic in ("nutrition", "soil", "irrigation", "climate", "seed", "herbicide") and not crop and not disease:
        g = answer_glossary(msg)
        if g:
            return g
        if top_topic == "soil":
            return GLOSSARY["ph level"]
        if top_topic == "herbicide":
            return GLOSSARY["herbicide"]
        if top_topic == "nutrition":
            return GLOSSARY["npk"]

    # Disease without a clear sub-topic -> give overview + treatment
    if disease:
        return answer_disease(disease, "treatment")

    # Crop alone -> full guide
    if crop:
        full = answer_crop(crop, plant_stats)
        if full:
            return full

    # State alone -> profile
    if state:
        return answer_state(state)

    # Chemical alone -> info
    if chemical:
        return answer_chemical(chemical, "info")

    # Glossary for basic "what is ..." even if no topic scored
    g = answer_glossary(msg)
    if g:
        return g

    # 4) Universal DB search fallback
    search = INDIA_AGRI_DB.search_agri_knowledge(raw)
    parts = []
    if search.get("crops"):
        parts.append("🌱 Crops: " + ", ".join(c["name"] for c in search["crops"][:6]))
    if search.get("pesticides"):
        parts.append("🧪 Pesticides: " + ", ".join(p["name"] for p in search["pesticides"][:6]))
    if search.get("banned_chemicals_flagged"):
        parts.append("⛔ Flagged (banned): " + ", ".join(b["name"] for b in search["banned_chemicals_flagged"][:4]))
    if search.get("states"):
        parts.append("📍 States: " + ", ".join(search["states"][:6]))
    if parts:
        return "🔎 I found related knowledge:\n" + "\n".join(parts) + "\n\nAsk me more specifically (e.g. dosage, symptoms, treatment, how to grow)."

    # 5) Wikipedia fallback
    try:
        import wikipedia
        results = wikipedia.search(raw + " agriculture crop plant pesticide")
        if results:
            return f"📖 {wikipedia.summary(results[0], sentences=3)}"
    except Exception:
        pass

    # 6) Helpful redirect
    return (
        "🌾 I specialise in practical agriculture. I couldn't pin that exact term, but I can help with:\n"
        "• Pesticides & dosages  • Plant disease symptoms/treatment/prevention\n"
        "• Crop growing guides  • Organic & biopesticide alternatives\n"
        "• Soil, pH, irrigation, NPK  • State-wise farming\n\n"
        "Try asking: 'how to grow tomato', 'dosage of mancozeb', 'treat potato late blight', "
        "'prevent fungal disease', 'is endosulfan banned', or 'crops in Kerala'."
    )
