"""
india_agri_db.py
================
Comprehensive Indian Agriculture & Agrochemical Knowledgebase Engine.
Covers:
1. All 28 States of India (major crops, approved pesticides, organic mandates)
2. Three-tier Plant Anatomy (Root System, Stem System, Canopy/Leaves)
3. CIBRC Safety Validation (Flagging banned chemicals: Endosulfan, Phorate, Methyl Parathion, Dichlorvos, Alachlor)
4. Organic & Bio-pesticide Alternatives (Neem Azadirachtin, Panchagavya, Trichoderma viride, Pseudomonas fluorescens)
5. SQLite persistent storage and fast query API.
"""

import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "india_agriculture.db")

# ── 28 STATES SEED DATA ────────────────────────────────────────────────────────
STATES_DATA = [
    {
        "id": 1, "state": "Kerala", "zone": "South", "is_organic_mandate": 0,
        "major_crops": ["Coconut", "Rubber", "Tea", "Cardamom", "Black Pepper", "Paddy"],
        "commonly_used_pesticides": ["Copper Oxychloride", "Chlorpyrifos", "Carbendazim"],
        "climate": "Tropical Humid / Western Ghats",
        "notes": "High humidity, high fungal blister blight and fungal leaf rot incidence."
    },
    {
        "id": 2, "state": "Tamil Nadu", "zone": "South", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Sugarcane", "Groundnut", "Banana", "Cotton", "Maize"],
        "commonly_used_pesticides": ["Imidacloprid", "Cartap Hydrochloride", "Chlorantraniliprole", "Mancozeb"],
        "climate": "Tropical Coastal / Semi-arid Interior",
        "notes": "Intensive paddy delta and sugarcane belts requiring stem borer and blast management."
    },
    {
        "id": 3, "state": "Andhra Pradesh", "zone": "South", "is_organic_mandate": 0,
        "major_crops": ["Chilli", "Cotton", "Paddy", "Tobacco", "Maize"],
        "commonly_used_pesticides": ["Acephate", "Thiamethoxam", "Profenofos", "Diafenthiuron"],
        "climate": "Coastal Humid to Semi-arid Deccan",
        "notes": "Hub of Indian chilli and cotton; high pressure from invasive thrips and bollworms."
    },
    {
        "id": 4, "state": "Telangana", "zone": "South", "is_organic_mandate": 0,
        "major_crops": ["Cotton", "Paddy", "Maize", "Chilli", "Turmeric"],
        "commonly_used_pesticides": ["Fipronil", "Spinetoram", "Monocrotophos"],
        "climate": "Semi-arid Tropical",
        "notes": "Vast cotton and red gram acreages. Requires vector control for leaf curl."
    },
    {
        "id": 5, "state": "Karnataka", "zone": "South", "is_organic_mandate": 0,
        "major_crops": ["Coffee", "Ragi", "Paddy", "Sugarcane", "Sunflower", "Pigeon Pea"],
        "commonly_used_pesticides": ["Hexaconazole", "Propiconazole", "Cypermethrin"],
        "climate": "Western Ghats Highland to Deccan Plateau",
        "notes": "Leading producer of coffee and ragi; coffee rust and sunflower downy mildew control."
    },
    {
        "id": 6, "state": "Goa", "zone": "West", "is_organic_mandate": 0,
        "major_crops": ["Cashew", "Coconut", "Paddy", "Arecanut"],
        "commonly_used_pesticides": ["Bordeaux Mixture", "Carbaryl", "Glyphosate"],
        "climate": "Coastal Maritime Humid",
        "notes": "Heavy monsoon rains necessitate rainfast copper fungicide and Bordeaux mixture sprays."
    },
    {
        "id": 7, "state": "Maharashtra", "zone": "West", "is_organic_mandate": 0,
        "major_crops": ["Sugarcane", "Cotton", "Soybean", "Grapes", "Onion"],
        "commonly_used_pesticides": ["Dimethoate", "Sulphur", "Emamectin Benzoate", "Lambda-cyhalothrin"],
        "climate": "Deccan Semi-arid to Coastal Konkan",
        "notes": "Global grape and onion hub. Downy mildew and thrips require strict MRL adherence."
    },
    {
        "id": 8, "state": "Gujarat", "zone": "West", "is_organic_mandate": 0,
        "major_crops": ["Cotton", "Groundnut", "Castor", "Cumin"],
        "commonly_used_pesticides": ["Acetamiprid", "Diafenthiuron", "Profenofos"],
        "climate": "Arid to Semi-arid Coastal",
        "notes": "Top producer of cotton and groundnut. Whitefly and cumin blight monitoring."
    },
    {
        "id": 9, "state": "Rajasthan", "zone": "North-West", "is_organic_mandate": 0,
        "major_crops": ["Mustard", "Pearl Millet (Bajra)", "Green Gram", "Cumin", "Coriander"],
        "commonly_used_pesticides": ["Malathion", "Quinalphos", "Dimethoate"],
        "climate": "Arid Desert to Semi-arid",
        "notes": "Mustard white rust and cumin powdery mildew require targeted seasonal foliar sprays."
    },
    {
        "id": 10, "state": "Punjab", "zone": "North", "is_organic_mandate": 0,
        "major_crops": ["Wheat", "Paddy (Basmati)", "Cotton", "Potato"],
        "commonly_used_pesticides": ["Pretilachlor", "Tricyclazole", "Glyphosate", "Thiamethoxam"],
        "climate": "Sub-tropical Semi-arid Plains",
        "notes": "Granary of India; strict yellow rust (Puccinia striiformis) and basmati blast containment."
    },
    {
        "id": 11, "state": "Haryana", "zone": "North", "is_organic_mandate": 0,
        "major_crops": ["Wheat", "Paddy", "Mustard", "Sugarcane", "Cotton"],
        "commonly_used_pesticides": ["Chlorpyrifos", "Carbendazim", "Imidacloprid"],
        "climate": "Semi-arid Indo-Gangetic Plains",
        "notes": "High-yield wheat and mustard belts; strict root rot and aphid suppression."
    },
    {
        "id": 12, "state": "Himachal Pradesh", "zone": "North", "is_organic_mandate": 0,
        "major_crops": ["Apple", "Potato", "Maize", "Vegetables"],
        "commonly_used_pesticides": ["Mancozeb", "Diphos", "Dodine", "Lime Sulphur"],
        "climate": "Temperate Montane / Sub-Himalayan",
        "notes": "Apple scab (Venturia inaequalis) and mite control under mountain canopy."
    },
    {
        "id": 13, "state": "Uttarakhand", "zone": "North", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Wheat", "Sugarcane", "Fruits", "Pulses"],
        "commonly_used_pesticides": ["Copper Fungicides", "Cypermethrin", "Carbaryl"],
        "climate": "Himalayan Foothills / Terai",
        "notes": "Terai plains grow sugarcane and rice; hill tracts focus on organic hill pulses and fruits."
    },
    {
        "id": 14, "state": "Uttar Pradesh", "zone": "North", "is_organic_mandate": 0,
        "major_crops": ["Sugarcane", "Wheat", "Potato", "Mustard", "Mango"],
        "commonly_used_pesticides": ["Carbofuran", "Chlorpyrifos", "Mancozeb"],
        "climate": "Humid Sub-tropical Indo-Gangetic",
        "notes": "India's highest sugarcane and potato producer; late blight and red rot surveillance."
    },
    {
        "id": 15, "state": "Bihar", "zone": "East", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Maize", "Wheat", "Jute", "Litchi"],
        "commonly_used_pesticides": ["Phorate", "Imidacloprid", "Mancozeb"],
        "climate": "Sub-tropical Gangetic Alluvial",
        "notes": "Shahi Litchi fruit borer and maize armyworm require bio-rational interventions."
    },
    {
        "id": 16, "state": "Jharkhand", "zone": "East", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Pulses", "Maize", "Vegetables"],
        "commonly_used_pesticides": ["Chlorpyrifos", "Carbendazim", "Cypermethrin"],
        "climate": "Tropical Plateau Sub-humid",
        "notes": "Plateau agriculture; focus on soil moisture conservation and pulse pod borer protection."
    },
    {
        "id": 17, "state": "West Bengal", "zone": "East", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Jute", "Tea", "Potato", "Mango"],
        "commonly_used_pesticides": ["Cartap Hydrochloride", "Hexaconazole", "Neem Formulations"],
        "climate": "Tropical Humid Deltaic",
        "notes": "Top rice and jute producer. Darjeeling tea gardens enforce strict organic MRL regulations."
    },
    {
        "id": 18, "state": "Odisha", "zone": "East", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Pulses", "Groundnut", "Cashew", "Sugarcane"],
        "commonly_used_pesticides": ["Triazophos", "Imidacloprid", "Carbendazim"],
        "climate": "Coastal Tropical Humid",
        "notes": "Mahanadi delta paddy; brown plant hopper (BPH) and sheath rot monitoring."
    },
    {
        "id": 19, "state": "Chhattisgarh", "zone": "Central", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Maize", "Oilseeds", "Vegetables"],
        "commonly_used_pesticides": ["Cartap", "Chlorpyrifos", "Tricyclazole"],
        "climate": "Tropical Wet-and-Dry",
        "notes": "Rice bowl of central India; traditional varieties managed with bio-fungicides."
    },
    {
        "id": 20, "state": "Madhya Pradesh", "zone": "Central", "is_organic_mandate": 0,
        "major_crops": ["Soybean", "Wheat", "Chickpea", "Mustard"],
        "commonly_used_pesticides": ["Chlorantraniliprole", "Thiamethoxam", "Tebuconazole"],
        "climate": "Sub-tropical Continental",
        "notes": "Soybean and pulse hub of India; pod borer and rust control across extensive black soils."
    },
    {
        "id": 21, "state": "Sikkim", "zone": "North-East", "is_organic_mandate": 1,
        "major_crops": ["Cardamom", "Ginger", "Orange", "Buckwheat"],
        "commonly_used_pesticides": ["Bio-pesticides (Neem oil, Trichoderma, Vermicompost)"],
        "climate": "Montane Temperate to Alpine",
        "notes": "100% Certified Organic State by law. All synthetic chemical pesticides strictly prohibited."
    },
    {
        "id": 22, "state": "Assam", "zone": "North-East", "is_organic_mandate": 0,
        "major_crops": ["Tea", "Paddy", "Jute", "Mustard"],
        "commonly_used_pesticides": ["Copper Oxychloride", "Ethion", "Propargite"],
        "climate": "Sub-tropical Humid Monsoon Valley",
        "notes": "Brahmaputra valley tea estates; red spider mite and black rot control."
    },
    {
        "id": 23, "state": "Arunachal Pradesh", "zone": "North-East", "is_organic_mandate": 1,
        "major_crops": ["Paddy", "Maize", "Orange", "Pineapple", "Ginger"],
        "commonly_used_pesticides": ["Neem Oil", "Copper Hydroxide", "Bio-fungicides"],
        "climate": "Humid Sub-tropical to Alpine",
        "notes": "Emphasis on natural farming and organic pest management for indigenous crops."
    },
    {
        "id": 24, "state": "Nagaland", "zone": "North-East", "is_organic_mandate": 1,
        "major_crops": ["Paddy", "Maize", "King Chilli", "Cardamom"],
        "commonly_used_pesticides": ["Organic Bio-pesticides", "Lime Sulphur"],
        "climate": "Sub-tropical Hill Humid",
        "notes": "Famous Naga King Chilli (Bhut Jolokia); protected using traditional bio-controls."
    },
    {
        "id": 25, "state": "Manipur", "zone": "North-East", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Maize", "Mustard", "Fruits"],
        "commonly_used_pesticides": ["Neem Formulations", "Carbendazim"],
        "climate": "Sub-tropical Monsoon Valley",
        "notes": "Chak-hao (Black Aromatic Rice) cultivation; priority on bio-rational IPM."
    },
    {
        "id": 26, "state": "Mizoram", "zone": "North-East", "is_organic_mandate": 1,
        "major_crops": ["Paddy", "Ginger", "Turmeric", "Bamboo", "Fruits"],
        "commonly_used_pesticides": ["Bio-pesticides", "Organic Compost Controls"],
        "climate": "Montane Sub-tropical",
        "notes": "Organic ginger and turmeric value chains; strict avoidance of chemical residues."
    },
    {
        "id": 27, "state": "Tripura", "zone": "North-East", "is_organic_mandate": 0,
        "major_crops": ["Paddy", "Rubber", "Tea", "Pineapple", "Bamboo"],
        "commonly_used_pesticides": ["Copper Oxychloride", "Chlorpyrifos"],
        "climate": "Tropical Humid",
        "notes": "Queen Pineapple and natural rubber plantations; fungal shoot dieback protection."
    },
    {
        "id": 28, "state": "Meghalaya", "zone": "North-East", "is_organic_mandate": 1,
        "major_crops": ["Paddy", "Potato", "Lakadong Turmeric", "Ginger"],
        "commonly_used_pesticides": ["Organic Bio-pesticides", "Bordeaux Mixture"],
        "climate": "High-rainfall Sub-tropical Plateau",
        "notes": "Lakadong Turmeric (high curcumin) grown exclusively through certified organic methods."
    }
]

# ── PLANT STRUCTURE ANATOMY ───────────────────────────────────────────────────
PLANT_STRUCTURES_DATA = [
    {
        "id": 1,
        "tier_name": "Bottom Part - Root System",
        "anatomical_parts": "Taproot, Fibrous Roots, Root Hairs, Mycorrhizae",
        "primary_function": "Anchors plant firmly in soil; absorbs water and essential mineral nutrients (N, P, K) to transport upwards.",
        "root_types": "Tap Root System: Penetrates deep into soil in trees and dicots (Mango, Neem). Fibrous Root System: Spreads along topsoil layer in monocots, paddy, wheat, and grasses.",
        "vulnerable_pathogens": "Root Rot (Rhizoctonia, Pythium), Bacterial Wilt (Ralstonia), Fusarium Wilt, Root Knot Nematodes.",
        "optimal_actuator": "Smart Solenoid Drip Valves (Subterranean Fertigation & Bio-inoculant Drenching)",
        "actuator_code": "VALVE_DRIP_ROOT",
        "notes": "Aerial drones cannot penetrate dense soil to reach roots. Root rot must be treated through drip irrigation with Trichoderma viride or Pseudomonas fluorescens."
    },
    {
        "id": 2,
        "tier_name": "Middle Part - Stem / Trunk System",
        "anatomical_parts": "Stem, Trunk, Bark, Branches, Xylem, Phloem, Nodes",
        "primary_function": "Provides structural support; Xylem transports water/minerals upward; Phloem translocates photosynthesized sugars downward.",
        "root_types": "Woody Bark (trees, perennial orchards) vs Soft Green Stems (herbs, annual crops, paddy tillers).",
        "vulnerable_pathogens": "Sugarcane Red Rot (Colletotrichum falcatum), Sheath Blight, Stem Cankers, Gummosis, Stem Borer tunnels.",
        "optimal_actuator": "Targeted Low-Canopy Drone Swarm (Oblique Nozzle Angle) & Soil Injections",
        "actuator_code": "DRONE_OBLIQUE_STEM",
        "notes": "Requires low flight altitude (1.2m - 1.8m) with angled spray nozzles to hit stem collars and lower tillers."
    },
    {
        "id": 3,
        "tier_name": "Top Part - Leaves, Canopy & Organs",
        "anatomical_parts": "Leaves, Terminal Buds, Petioles, Flowers, Inflorescence, Fruits, Seeds",
        "primary_function": "Photosynthesis (chlorophyll), transpiration cooling, stomatal gas exchange (O2/CO2), and reproductive pollination.",
        "root_types": "Broadleaf dicots vs Narrow-blade monocots.",
        "vulnerable_pathogens": "Leaf Rust (Puccinia), Early/Late Blight (Alternaria/Phytophthora), Powdery Mildew, Anthracnose, Leaf Curl Viruses, Aphids, Whiteflies.",
        "optimal_actuator": "Worker Drone Swarm (High-Speed Aerial Micro-Atomized Foliar Spraying)",
        "actuator_code": "DRONE_AERIAL_FOLIAR",
        "notes": "Ideal target for autonomous aerial drones. Electrostatic atomized droplets (80-150 microns) ensure uniform canopy coverage without chemical runoff."
    }
]

# ── CIBRC BANNED & RESTRICTED PESTICIDES IN INDIA ──────────────────────────────
BANNED_PESTICIDES_DATA = [
    {
        "name": "Endosulfan",
        "status": "BANNED",
        "legal_basis": "Hon'ble Supreme Court of India Order & CIBRC Notification",
        "hazard_class": "Extremely Hazardous (Organochlorine)",
        "hazard_reason": "Endocrine disruptor, severe neurotoxicity, genetic teratogenicity, persistent environmental bioaccumulation.",
        "organic_alternative": "Neem Oil (Azadirachtin 1500-10000 ppm) + Beauveria bassiana"
    },
    {
        "name": "Phorate",
        "status": "BANNED / STRICTLY REGULATED",
        "legal_basis": "CIBRC Gazette Notification S.O. 3951(E)",
        "hazard_class": "WHO Class Ia (Extremely Hazardous Organophosphate)",
        "hazard_reason": "Extreme mammalian oral toxicity; rapid acetylcholinesterase inhibition; groundwater contamination.",
        "organic_alternative": "Neem Cake soil incorporation (250 kg/ha) + Trichoderma viride"
    },
    {
        "name": "Methyl Parathion",
        "status": "BANNED",
        "legal_basis": "CIBRC Banned Chemicals Registry",
        "hazard_class": "WHO Class Ia (Organophosphate)",
        "hazard_reason": "Lethal systemic toxicity to farmers, non-target pollinators, and wildlife.",
        "organic_alternative": "Panchagavya foliar spray (3%) + Spinetoram or Bacillus thuringiensis"
    },
    {
        "name": "Dichlorvos",
        "status": "BANNED / PHASED OUT",
        "legal_basis": "CIBRC Review Committee Directives",
        "hazard_class": "WHO Class Ib (Highly Hazardous Organophosphate)",
        "hazard_reason": "Vapor toxicity, suspected human carcinogen, rapid dermal penetration.",
        "organic_alternative": "Dashparni Ark or Neem Seed Kernel Extract (NSKE 5%)"
    },
    {
        "name": "Alachlor",
        "status": "BANNED",
        "legal_basis": "Ministry of Agriculture Gazette S.O. 2486(E)",
        "hazard_class": "Class II Carcinogenic Chloroacetanilide",
        "hazard_reason": "Leaches into drinking aquifers; classified as probable human carcinogen.",
        "organic_alternative": "Straw mulching, cover cropping, and manual rotary weeding"
    },
    {
        "name": "Carbofuran",
        "status": "RESTRICTED / BANNED IN MULTIPLE CROPS",
        "legal_basis": "CIBRC Restriction Order",
        "hazard_class": "WHO Class Ib (Carbamate)",
        "hazard_reason": "Severe avian toxicity, kills beneficial soil earthworms and aquatic fauna.",
        "organic_alternative": "Trichoderma harzianum + Pseudomonas fluorescens enriched Farm Yard Manure"
    }
]

# ── COMPREHENSIVE PESTICIDE LIBRARY ───────────────────────────────────────────
PESTICIDES_LIBRARY = [
    {
        "name": "Copper Oxychloride 50% WP",
        "category": "Fungicide / Bactericide",
        "type": "Inorganic Copper Protectant",
        "target_diseases": "Bacterial Blight, Downy Mildew, Rust, Canker, Anthracnose",
        "target_part": "Leaves & Stem",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "2.5 - 3.0 g/L (500-750 g/acre)",
        "organic_status": "Permitted in Organic IPM (with strict Cu ceiling)",
        "cibrc_status": "APPROVED",
        "states_used": ["Kerala", "Assam", "Tripura", "Uttarakhand"]
    },
    {
        "name": "Mancozeb 75% WP",
        "category": "Fungicide",
        "type": "Dithiocarbamate Multi-Site Protectant (FRAC M03)",
        "target_diseases": "Early Blight, Late Blight, Leaf Rust, Leaf Spot, Tikka Disease",
        "target_part": "Leaves & Canopy",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "2.0 - 2.5 g/L (600-800 g/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Tamil Nadu", "Himachal Pradesh", "Uttar Pradesh", "Bihar"]
    },
    {
        "name": "Azoxystrobin 23% SC",
        "category": "Fungicide",
        "type": "Strobilurin / QoI Systemic Fungicide (FRAC 11)",
        "target_diseases": "Powdery Mildew, Downy Mildew, Rust, Anthracnose, Sheath Blight",
        "target_part": "Leaves & Canopy",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "1.0 ml/L (200 ml/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Punjab", "Maharashtra", "Tamil Nadu", "Telangana"]
    },
    {
        "name": "Hexaconazole 5% EC",
        "category": "Fungicide",
        "type": "Triazole DMI Systemic (FRAC 3)",
        "target_diseases": "Sheath Blight, Powdery Mildew, Rust, Scab",
        "target_part": "Leaves & Stem",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "2.0 ml/L (400 ml/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Karnataka", "West Bengal", "Andhra Pradesh"]
    },
    {
        "name": "Propiconazole 25% EC (Tilt)",
        "category": "Fungicide",
        "type": "Triazole DMI Systemic (FRAC 3)",
        "target_diseases": "Wheat Yellow Rust, Rice Sheath Blight, Sigatoka",
        "target_part": "Leaves & Canopy",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "1.0 ml/L (200 ml/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Punjab", "Haryana", "Karnataka"]
    },
    {
        "name": "Tricyclazole 75% WP",
        "category": "Fungicide",
        "type": "Melanin Biosynthesis Inhibitor (FRAC 16.1)",
        "target_diseases": "Rice Blast (Leaf, Neck and Node Blast)",
        "target_part": "Leaves & Panicles",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "0.6 g/L (120 g/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Punjab", "Chhattisgarh", "Odisha", "Andhra Pradesh"]
    },
    {
        "name": "Cartap Hydrochloride 50% SP",
        "category": "Insecticide",
        "type": "Nereistoxin Analogue",
        "target_diseases": "Stem Borer, Leaf Folder, Gall Midge",
        "target_part": "Leaves & Stem",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "1.5 - 2.0 g/L (400 g/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Tamil Nadu", "West Bengal", "Chhattisgarh"]
    },
    {
        "name": "Imidacloprid 17.8% SL",
        "category": "Insecticide",
        "type": "Neonicotinoid Systemic",
        "target_diseases": "Aphids, Whiteflies, Jassids, Leaf Hoppers, Thrips",
        "target_part": "Leaves & Canopy",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "0.3 - 0.5 ml/L (60-100 ml/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Tamil Nadu", "Haryana", "Bihar", "Odisha"]
    },
    {
        "name": "Chlorantraniliprole 18.5% SC (Coragen)",
        "category": "Insecticide",
        "type": "Ryanodine Receptor Modulator (Diamide)",
        "target_diseases": "Pod Borer, Fall Armyworm, Diamondback Moth, Stem Borer",
        "target_part": "Leaves & Fruit",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "0.3 - 0.4 ml/L (60 ml/acre)",
        "organic_status": "Synthetic Chemical",
        "cibrc_status": "APPROVED",
        "states_used": ["Tamil Nadu", "Madhya Pradesh", "Maharashtra"]
    },
    {
        "name": "Neem Oil 10000 ppm (Azadirachtin 1%)",
        "category": "Bio-Insecticide / Botanical",
        "type": "Pure Cold-Pressed Botanical Terpenoid",
        "target_diseases": "Sap-sucking thrips, Whiteflies, Leaf miners, Aphids, Mites",
        "target_part": "Leaves & Canopy",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "3.0 - 5.0 ml/L (500 ml/acre)",
        "organic_status": "100% Certified Organic (APEDA / NPOP)",
        "cibrc_status": "APPROVED_ORGANIC",
        "states_used": ["Sikkim", "Arunachal Pradesh", "Meghalaya", "Nagaland", "Mizoram", "West Bengal"]
    },
    {
        "name": "Trichoderma viride 1.5% WP",
        "category": "Bio-Fungicide / Antagonist",
        "type": "Beneficial Fungal Biocontrol Agent",
        "target_diseases": "Root Rot, Collar Rot, Damping Off, Fusarium Wilt, Sheath Blight",
        "target_part": "Root System & Soil",
        "actuator": "VALVE_DRIP_ROOT",
        "dosage": "2.5 kg/ha applied through drip irrigation or 10g/L root drench",
        "organic_status": "100% Certified Organic (APEDA / NPOP)",
        "cibrc_status": "APPROVED_ORGANIC",
        "states_used": ["Sikkim", "Nagaland", "Meghalaya", "Tamil Nadu", "Kerala", "Karnataka"]
    },
    {
        "name": "Pseudomonas fluorescens 1.0% WP",
        "category": "Bio-Bactericide & Growth Promoter",
        "type": "Beneficial Rhizobacterium (PGPR)",
        "target_diseases": "Bacterial Leaf Blight, Panama Wilt, Bacterial Canker, Seedling Blight",
        "target_part": "Root System & Foliage",
        "actuator": "VALVE_DRIP_ROOT",
        "dosage": "2.5 kg/ha in drip line or 5g/L foliar spray",
        "organic_status": "100% Certified Organic (APEDA / NPOP)",
        "cibrc_status": "APPROVED_ORGANIC",
        "states_used": ["Sikkim", "Kerala", "Tamil Nadu", "Arunachal Pradesh"]
    },
    {
        "name": "Bordeaux Mixture (1% Cu)",
        "category": "Bio-Rational Fungicide",
        "type": "Copper Sulphate + Slaked Lime (1:1:100)",
        "target_diseases": "Downy Mildew, Anthracnose, Koleroga (Arecanut rot), Phytophthora foot rot",
        "target_part": "Leaves & Stem",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "1% solution (10g CuSO4 + 10g Lime per Litre)",
        "organic_status": "Permitted in Organic Agriculture under NPOP guidelines",
        "cibrc_status": "APPROVED_ORGANIC",
        "states_used": ["Goa", "Meghalaya", "Kerala", "Karnataka"]
    },
    {
        "name": "Panchagavya Organic Formulation",
        "category": "Organic Foliar Tonic & Immunity Booster",
        "type": "Traditional 5-Cow Byproduct Ferment",
        "target_diseases": "Crop vigor boosting, viral resistance, general pest deterrent",
        "target_part": "Leaves & Canopy",
        "actuator": "DRONE_AERIAL_FOLIAR",
        "dosage": "30 ml/L (3% foliar spray)",
        "organic_status": "100% Vedic Organic Bio-Stimulant",
        "cibrc_status": "APPROVED_ORGANIC",
        "states_used": ["All 28 States (Organic Farming Belts)"]
    }
]

# ── CROPS DATABASE ─────────────────────────────────────────────────────────────
CROPS_DATA = [
    {
        "name": "Paddy (Rice)", "hindi_name": "Dhan (धान)", "root_system": "Fibrous Root System",
        "stem_type": "Hollow Herbaceous Culm", "category": "Cereal / Staple",
        "major_states": "West Bengal, Punjab, Tamil Nadu, Andhra Pradesh, Telangana, Chhattisgarh, Odisha, Assam",
        "primary_diseases": "Bacterial Leaf Blight, Rice Blast, Sheath Blight, False Smut"
    },
    {
        "name": "Wheat", "hindi_name": "Gehun (गेहूं)", "root_system": "Fibrous Root System",
        "stem_type": "Herbaceous Tillering Culm", "category": "Cereal / Rabi Staple",
        "major_states": "Uttar Pradesh, Punjab, Madhya Pradesh, Haryana, Rajasthan, Bihar",
        "primary_diseases": "Yellow Rust (Puccinia striiformis), Brown Rust, Loose Smut, Karnal Bunt"
    },
    {
        "name": "Cotton", "hindi_name": "Kapas (कपास)", "root_system": "Deep Tap Root System",
        "stem_type": "Semi-woody Branching Shrub", "category": "Fiber / Cash Crop",
        "major_states": "Gujarat, Maharashtra, Telangana, Andhra Pradesh, Punjab, Haryana, Karnataka",
        "primary_diseases": "Cotton Leaf Curl Virus (CLCuV), Bacterial Blight, Grey Mildew, Bollworm infestation"
    },
    {
        "name": "Sugarcane", "hindi_name": "Ganna (गन्ना)", "root_system": "Fibrous Adventitious Roots",
        "stem_type": "Solid Jointed Woody Culm", "category": "Sugar / Cash Crop",
        "major_states": "Uttar Pradesh, Maharashtra, Karnataka, Tamil Nadu, Bihar, Uttarakhand",
        "primary_diseases": "Red Rot (Colletotrichum falcatum), Smut, Grassy Shoot Disease, Pokkah Boeng"
    },
    {
        "name": "Chilli", "hindi_name": "Mirchi (मिर्च)", "root_system": "Tap Root System with Lateral Feeders",
        "stem_type": "Semi-woody Branching Herb", "category": "Spice / Commercial",
        "major_states": "Andhra Pradesh, Telangana, Karnataka, Madhya Pradesh, Nagaland (King Chilli)",
        "primary_diseases": "Chilli Leaf Curl Virus, Anthracnose / Dieback, Powdery Mildew, Bacterial Spot"
    },
    {
        "name": "Tea", "hindi_name": "Chai (चाय)", "root_system": "Deep Tap Root System",
        "stem_type": "Woody Perennial Shrub", "category": "Plantation / Beverage",
        "major_states": "Assam, West Bengal (Darjeeling), Tamil Nadu (Nilgiris), Kerala, Tripura",
        "primary_diseases": "Blister Blight (Exobasidium vexans), Black Rot, Red Rust (Cephaleuros), Algal Leaf"
    },
    {
        "name": "Potato", "hindi_name": "Aloo (आलू)", "root_system": "Fibrous Shallow Root System",
        "stem_type": "Herbaceous Aerial Stem + Underground Tubers", "category": "Horticulture / Tuber",
        "major_states": "Uttar Pradesh, West Bengal, Bihar, Gujarat, Punjab, Himachal Pradesh",
        "primary_diseases": "Late Blight (Phytophthora infestans), Early Blight (Alternaria solani), Black Scurf"
    },
    {
        "name": "Mustard", "hindi_name": "Sarson (सरसों)", "root_system": "Tap Root System",
        "stem_type": "Erect Branching Herbaceous Stem", "category": "Oilseed",
        "major_states": "Rajasthan, Madhya Pradesh, Haryana, Uttar Pradesh, West Bengal, Assam",
        "primary_diseases": "White Rust (Albugo candida), Alternaria Blight, Downy Mildew, Sclerotinia Rot"
    },
    {
        "name": "Cardamom", "hindi_name": "Elaichi (इलायची)", "root_system": "Rhizomatous Shallow Roots",
        "stem_type": "Pseudostem formed by Leaf Sheaths", "category": "Spices / Cash Crop",
        "major_states": "Kerala (Idukki), Sikkim (Large Cardamom), Karnataka, Nagaland",
        "primary_diseases": "Katte Disease (Mosaic Virus), Capsule Rot / Azhukal, Chenthal, Clump Rot"
    },
    {
        "name": "Turmeric", "hindi_name": "Haldi (हल्दी)", "root_system": "Rhizome & Fibrous Roots",
        "stem_type": "Underground Modified Rhizome + Foliar Leaves", "category": "Spice / Medicinal",
        "major_states": "Telangana, Andhra Pradesh, Tamil Nadu, Meghalaya (Lakadong), Mizoram",
        "primary_diseases": "Rhizome Rot (Pythium aphanidermatum), Leaf Spot (Colletotrichum), Leaf Blotch"
    },
    {
        "name": "Apple", "hindi_name": "Seb (सेब)", "root_system": "Deep Woody Tap Root & Lateral Network",
        "stem_type": "Woody Deciduous Trunk", "category": "Temperate Fruit",
        "major_states": "Himachal Pradesh, Jammu & Kashmir, Uttarakhand",
        "primary_diseases": "Apple Scab (Venturia inaequalis), Marssonina Blotch, Powdery Mildew, Canker"
    },
    {
        "name": "Soybean", "hindi_name": "Soyabean (सोयाबीन)", "root_system": "Tap Root System with N-Fixing Nodules",
        "stem_type": "Bushy Herbaceous Erect Stem", "category": "Legume / Oilseed",
        "major_states": "Madhya Pradesh, Maharashtra, Rajasthan, Karnataka",
        "primary_diseases": "Yellow Mosaic Virus, Charcoal Rot, Rhizoctonia Aerial Blight, Rust"
    }
]


class IndiaAgriDatabase:
    """Singleton-style database manager for Indian Agricultural knowledge."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self):
        """Creates tables and seeds initial data if not present."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # 1. States table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    id INTEGER PRIMARY KEY,
                    state_name TEXT UNIQUE NOT NULL,
                    zone TEXT NOT NULL,
                    is_organic_mandate INTEGER DEFAULT 0,
                    major_crops TEXT NOT NULL,
                    commonly_used_pesticides TEXT NOT NULL,
                    climate TEXT,
                    notes TEXT
                )
            """)

            # 2. Plant Structures table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS plant_structures (
                    id INTEGER PRIMARY KEY,
                    tier_name TEXT NOT NULL,
                    anatomical_parts TEXT NOT NULL,
                    primary_function TEXT NOT NULL,
                    root_types TEXT,
                    vulnerable_pathogens TEXT NOT NULL,
                    optimal_actuator TEXT NOT NULL,
                    actuator_code TEXT NOT NULL,
                    notes TEXT
                )
            """)

            # 3. Crops table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    hindi_name TEXT,
                    root_system TEXT NOT NULL,
                    stem_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    major_states TEXT NOT NULL,
                    primary_diseases TEXT NOT NULL
                )
            """)

            # 4. Pesticides table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pesticides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL,
                    target_diseases TEXT NOT NULL,
                    target_part TEXT NOT NULL,
                    actuator TEXT NOT NULL,
                    dosage TEXT NOT NULL,
                    organic_status TEXT NOT NULL,
                    cibrc_status TEXT NOT NULL,
                    states_used TEXT NOT NULL
                )
            """)

            # 5. Banned & Restricted chemicals table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS banned_chemicals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    hazard_class TEXT NOT NULL,
                    hazard_reason TEXT NOT NULL,
                    organic_alternative TEXT NOT NULL
                )
            """)

            conn.commit()

            # Seed data if empty
            cur.execute("SELECT COUNT(*) FROM states")
            if cur.fetchone()[0] == 0:
                self._seed_database(cur, conn)

    def _seed_database(self, cur: sqlite3.Cursor, conn: sqlite3.Connection):
        """Populates the database with initial records."""
        # States
        for s in STATES_DATA:
            cur.execute("""
                INSERT OR REPLACE INTO states (id, state_name, zone, is_organic_mandate, major_crops, commonly_used_pesticides, climate, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["id"], s["state"], s["zone"], s["is_organic_mandate"],
                json.dumps(s["major_crops"]), json.dumps(s["commonly_used_pesticides"]),
                s["climate"], s["notes"]
            ))

        # Plant Structures
        for ps in PLANT_STRUCTURES_DATA:
            cur.execute("""
                INSERT OR REPLACE INTO plant_structures (id, tier_name, anatomical_parts, primary_function, root_types, vulnerable_pathogens, optimal_actuator, actuator_code, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ps["id"], ps["tier_name"], ps["anatomical_parts"], ps["primary_function"],
                ps["root_types"], ps["vulnerable_pathogens"], ps["optimal_actuator"],
                ps["actuator_code"], ps["notes"]
            ))

        # Crops
        for c in CROPS_DATA:
            cur.execute("""
                INSERT OR REPLACE INTO crops (name, hindi_name, root_system, stem_type, category, major_states, primary_diseases)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                c["name"], c["hindi_name"], c["root_system"], c["stem_type"],
                c["category"], c["major_states"], c["primary_diseases"]
            ))

        # Pesticides
        for p in PESTICIDES_LIBRARY:
            cur.execute("""
                INSERT OR REPLACE INTO pesticides (name, category, type, target_diseases, target_part, actuator, dosage, organic_status, cibrc_status, states_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["name"], p["category"], p["type"], p["target_diseases"],
                p["target_part"], p["actuator"], p["dosage"], p["organic_status"],
                p["cibrc_status"], json.dumps(p["states_used"])
            ))

        # Banned chemicals
        for b in BANNED_PESTICIDES_DATA:
            cur.execute("""
                INSERT OR REPLACE INTO banned_chemicals (name, status, legal_basis, hazard_class, hazard_reason, organic_alternative)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                b["name"], b["status"], b["legal_basis"], b["hazard_class"],
                b["hazard_reason"], b["organic_alternative"]
            ))

        conn.commit()

    # ── PUBLIC QUERY METHODS ───────────────────────────────────────────────────

    def get_all_states(self) -> List[Dict[str, Any]]:
        """Returns all 28 Indian states formatted as dictionaries."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM states ORDER BY id ASC")
            rows = cur.fetchall()
            result = []
            for r in rows:
                result.append({
                    "id": r["id"],
                    "state": r["state_name"],
                    "zone": r["zone"],
                    "is_organic_mandate": bool(r["is_organic_mandate"]),
                    "major_crops": json.loads(r["major_crops"]),
                    "commonly_used_pesticides": json.loads(r["commonly_used_pesticides"]),
                    "climate": r["climate"],
                    "notes": r["notes"]
                })
            return result

    def get_state_profile(self, state_name: str) -> Optional[Dict[str, Any]]:
        """Fetches full agronomic profile for an Indian state."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM states WHERE LOWER(state_name) = LOWER(?)", (state_name.strip(),))
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "state": r["state_name"],
                "zone": r["zone"],
                "is_organic_mandate": bool(r["is_organic_mandate"]),
                "major_crops": json.loads(r["major_crops"]),
                "commonly_used_pesticides": json.loads(r["commonly_used_pesticides"]),
                "climate": r["climate"],
                "notes": r["notes"]
            }

    def get_plant_structures(self) -> List[Dict[str, Any]]:
        """Returns the 3 plant anatomical tiers and actuator mapping."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM plant_structures ORDER BY id ASC")
            return [dict(r) for r in cur.fetchall()]

    def get_all_crops(self) -> List[Dict[str, Any]]:
        """Returns all registered crop profiles."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crops ORDER BY name ASC")
            return [dict(r) for r in cur.fetchall()]

    def get_all_pesticides(self) -> List[Dict[str, Any]]:
        """Returns the pesticide library."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pesticides ORDER BY name ASC")
            rows = cur.fetchall()
            res = []
            for r in rows:
                item = dict(r)
                try:
                    item["states_used"] = json.loads(item["states_used"])
                except Exception:
                    pass
                res.append(item)
            return res

    def get_banned_chemicals(self) -> List[Dict[str, Any]]:
        """Returns banned/restricted pesticides in India."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM banned_chemicals ORDER BY id ASC")
            return [dict(r) for r in cur.fetchall()]

    def validate_pesticide_safety(self, chemical_name: str) -> Dict[str, Any]:
        """
        Validates whether a chemical is banned, restricted, or allowed in India.
        Recommends approved organic alternatives if flagged.
        """
        name_clean = chemical_name.lower().strip()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM banned_chemicals")
            banned = cur.fetchall()
            for b in banned:
                b_name = b["name"].lower()
                if b_name in name_clean or name_clean in b_name:
                    return {
                        "is_safe": False,
                        "status": b["status"],
                        "chemical": b["name"],
                        "legal_basis": b["legal_basis"],
                        "hazard_reason": b["hazard_reason"],
                        "recommended_organic_alternative": b["organic_alternative"]
                    }

            # Check allowed library
            cur.execute("SELECT * FROM pesticides WHERE LOWER(name) LIKE ?", (f"%{name_clean}%",))
            row = cur.fetchone()
            if row:
                return {
                    "is_safe": True,
                    "status": row["cibrc_status"],
                    "chemical": row["name"],
                    "category": row["category"],
                    "dosage": row["dosage"],
                    "organic_status": row["organic_status"],
                    "recommended_organic_alternative": None
                }

            return {
                "is_safe": True,
                "status": "UNRESTRICTED_CONVENTIONAL",
                "chemical": chemical_name,
                "recommended_organic_alternative": "Neem Oil 10000 ppm / Trichoderma viride"
            }

    def search_agri_knowledge(self, query: str) -> Dict[str, Any]:
        """Universal search across states, crops, diseases, and pesticides."""
        q = f"%{query.lower().strip()}%"
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Search States
            cur.execute("SELECT * FROM states WHERE LOWER(state_name) LIKE ? OR LOWER(major_crops) LIKE ?", (q, q))
            matched_states = [r["state_name"] for r in cur.fetchall()]

            # Search Crops
            cur.execute("SELECT * FROM crops WHERE LOWER(name) LIKE ? OR LOWER(hindi_name) LIKE ? OR LOWER(primary_diseases) LIKE ?", (q, q, q))
            matched_crops = [dict(r) for r in cur.fetchall()]

            # Search Pesticides
            cur.execute("SELECT * FROM pesticides WHERE LOWER(name) LIKE ? OR LOWER(target_diseases) LIKE ?", (q, q))
            matched_pesticides = [dict(r) for r in cur.fetchall()]

            # Search Banned
            cur.execute("SELECT * FROM banned_chemicals WHERE LOWER(name) LIKE ? OR LOWER(hazard_reason) LIKE ?", (q, q))
            matched_banned = [dict(r) for r in cur.fetchall()]

            return {
                "query": query,
                "states": matched_states,
                "crops": matched_crops,
                "pesticides": matched_pesticides,
                "banned_chemicals_flagged": matched_banned
            }


# Singleton instance
INDIA_AGRI_DB = IndiaAgriDatabase()
