"""
treatment_protocols.py
======================
Comprehensive Agronomic & Phytopathological Knowledge Base.
Provides structured, multi-tier intervention protocols for plant diseases:
1. Emergency Immediate Actions (0-24h)
2. Organic & Biopesticide Formulations
3. Chemical Pesticide Prescriptions (Active ingredient, CIB&RC dosage, PHI, PPE)
4. Soil & Plant Nutrition Remediation
5. Severity Assessment & Spore Weather Risk Warning
"""

import os
import json
import re
from typing import Dict, Any, List

from disease_formatter import format_disease_prediction
from agri_pesticides_db import get_crop_agronomy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CURE_FILE = os.path.join(BASE_DIR, 'data', 'cure.json')

CURE_DB = {}
if os.path.exists(CURE_FILE):
    try:
        with open(CURE_FILE, 'r', encoding='utf-8') as f:
            CURE_DB = json.load(f)
    except Exception as e:
        print(f"[!] Warning reading cure.json: {e}")

# High-fidelity curated chemical & organic treatment database for active classes
CURATED_TREATMENTS = {
    "apple_apple_scab": {
        "immediate": [
            "Prune overcrowded inner branches to enhance canopy sunlight penetration and wind aeration.",
            "Rake up and destroy fallen leaf litter to prevent ascospores from overwintering in soil.",
            "Avoid late evening overhead sprinkler irrigation; keep foliage dry overnight."
        ],
        "organic": [
            "Foliar spray of Potassium Bicarbonate (4 g/L) or diluted apple cider vinegar (15 ml/L).",
            "Spray Bio-Fungicide Bacillus subtilis or Trichoderma viride @ 5 g/L at bud burst.",
            "Neem oil (1500 ppm @ 4 ml/L) mixed with mild liquid soap emulsion."
        ],
        "chemical": [
            {
                "name": "Mancozeb 75% WP (Dithane M-45)",
                "type": "Protectant Contact Fungicide",
                "dosage": "2.5 g / Liter of water",
                "application": "Complete foliar coverage beginning at green tip stage",
                "interval": "Every 10-12 days during wet periods",
                "phi_days": "14 days",
                "ppe": "Chemical-resistant nitrile gloves, safety goggles, N95 dust respirator"
            },
            {
                "name": "Captan 50% WP",
                "type": "Broad-Spectrum Protectant",
                "dosage": "2.0 g / Liter of water",
                "application": "Foliar misting at early pink bud stage",
                "interval": "7-10 days interval",
                "phi_days": "7 days",
                "ppe": "Full apron, protective eyewear, long sleeves"
            }
        ],
        "nutrition": [
            "Apply foliar spray of Urea (0.5%) post-harvest to accelerate leaf litter breakdown.",
            "Supplement with Calcium Nitrate (1.5%) to strengthen fruit and leaf epidermal cell walls."
        ],
        "yield_loss_risk": "Up to 50-70% reduction in marketable fruit yield due to severe scabbing and fruit deformation."
    },
    "apple_black_rot": {
        "immediate": [
            "Prune out dead wood, cankered twigs, and mummified shriveled apples hanging on the tree.",
            "Disinfect pruning secateurs in 70% alcohol between cuts.",
            "Sterilize wound cut ends with Bordeaux paste (1:1:10)."
        ],
        "organic": [
            "Spray Copper-based Bordeaux mixture (1%) at dormant winter stage.",
            "Bio-agent Ampelomyces quisqualis or Trichoderma harzianum foliar application @ 5 g/L."
        ],
        "chemical": [
            {
                "name": "Ziram 27% SC",
                "type": "Protective Dithiocarbamate Fungicide",
                "dosage": "3.0 ml / Liter of water",
                "application": "Spray foliage and fruit clusters thoroughly before rain events",
                "interval": "10-14 days",
                "phi_days": "14 days",
                "ppe": "Respirator mask, face shield, rubber gloves"
            },
            {
                "name": "Tebuconazole 25.9% EC",
                "type": "Systemic Triazole Fungicide",
                "dosage": "1.0 ml / Liter of water",
                "application": "Translaminar spray when leaf spots first appear",
                "interval": "14 days",
                "phi_days": "10 days",
                "ppe": "Protective clothing, gloves"
            }
        ],
        "nutrition": [
            "Maintain balanced Potassium (K) to improve disease resistance against rot pathogens.",
            "Avoid excessive late-season nitrogen which promotes tender, susceptible succulent shoots."
        ],
        "yield_loss_risk": "Can cause 30-60% fruit loss and limb dieback if wood cankers are unmanaged."
    },
    "apple_cedar_apple_rust": {
        "immediate": [
            "Inspect perimeter and remove any alternate host wild red cedars/junipers within 500 meters if possible.",
            "Prune rust galls from nearby juniper trees in late winter before spring spore discharge.",
            "Collect and burn fallen orange-gelatinous rust leaves."
        ],
        "organic": [
            "Foliar spray of Wettable Sulfur 80% WP @ 3 g/L from pink bud until petal fall.",
            "Neem-based botanical fungicide (Azadirachtin 0.15% @ 3 ml/L)."
        ],
        "chemical": [
            {
                "name": "Myclobutanil 10% WP",
                "type": "Systemic Demethylation Inhibitor (DMI)",
                "dosage": "1.0 - 1.5 g / Liter of water",
                "application": "Foliar spray when blossom flower buds first emerge",
                "interval": "Apply 3 times at 10-day intervals",
                "phi_days": "14 days",
                "ppe": "Goggles, protective rubber gloves, mask"
            }
        ],
        "nutrition": [
            "Apply balanced NPK with micronutrient blend (Zinc, Boron) to accelerate defoliation recovery."
        ],
        "yield_loss_risk": "Premature tree defoliation, weakened fruiting buds, and unmarketable blemished apples."
    },
    "potato_early_blight": {
        "immediate": [
            "Remove and safely burn lower infected leaves showing concentric 'target-board' brown rings.",
            "Transition to drip irrigation; eliminate overhead sprinkler watering to keep foliage dry.",
            "Ensure wide spacing (60x20 cm) for maximum canopy airflow."
        ],
        "organic": [
            "Spray Copper Oxychloride 50% WP (3.0 g/L) or Bordeaux mixture 1%.",
            "Foliar bio-formulation of Trichoderma viride (5 g/L) enriched with fermented cow urine.",
            "Foliar spray of 5% Neem Seed Kernel Extract (NSKE)."
        ],
        "chemical": [
            {
                "name": "Mancozeb 75% WP",
                "type": "Protective Contact Fungicide",
                "dosage": "2.5 g / Liter of water",
                "application": "Thorough foliar spray at the earliest detection of concentric lesions",
                "interval": "7-10 days interval during humid conditions",
                "phi_days": "7 days",
                "ppe": "Rubber gloves, protective glasses, mask"
            },
            {
                "name": "Chlorothalonil 75% WP (Kavach)",
                "type": "Multi-Site Inhibitor Fungicide",
                "dosage": "2.0 g / Liter of water",
                "application": "Even foliar coverage across both leaf surfaces",
                "interval": "10 days",
                "phi_days": "7 days",
                "ppe": "Full apron, chemical-resistant gloves"
            }
        ],
        "nutrition": [
            "Apply Muriate of Potash (MOP) to boost tuber resistance and leaf tissue firmness.",
            "Avoid nitrogen stress; nitrogen deficiency strongly predisposes potatoes to Early Blight."
        ],
        "yield_loss_risk": "Reduces tuber size and overall harvest yield by 20-40% if defoliation occurs before tuber bulking."
    },
    "potato_late_blight": {
        "immediate": [
            "CRITICAL ALERT: Phytophthora late blight spreads rapidly! Immediately destroy heavily infested cull piles.",
            "Stop irrigation immediately to lower soil and canopy humidity.",
            "Hilling up soil around potato ridges prevents down-washed zoospores from reaching tubers."
        ],
        "organic": [
            "Preventative Copper Sulfate spray (Bordeaux Mixture 1:1:100).",
            "Apply bio-control agent Pseudomonas fluorescens (5 g/L) at vegetative emergence."
        ],
        "chemical": [
            {
                "name": "Metalaxyl 8% + Mancozeb 64% WP (Ridomil Gold)",
                "type": "Systemic + Contact Combination Fungicide",
                "dosage": "2.0 g / Liter of water",
                "application": "Spray immediately upon cloudy, humid weather forecasting",
                "interval": "7-10 days during epidemic alerts",
                "phi_days": "14 days",
                "ppe": "Chemical splash goggles, respirator, gloves"
            },
            {
                "name": "Cymoxanil 8% + Mancozeb 64% WP (Curzate)",
                "type": "Curative & Protective Translaminar Fungicide",
                "dosage": "2.0 - 2.5 g / Liter of water",
                "application": "Apply within 48 hours of infection onset to halt lesions",
                "interval": "7 days",
                "phi_days": "10 days",
                "ppe": "Complete PPE gear"
            }
        ],
        "nutrition": [
            "Spray Potassium Phosphite (3 ml/L) to induce Systemic Acquired Resistance (SAR) in foliage.",
            "Apply soluble Silica foliar feed to strengthen cellular epidermal barriers."
        ],
        "yield_loss_risk": "Devastating: can cause 80-100% total crop destruction within 7-10 days under cool, foggy conditions."
    },
    "tomato_early_blight": {
        "immediate": [
            "Prune all leaves within 12 inches of the soil to prevent soil-splash spore inoculation.",
            "Mulch the soil bed with clean straw or black plastic mulch to create a physical barrier.",
            "Stake or cage indeterminate tomato plants for upright vertical growth and aeration."
        ],
        "organic": [
            "Spray cold-pressed Neem Oil (1500 ppm @ 4 ml/L) emulsified with mild soap.",
            "Foliar spray of Potassium Bicarbonate (4 g/L) + compost tea.",
            "Bio-fungicide Trichoderma harzianum or Bacillus amyloliquefaciens @ 5 g/L."
        ],
        "chemical": [
            {
                "name": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC (Amistar Top)",
                "type": "Broad-Spectrum Systemic Fungicide",
                "dosage": "1.0 ml / Liter of water",
                "application": "Fine canopy misting ensuring undersides of leaves are covered",
                "interval": "10-14 days",
                "phi_days": "5 days",
                "ppe": "Nitrile gloves, safety mask, eyewear"
            },
            {
                "name": "Mancozeb 75% WP",
                "type": "Protectant Fungicide",
                "dosage": "2.5 g / Liter of water",
                "application": "Preventative spray before rainy spells",
                "interval": "7-10 days",
                "phi_days": "7 days",
                "ppe": "Protective gloves and mask"
            }
        ],
        "nutrition": [
            "Foliar application of Calcium Nitrate (2 g/L) to prevent blossom end rot and strengthen leaf tissue.",
            "Maintain optimal soil pH (6.2 - 6.8) and supply micronutrient Zinc and Boron."
        ],
        "yield_loss_risk": "Reduces photosynthetic capacity, causing sunscald on exposed fruit and 30-50% yield loss."
    },
    "tomato_late_blight": {
        "immediate": [
            "Isolate infected field section; rogue out and bag collapsing blighted vines immediately.",
            "Cease all sprinkler/overhead watering; switch strictly to drip irrigation.",
            "Ensure wide spacing and sanitize garden tools with bleach or alcohol."
        ],
        "organic": [
            "Bordeaux Mixture (1:1:100) preventative spray.",
            "Bio-agent Pseudomonas fluorescens @ 5 g/L sprayed every 7 days."
        ],
        "chemical": [
            {
                "name": "Dimethomorph 50% WP (Acrobat)",
                "type": "Systemic Oomyceticide",
                "dosage": "1.0 g / Liter of water",
                "application": "Foliar mist covering stems and developing green tomatoes",
                "interval": "7-10 days",
                "phi_days": "5 days",
                "ppe": "Full protective clothing, gloves, mask"
            },
            {
                "name": "Fenamidone 10% + Mancozeb 50% WG (Sectin)",
                "type": "Contact and Translaminar Fungicide",
                "dosage": "2.5 g / Liter of water",
                "application": "Spray when dark water-soaked patches appear",
                "interval": "7 days",
                "phi_days": "7 days",
                "ppe": "Chemical gloves, mask"
            }
        ],
        "nutrition": [
            "Apply Potassium Schoenite (K2SO4 + MgSO4) to bolster vegetative immune response.",
            "Avoid high nitrogen fertilizers."
        ],
        "yield_loss_risk": "Rapid complete defoliation and fruit rotting; up to 90% harvest loss in cool, wet weather."
    },
    "tomato_bacterial_spot": {
        "immediate": [
            "Never work in tomato field or harvest fruit while foliage is wet.",
            "Sterilize all trellis posts, stakes, and tomato cages with 10% bleach solution.",
            "Eliminate solanaceous weeds (nightshade, datura) which harbor Xanthomonas bacteria."
        ],
        "organic": [
            "Copper Sulfate (Bordeaux mixture 1%) or Copper Hydroxide (2 g/L).",
            "Spray bactericide Bacillus amyloliquefaciens @ 5 g/L.",
            "Soak seeds in 50°C hot water for 25 minutes prior to sowing to eradicate seed-borne bacteria."
        ],
        "chemical": [
            {
                "name": "Copper Oxychloride 50% WP + Streptocycline (90:10)",
                "type": "Bactericide + Contact Protectant",
                "dosage": "Copper Oxychloride 2.5 g/L + Streptocycline 1.0 g per 10 Liters",
                "application": "Foliar spray when water-soaked pinhead spots first appear",
                "interval": "7-10 days interval during humid weather",
                "phi_days": "7 days",
                "ppe": "Nitrile gloves, protective glasses, dust mask"
            }
        ],
        "nutrition": [
            "Foliar calcium spray to firm up tomato cell walls against bacterial pectolytic enzymes."
        ],
        "yield_loss_risk": "Severe defoliation, blossom drop, and unmarketable scabby fruit; 30-50% loss."
    },
    "tomato_yellow_leaf_curl_virus": {
        "immediate": [
            "Install yellow sticky traps (15-20 traps per acre) to monitor and trap vector Whiteflies (Bemisia tabaci).",
            "Rogue out and destroy curled, stunted plants immediately inside sealed plastic bags.",
            "Plant barrier crops (2-3 rows of maize, sorghum, or pearl millet) around tomato field perimeter."
        ],
        "organic": [
            "Foliar spray of 5% Neem Seed Kernel Extract (NSKE) or Neem Oil 10,000 ppm (2 ml/L).",
            "Spray entomopathogenic fungus Beauveria bassiana or Verticillium lecanii (5 g/L) against whiteflies.",
            "Install 40-50 mesh insect-proof netting in nursery beds."
        ],
        "chemical": [
            {
                "name": "Diafenthiuron 50% WP (Pegasus)",
                "type": "Selective Insecticide / Miticide",
                "dosage": "1.2 g / Liter of water",
                "application": "Target whitefly adults and nymphs feeding on leaf undersides",
                "interval": "10-12 days",
                "phi_days": "7 days",
                "ppe": "Face mask, gloves, protective apron"
            },
            {
                "name": "Acetamiprid 20% SP",
                "type": "Systemic Neonicotinoid",
                "dosage": "0.3 g / Liter of water",
                "application": "Spray at first appearance of whitefly clusters",
                "interval": "14 days",
                "phi_days": "5 days",
                "ppe": "Protective gear"
            }
        ],
        "nutrition": [
            "Foliar spray of micro-nutrients (Zinc Sulphate 0.5% + Borax 0.2%) to alleviate chlorotic curling stress."
        ],
        "yield_loss_risk": "Devastating; near 100% crop loss if infection strikes plants in early vegetative/flowering stage."
    },
    "grape_black_rot": {
        "immediate": [
            "Prune out mummified shriveled grape bunches left on vines from the previous harvest.",
            "Maintain trellis canopy training for maximum solar exposure and rapid drying of morning dew.",
            "Cultivate soil under vines to bury overwintered infected berry debris."
        ],
        "organic": [
            "Bordeaux mixture 1% preventative sprays beginning at 2-3 inch shoot growth.",
            "Sulfur-based fungicides or bio-fungicide Bacillus pumilus @ 4 g/L."
        ],
        "chemical": [
            {
                "name": "Mancozeb 75% WP",
                "type": "Contact Protectant Fungicide",
                "dosage": "2.5 g / Liter of water",
                "application": "Spray from early shoot growth until 4-5 weeks post-bloom",
                "interval": "10-14 days",
                "phi_days": "21 days",
                "ppe": "Gloves, respirator, eye goggles"
            },
            {
                "name": "Kresoxim-methyl 44.3% SC",
                "type": "Strobilurin Translaminar Fungicide",
                "dosage": "0.7 ml / Liter of water",
                "application": "Pre-bloom and post-bloom berry cluster spray",
                "interval": "12-14 days",
                "phi_days": "14 days",
                "ppe": "Complete PPE gear"
            }
        ],
        "nutrition": [
            "Foliar spray of Potassium Sulphate (1.0%) to enhance berry skin elasticity and disease resistance."
        ],
        "yield_loss_risk": "Can destroy 50-80% of the entire grape bunch yield under hot, humid summer conditions."
    },
    "corn_common_rust": {
        "immediate": [
            "Monitor lower leaves around tassel/silk emergence for cinnamon-brown pustules.",
            "Plow under or chop corn stover residue post-harvest to reduce local inoculum.",
            "Avoid late planting to escape seasonal peak rust spore migrations."
        ],
        "organic": [
            "Foliar spray of wettable sulfur (3 g/L) or neem oil (3 ml/L).",
            "Biological foliar agent Trichoderma harzianum (5 g/L)."
        ],
        "chemical": [
            {
                "name": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "type": "Broad-Spectrum Systemic Fungicide",
                "dosage": "1.0 ml / Liter of water",
                "application": "Spray when pustules appear on upper canopy leaves near silking stage",
                "interval": "14 days",
                "phi_days": "14 days",
                "ppe": "Standard applicator protective gear"
            },
            {
                "name": "Mancozeb 75% WP",
                "type": "Contact Protectant",
                "dosage": "2.5 g / Liter of water",
                "application": "Early vegetative spray",
                "interval": "10-12 days",
                "phi_days": "14 days",
                "ppe": "Gloves, mask"
            }
        ],
        "nutrition": [
            "Maintain balanced Potash and Phosphorus; avoid excessive nitrogen."
        ],
        "yield_loss_risk": "Causes 15-30% loss of grain weight and stalk lodging in susceptible varieties."
    },
    "orange_citrus_greening": {
        "immediate": [
            "CRITICAL BACTERIAL VASCULAR DISEASE: Rogue out and destroy trees with severe asymmetrical blotchy mottle.",
            "Target and eradicate Asian Citrus Psyllid (Diaphorina citri) insect vectors immediately.",
            "Use only certified disease-free rootstock and budwood from accredited nurseries."
        ],
        "organic": [
            "Foliar spray of Horticultural Mineral Oil (1.5%) + Neem oil (5 ml/L) to deter psyllid egg laying.",
            "Introduce parasitoid wasp Tamarixia radiata as biological psyllid predator.",
            "Apply root drench of Trichoderma viride and mycorrhizal fungi."
        ],
        "chemical": [
            {
                "name": "Imidacloprid 17.8% SL",
                "type": "Systemic Insecticide (Psyllid Vector Control)",
                "dosage": "0.5 ml / Liter of water",
                "application": "Foliar spray at vegetative flush when psyllids reproduce",
                "interval": "21 days minimum retreatment interval",
                "phi_days": "15 days",
                "ppe": "Chemical gloves, eye goggles, mask"
            },
            {
                "name": "Streptocycline + Copper Oxychloride",
                "type": "Bactericidal Flush Protection",
                "dosage": "1 g Streptocycline per 10 L + 2.5 g/L Copper Oxychloride",
                "application": "Foliar spray on tender shoots",
                "interval": "15-20 days",
                "phi_days": "20 days",
                "ppe": "Full apron, gloves, goggles"
            }
        ],
        "nutrition": [
            "Intensive micronutrient cocktail: foliar spray Zinc Sulphate (0.5%), Manganese Sulphate (0.5%), Iron Chelate (0.2%), and Boron (0.1%) to maintain tree vigor and unclog phloem vascular bundles."
        ],
        "yield_loss_risk": "Permanent tree decline, unpalatable bitter lopsided fruit, and total orchard mortality over 3-5 years."
    }
}


def build_generic_protocol(crop: str, disease: str, pathogen_type: str, is_healthy: bool) -> Dict[str, Any]:
    """Generates a high-quality agronomic protocol for any plant pathology."""
    if is_healthy:
        return {
            "immediate": [
                "Continue standard agricultural crop maintenance and regular weed control.",
                "Ensure routine scout inspections twice a week for early signs of foliar stress.",
                "Maintain optimal drip or furrow irrigation schedule based on soil moisture."
            ],
            "organic": [
                "Apply prophylactic neem oil spray (3 ml/L) or botanical leaf extracts once a month.",
                "Incorporate compost or vermicompost (2-3 tonnes/acre) into soil to boost microflora.",
                "Drench soil with Trichoderma viride (2.5 kg/ha) to prevent root pathogens."
            ],
            "chemical": [
                {
                    "name": "No chemical fungicide required",
                    "type": "Healthy Crop Baseline",
                    "dosage": "0 ml/L",
                    "application": "N/A - Plant is in excellent physiological vigor",
                    "interval": "N/A",
                    "phi_days": "0 days",
                    "ppe": "Standard garden/farm wear"
                }
            ],
            "nutrition": [
                "Apply balanced NPK fertilizer according to standard regional crop dosage schedule.",
                "Ensure adequate micronutrient balance (Zinc, Iron, Manganese) during flowering."
            ],
            "yield_loss_risk": "0% Risk - Crop displays robust vigor and optimal leaf area index."
        }

    # Diseased fallback based on pathogen type
    if pathogen_type == "Bacterial":
        return {
            "immediate": [
                "Immediately sanitize pruning shears and tools in 70% ethanol or 10% bleach solution.",
                "Avoid working in or harvesting the field while leaves are damp with dew or rain.",
                "Prune out water-soaked stems and destroy debris away from agricultural fields."
            ],
            "organic": [
                "Foliar spray of Copper Hydroxide (2.0 g/L) or Bordeaux Mixture 1%.",
                "Apply biocontrol agent Bacillus amyloliquefaciens or Pseudomonas fluorescens @ 5 g/L.",
                "Seed or seedling treatment with hot water (50°C for 25 min) or biocontrol slurry."
            ],
            "chemical": [
                {
                    "name": "Copper Oxychloride 50% WP + Streptocycline",
                    "type": "Bactericide + Protective Fungicide",
                    "dosage": "Copper Oxychloride 2.5 g/L + Streptocycline 1.0 g / 10 Liters water",
                    "application": "Foliar mist covering both upper and lower leaf surfaces",
                    "interval": "7-10 days interval during humid weather",
                    "phi_days": "7 days",
                    "ppe": "Chemical gloves, safety goggles, mask"
                }
            ],
            "nutrition": [
                "Foliar spray of Calcium Nitrate (1.5 g/L) to strengthen plant cell walls against bacterial pectolytic enzymes.",
                "Avoid high nitrogen fertilizers that produce tender, vulnerable succulent tissue."
            ],
            "yield_loss_risk": "Moderate to High: 25-45% yield decline if bacterial blight spreads across vegetative canopy."
        }
    elif pathogen_type == "Viral":
        return {
            "immediate": [
                "Rogue out and destroy curled, stunted, and mosaic-mottled plants immediately in sealed bags.",
                "Install yellow and blue sticky traps (15-20 per acre) to control vector whiteflies, thrips, and aphids.",
                "Eradicate alternate weed hosts (Parthenium, Sida, Datura) along field borders."
            ],
            "organic": [
                "Foliar spray of 5% Neem Seed Kernel Extract (NSKE) or Neem Oil 1500 ppm @ 4 ml/L.",
                "Spray entomopathogenic fungus Beauveria bassiana (5 g/L) to suppress insect vectors.",
                "Apply sour buttermilk spray (20 ml/L) mixed with water as a traditional antiviral stimulant."
            ],
            "chemical": [
                {
                    "name": "Acetamiprid 20% SP / Dinotefuran 20% SG",
                    "type": "Systemic Vector-Targeted Insecticide",
                    "dosage": "Acetamiprid 0.3 g/L or Dinotefuran 0.4 g/L",
                    "application": "Target underside of leaves where insect vectors feed and reproduce",
                    "interval": "10-14 days",
                    "phi_days": "7 days",
                    "ppe": "Respirator, chemical-resistant gloves, apron"
                }
            ],
            "nutrition": [
                "Apply foliar micronutrient blend (Zinc Sulphate 0.5% + Ferrous Sulphate 0.5% + Borax 0.2%) to support recovery.",
                "Supply Potassium Schoenite to restore metabolic balance."
            ],
            "yield_loss_risk": "Severe: 40-80% harvest loss; viruses induce sterility and stunting if uncontained."
        }
    elif pathogen_type == "Pest / Insect":
        return {
            "immediate": [
                "Physically inspect under-leaf surfaces and hand-pick caterpillars/clusters if small infestation.",
                "Install pheromone traps (5-8 per acre) and light traps to disrupt mating cycles.",
                "Spray strong water jet to dislodge spider mites and aphid colonies."
            ],
            "organic": [
                "Foliar spray of cold-pressed Neem Oil (1500 ppm @ 5 ml/L) with liquid soap.",
                "Spray Bacillus thuringiensis (Bt @ 2 g/L) for caterpillar pests.",
                "Release biocontrol predatory mites or ladybird beetles."
            ],
            "chemical": [
                {
                    "name": "Chlorantraniliprole 18.5% SC (Coragen) / Spiromesifen 22.9% SC",
                    "type": "Selective Crop Insecticide / Acaricide",
                    "dosage": "0.3 ml/L for chewing caterpillars; 1.0 ml/L for mites",
                    "application": "Foliar mist covering flower buds and new foliage",
                    "interval": "14 days",
                    "phi_days": "5 days",
                    "ppe": "Gloves, eye protection, face shield"
                }
            ],
            "nutrition": [
                "Foliar silica and potassium application to toughen leaf cuticular armor against piercing mouthparts."
            ],
            "yield_loss_risk": "Variable: 20-50% foliar damage resulting in stunted fruit size."
        }
    else:  # Fungal default
        return {
            "immediate": [
                "Prune and safely burn infected leaves displaying spots, powdery mildew, or rust pustules.",
                "Eliminate overhead sprinkler watering; switch strictly to ground-level or drip irrigation.",
                "Increase plant row spacing to optimize canopy air circulation and rapid dew evaporation."
            ],
            "organic": [
                "Foliar spray of Potassium Bicarbonate (4 g/L) or Baking Soda (Sodium Bicarbonate 5 g/L).",
                "Spray Bio-Fungicide Trichoderma viride or Bacillus subtilis @ 5-10 g/L.",
                "Neem Oil (1500 ppm @ 4 ml/L) mixed with mild liquid soap emulsion."
            ],
            "chemical": [
                {
                    "name": "Mancozeb 75% WP (Contact) or Azoxystrobin + Difenoconazole (Systemic)",
                    "type": "Broad-Spectrum Foliar Fungicide",
                    "dosage": "Mancozeb 2.5 g/L or Azoxystrobin 1.0 ml/L",
                    "application": "Uniform foliar spray covering upper and lower leaf surfaces",
                    "interval": "10-12 days during humid/rainy periods",
                    "phi_days": "7-14 days",
                    "ppe": "Protective gloves, goggles, dust respirator"
                }
            ],
            "nutrition": [
                "Avoid high nitrogen fertilizers that cause soft leaf growth favored by fungal mycelia.",
                "Apply Potassium and Soluble Silicon to fortify epidermal cell walls against fungal appressorial penetration."
            ],
            "yield_loss_risk": "Estimated 25-50% yield reduction due to premature defoliation and chlorosis."
        }


# --- LONG-TERM DISEASE PREVENTION ROADMAPS (IPM) ---
PREVENTION_ROADMAPS = {
    "Fungal": [
        "Follow a 2-3 year crop rotation with non-host cereals (wheat, maize, bajra) to break the soil-borne inoculum cycle.",
        "Sow certified disease-free, fungicide-treated seed (Carbendazim 2 g + Thiram 2 g per kg seed).",
        "Select resistant / tolerant hybrids released by ICAR and State Agricultural Universities.",
        "Maintain wider row spacing (≥ 60 cm) and prune lower foliage for canopy aeration and rapid dew drying.",
        "Switch to drip / furrow irrigation only; never wet the leaf canopy, and irrigate in the morning.",
        "Adopt sanitation hygiene: remove and burn volunteer seedlings, infected debris and weed hosts every week.",
        "Apply protective bio-fungicide (Trichoderma viride 2.5 kg/ha soil drench + Bacillus subtilis foliar) on a 15-day calendar schedule.",
        "Destroy alternate / wild host plants of the pathogen within 5 m of the field bunds."
    ],
    "Bacterial": [
        "Use pathogen-free certified seed and hot-water seed treatment (50°C for 25-30 minutes) before sowing.",
        "Rotate with non-solanaceous / non-host crops (grains, maize) for at least 2 seasons in affected plots.",
        "Avoid overhead sprinklers and never work the field when foliage is wet to stop bacterial smearing.",
        "Sanitize pruning knives, shears and hands between plants with 70% alcohol or 5% sodium hypochlorite.",
        "Incorporate copper hydroxide / Bordeaux preventive sprays at the first sign of water-soaked lesions.",
        "Control insect wounds and spreading vectors (leafhoppers, beetles) that inject bacteria into stems.",
        "Raise transplants in sterile soilless media and drench with Pseudomonas fluorescens before transplanting."
    ],
    "Viral": [
        "Plant only virus-tested planting material and resistant cultivars certified by ICAR / NBPGR.",
        "Raise seedlings under 40-mesh insect-proof nylon nets to exclude whiteflies, aphids and thrips.",
        "Install yellow sticky traps (10-12/acre) + blue sticky traps (4-6/acre) from the day of transplanting.",
        "Deploy barrier / trap crops of maize, sorghum or marigold around field borders to block vector flights.",
        "Rogue out and bag symptomatic plants within 48 hours - a single curled plant can seed a whole field.",
        "Spray preventive vector control (Neem NSKE 5% weekly; Acetamiprid need-based) since viruses have no cure.",
        "Remove Parthenium, Datura and Sida weeds that shelter viruliferous vectors between crops.",
        "Disinfect hands and tools with 20% milk solution when handling/marking plants (mechanical transmission)."
    ],
    "Pest / Insect": [
        "Install pheromone traps (5-8/acre) and nutrient traps to monitor and disrupt male insect mating flights.",
        "Run light traps (1 per acre) at 15-20 nights during the active moth flight season.",
        "Conserve natural enemies: release Trichogramma cards (2/acre) for egg parasitism and ladybird beetles for aphids.",
        "Follow the Economic Threshold Level (ETL) - spray only when crossing pest-specific thresholds, not on a fixed calendar.",
        "Rotate insecticide chemistry classes (IRAC groups) each generation to prevent resistance build-up.",
        "Deep summer plowing to expose pupae and root-dwelling larvae to birds and solar heat.",
        "Hand-pick and destroy egg masses and gregarious early-instar larvae from foliage weekly."
    ],
    "Healthy": [
        "Continue preventive schedule: weekly field scouting along diagonals (W-pattern) for early symptom detection.",
        "Maintain balanced nutrition as per soil health card; avoid nitrogen excess that invites pathogens.",
        "Apply monthly prophylactic neem oil (3 ml/L) or mycorrhizal / Trichoderma soil drenches.",
        "Keep irrigation uniform and ensure good drainage to prevent root-zone anaerobiosis.",
        "Seed treatment with bio-agents remains the cheapest insurance for the next crop cycle."
    ]
}


# --- DISEASE SYMPTOM / PATHOLOGY DESCRIPTIONS ---
SYMPTOM_PROFILES = {
    "Fungal": "Typical signs: powdery/downy growth, target-like concentric spots, rust pustules, dark lesions with yellow halos and premature leaf drop. The pathogen spreads via wind-borne spores that germinate on free moisture (dew >10 hrs, rain splash) and moderate temperatures of 18-28°C.",
    "Bacterial": "Typical signs: water-soaked angular spots that turn brown/black, oozing from lesions in humid weather, wilt of young shoots and foul smell from rotting tissue. Bacteria enter through stomata and wounds and multiply rapidly in the intercellular spaces.",
    "Viral": "Typical signs: mosaic or yellow mottle, leaf curling and stunting, vein clearing, shoe-string petioles and reduced fruit set. Viruses are injected by sucking insects (whitefly, aphid, thrips) or by contaminated hands and tools - no chemical cure exists, only vector control.",
    "Pest / Insect": "Typical damage: shot-hole feeding, skeletonized leaves, rolled/webbed foliage, sticky honeydew with sooty mould, and visible larvae/mites on leaf undersides. Pest populations explode in warm-dry weather and damage is amplified by plant water stress.",
    "Abiotic": "Typical signs: marginal leaf scorch, interveinal chlorosis, uniform yellowing or tip burn without spreading pattern or pathogen signs. Caused by nutrient imbalance, pH lock-out, moisture extremes or temperature stress rather than an infectious agent.",
    "Healthy": "Excellent baseline condition: deep green lamina, intact cuticle, turgid leaves with high chlorophyll index and no necrotic, sporulating or chlorotic regions detected in the image telemetry."
}


# --- PESTICIDE SAFETY & HANDLING GUIDELINES ---
SAFETY_GUIDELINES = [
    "Read the label twice; measure with the dedicated cup - never freehand pour.",
    "Calibrate knapsack: 80-100 L spray suspension per acre (20-25 L/ha tank basis) at 15-20 PSI.",
    "Mix in a well-ventiated area; never eat, drink or smoke while handling concentrates.",
    "Spray early morning or late evening, below 32°C and wind under 10 km/h to stop drift.",
    "Observe the Pre-Harvest Interval (PHI) strictly before picking the crop for market.",
    "Triple-rinse empty packets into the tank; do not burn or dump containers in field bunds or canals.",
    "Store concentrates away from children, food grains and cattle feed in original labelled packs.",
    "Shower and change clothes after spraying; if poisoned, take the label to the nearest hospital.",
    "Do not re-enter sprayed fields until sprays have dried (usually 24 hours re-entry interval)."
]


RESISTANCE_MANAGEMENT = [
    "Alternate fungicides from different FRAC code groups (e.g. Mancozeb → Tebuconazole → Azoxystrobin) - never repeat the same chemistry more than twice a season.",
    "Use protectant contact fungicides as tank-mix partners with systemic actives to dilute resistance selection pressure.",
    "Apply the full labelled dose - sub-lethal doses accelerate resistant strain evolution.",
    "Blend chemical tactics with biologicals (Bacillus subtilis, Trichoderma) and cultural methods into true IPM."
]


def _parse_dosage_amount(dosage_str: str):
    """Extract numeric dose and unit from strings like '2.5 g / Liter of water' or '1.0 - 1.5 g / L'."""
    if not dosage_str:
        return None, "g"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(g|ml|gm|mL|G|ML)", dosage_str)
    if m:
        val = float(m.group(1))
        unit = "ml" if m.group(2).lower().startswith("m") else "g"
        return val, unit
    return None, "g"


def compute_field_quantities(chemical_list: List[Dict[str, Any]],
                            spray_liters_per_acre: float = 100.0) -> List[Dict[str, str]]:
    """
    Converts per-liter lab dosages into ready farm-level quantities:
    how much product to weigh for a full acre spray tank / 100 L suspension.
    """
    quantities = []
    for chem in chemical_list:
        name = chem.get("name", "")
        dosage = chem.get("dosage", "")
        if "No chemical" in name or dosage.strip() in ("0 ml/L", "", "N/A"):
            quantities.append({
                "pesticide": name,
                "per_acre_product": "Not required - preventive spray only",
                "tank_mix_basis": f"No pesticide needed for a healthy specimen",
                "active_ingredient": chem.get("type", "Bio / prophylactic program")
            })
            continue

        dose_val, dose_unit = _parse_dosage_amount(dosage)
        if dose_val is None:
            quantities.append({
                "pesticide": name,
                "per_acre_product": "Refer to pack label",
                "tank_mix_basis": dosage,
                "active_ingredient": chem.get("type", "")
            })
            continue

        total_product = dose_val * spray_liters_per_acre
        big_unit = "ml" if dose_unit == "ml" else "g"
        if total_product >= 1000:
            shown = f"{total_product/1000:.2f} L" if big_unit == "ml" else f"{total_product/1000:.2f} kg"
        else:
            shown = f"{total_product:.0f} {big_unit}"

        quantities.append({
            "pesticide": name,
            "per_acre_product": f"{shown} per acre ({shown} in {spray_liters_per_acre:.0f} L spray tank)",
            "tank_mix_basis": f"Lab dose {dosage} → scaled to a {spray_liters_per_acre:.0f}-litre field suspension",
            "active_ingredient": chem.get("type", "")
        })
    return quantities


def get_prevention_methods(pathogen_type: str, disease_name: str) -> List[str]:
    """Return the IPM prevention roadmap matching the diagnosed pathogen category."""
    base = "Fungal"
    pt = (pathogen_type or "").lower()
    if "healthy" in pt:
        base = "Healthy"
    elif "bacteri" in pt:
        base = "Bacterial"
    elif "vir" in pt:
        base = "Viral"
    elif "pest" in pt or "insect" in pt or "mite" in pt:
        base = "Pest / Insect"
    elif "abiotic" in pt or "deficien" in pt:
        base = "Fungal"
    methods = list(PREVENTION_ROADMAPS.get(base, PREVENTION_ROADMAPS["Fungal"]))
    methods.append(f"Re-scout the field 7 days after every spray; record '{disease_name}' pressure trends to time the next intervention.")
    return methods


def get_symptom_profile(pathogen_type: str) -> str:
    pt = (pathogen_type or "").lower()
    if "bacteri" in pt:
        return SYMPTOM_PROFILES["Bacterial"]
    if "vir" in pt:
        return SYMPTOM_PROFILES["Viral"]
    if "pest" in pt or "insect" in pt or "mite" in pt:
        return SYMPTOM_PROFILES["Pest / Insect"]
    if "abiotic" in pt or "deficien" in pt:
        return SYMPTOM_PROFILES["Abiotic"]
    if "healthy" in pt:
        return SYMPTOM_PROFILES["Healthy"]
    return SYMPTOM_PROFILES["Fungal"]


def build_ppe_checklist(chemical_list: List[Dict[str, Any]]) -> List[str]:
    """Consolidated PPE checklist across all prescribed formulations."""
    checklist = {
        "gloves": "Chemical-resistant nitrile / rubber gloves",
        "goggle": "Sealed safety goggles or full face shield",
        "respirator": "N95 / half-mask respirator for WP + EC dusts and mists",
        "apron": "Rubberized or disposable chemical apron",
        "cloth": "Full-sleeve coveralls, head cap, and rubber boots",
        "mask": "Washable cloth mask over nose and mouth while mixing"
    }
    combined = " ".join((c.get("ppe", "") + " " + c.get("name", "")).lower() for c in chemical_list)
    selected = []
    for key, text in checklist.items():
        if key in combined or key in ("apron", "cloth"):
            selected.append(text)
    if not selected:
        selected = ["Nitrile gloves", "Safety goggles", "Full-sleeve clothing and mask"]
    selected.append("Keep milk / egg white and first-aid kit nearby (do NOT induce vomiting unless advised)")
    return selected



def get_comprehensive_treatment_protocol(
    raw_class_name: str,
    confidence: float = 85.0,
    thermal_metrics: Dict[str, float] = None,
    state: str = "",
    district: str = ""
) -> Dict[str, Any]:
    """
    Produces complete, structured 360-degree phytopathological analysis and treatment plan.
    """
    if thermal_metrics is None:
        thermal_metrics = {
            "cwsi_index": 0.25,
            "chlorophyll_ratio": 0.85,
            "necrosis_ratio": 0.08,
            "canopy_temp_delta": 0.8,
            "estimated_canopy_temp_c": 28.8
        }

    # 1. Pathology Formatter
    pathology = format_disease_prediction(raw_class_name, confidence)
    is_healthy = pathology["is_healthy"]
    pathogen_type = pathology["pathogen_type"]
    crop = pathology["crop"]
    disease_name = pathology["disease_name"]

    # 2. Determine Severity Tier & Foliar Area Damage
    necrosis = float(thermal_metrics.get("necrosis_ratio", 0.08))
    cwsi = float(thermal_metrics.get("cwsi_index", 0.25))
    
    if is_healthy:
        severity_tier = "Healthy Specimen (Optimal Foliar Vigor)"
        severity_badge = "badge-healthy"
        severity_color = "#2e7d32"
        estimated_damage_pct = round(necrosis * 100 * 0.3, 1)
        action_urgency = "Routine Monitoring"
    elif necrosis < 0.12 and cwsi < 0.35:
        severity_tier = "Mild / Early Stage Infection (1 - 15% leaf area)"
        severity_badge = "badge-mild"
        severity_color = "#fbc02d"
        estimated_damage_pct = round(max(3.5, necrosis * 100 * 1.2), 1)
        action_urgency = "Preventative Action Within 48 Hours"
    elif necrosis < 0.30 or cwsi < 0.65:
        severity_tier = "Moderate Stage Infection (15 - 40% leaf area)"
        severity_badge = "badge-moderate"
        severity_color = "#f57c00"
        estimated_damage_pct = round(min(39.5, max(16.0, necrosis * 100 * 1.8)), 1)
        action_urgency = "Immediate Therapeutic Action (24-48 Hours)"
    else:
        severity_tier = "Severe / Advanced Infection (> 40% leaf area)"
        severity_badge = "badge-severe"
        severity_color = "#d32f2f"
        estimated_damage_pct = round(min(85.0, max(42.0, necrosis * 100 * 2.2)), 1)
        action_urgency = "Critical Emergency Intervention (0-24 Hours)"

    # 3. Retrieve Curated Protocol or fallback
    class_key = raw_class_name.lower().replace("___", "_").replace("__", "_").replace(" ", "_")
    # Clean matches
    matched_key = None
    for k in CURATED_TREATMENTS.keys():
        if k in class_key or class_key in k:
            matched_key = k
            break

    if matched_key and not is_healthy:
        curated = CURATED_TREATMENTS[matched_key]
        immediate = curated["immediate"]
        organic = curated["organic"]
        chemical = curated["chemical"]
        nutrition = curated["nutrition"]
        yield_loss = curated.get("yield_loss_risk", "Estimated 25-45% yield reduction if untreated.")
    else:
        generic = build_generic_protocol(crop, disease_name, pathogen_type, is_healthy)
        immediate = generic["immediate"]
        organic = generic["organic"]
        chemical = generic["chemical"]
        nutrition = generic["nutrition"]
        yield_loss = generic.get("yield_loss_risk", "Variable based on timely intervention.")

    # 4. Extract rich cure description from cure.json if available
    cure_description = ""
    clean_dis = raw_class_name.lower().replace("_", " ")
    for c_key, c_val in CURE_DB.items():
        if c_key.lower() in clean_dis or clean_dis in c_key.lower():
            cure_description = c_val
            break

    # 5. Regional Spore Warning based on State & District
    loc_str = f"{district}, {state}".strip(", ").title()
    if not loc_str:
        loc_str = "Selected Region"
        
    climate_warning = f"Current microclimate conditions in {loc_str}: Monitor humidity. Fungal spores and vector insects thrive in high moisture (>70% RH)."
    if "Kerala" in state or "Coastal" in district or "Mumbai" in state:
        climate_warning = f"High Coastal Humidity in {loc_str}: Rapid sporulation risk! Apply protective fungicides prior to morning rainfall."
    elif "Punjab" in state or "Haryana" in state:
        climate_warning = f"Semi-Arid Continental Zone ({loc_str}): Monitor for hot-dry insect pest flares and ensure adequate furrow irrigation."
    elif "Himachal" in state or "Ooty" in district or "Nilgiris" in district:
        climate_warning = f"Hilly Chilly Climate ({loc_str}): Low evaporation rates. Avoid evening irrigation to prevent cold-wet foliar damping-off."

    # 6. Recovery Milestone Schedule
    recovery_schedule = [
        {"day": "Day 1", "action": "Field sanitation, isolation, and pruning of symptomatic leaves"},
        {"day": "Day 3 - 4", "action": "Primary foliar spray (Bio-fungicide or Targeted Chemical Formulation)"},
        {"day": "Day 8 - 10", "action": "Secondary inspection; respray if sporulating lesions persist"},
        {"day": "Day 14 - 16", "action": "Recovery confirmation, cellular vigor restoration, and micronutrient boost"}
    ]

    # 7. Farm-level pesticide quantity computation (per-acre spray tank maths)
    field_quantities = compute_field_quantities(chemical)

    # 8. Long-term prevention roadmap + symptom biology + safety kit
    prevention_methods = get_prevention_methods(pathogen_type, disease_name)
    symptom_description = get_symptom_profile(pathogen_type if not is_healthy else "Healthy")
    ppe_checklist = build_ppe_checklist(chemical)

    # 9. Comprehensive Crop Agronomy (Water, Irrigation, Soil)
    agronomy_profile = dict(get_crop_agronomy(crop))
    if not is_healthy:
        agronomy_profile["irrigation_disease_warning"] = (
            f"Foliar Pathogen Alert ({pathology['disease_name']}): Strictly avoid overhead sprinkler or late evening wetting! "
            f"Foliar moisture facilitates {pathogen_type.lower()} spore germination and leaf spot spread. Irrigate strictly at root zone (drip lines) early morning."
        )

    # 10. Pesticide Category & Mode of Action Guidance
    primary_chem_name = chemical[0]["name"] if chemical else "Organic Bio-Pesticide"
    pesticide_category_guidance = {
        "recommended_category": "Fungicide (Contact & Systemic Tank Mix)" if "Fungal" in pathogen_type else ("Bactericide & Antibiotic Formulation" if "Bacterial" in pathogen_type else ("Botanical Antagonist / Bio-Insecticide" if "Viral" in pathogen_type else "Prophylactic Bio-Stimulant")),
        "mode_of_action": "Systemic translaminar absorption combined with multi-site protective barrier on leaf surface." if not is_healthy else "Zero chemical required; maintain balanced foliar nutrition and organic bio-tonics.",
        "target_pathogen": pathogen_type,
        "primary_recommendation": primary_chem_name,
        "cibrc_band": "Blue Band (Moderately Toxic) or Green Band (Organic Bio-agent)" if not is_healthy else "Green Band (Non-toxic)",
        "application_timing": "Early morning (6:30 - 9:00 AM) or late afternoon (4:30 - 6:30 PM), avoiding wind speed >10 km/h and rain within 4 hours."
    }

    return {
        "pathology": pathology,
        "severity": {
            "tier": severity_tier,
            "badge": severity_badge,
            "color": severity_color,
            "urgency": action_urgency,
            "estimated_damage_pct": estimated_damage_pct,
            "cwsi_index": round(cwsi, 3),
            "chlorophyll_ratio": round(float(thermal_metrics.get("chlorophyll_ratio", 0.85)), 3),
            "necrosis_ratio": round(necrosis, 3),
            "canopy_temp_delta": f"{thermal_metrics.get('canopy_temp_delta', 0.8):+.1f}°C"
        },
        "immediate_actions": immediate,
        "organic_solutions": organic,
        "chemical_pesticides": chemical,
        "nutrition_management": nutrition,
        "risk_forecast": {
            "yield_loss_risk": yield_loss,
            "climate_warning": climate_warning,
            "recovery_schedule": recovery_schedule
        },
        "prevention_methods": prevention_methods,
        "symptom_description": symptom_description,
        "pesticide_field_quantities": field_quantities,
        "safety_guidelines": SAFETY_GUIDELINES,
        "ppe_checklist": ppe_checklist,
        "resistance_management": RESISTANCE_MANAGEMENT,
        "scientific_cure_summary": cure_description[:450] + "..." if len(cure_description) > 450 else cure_description,
        "plant_stats": agronomy_profile,
        "pesticide_category_guidance": pesticide_category_guidance
    }

