"""
plant_image_preprocessor.py
===========================
Calibrated Computer Vision & Pathology Preprocessing Engine:
- Aspect-ratio preserving letterbox resizing
- Adaptive CLAHE local contrast normalization
- Multi-mode leaf segmentation: 'smart_adaptive' vs 'full_frame'
- Calibrated chlorophyll color-space (distinguishes natural leaf veins & glare from lesions)
- Multi-pathology spectral profiling (Necrosis, Rust, Chlorosis/Blight, Powdery Mildew, Anthracnose)
- Spatial cluster lesion detection to eliminate camera sensor noise
- Configurable sensitivity modes: 'balanced', 'high_specificity', 'early_warning'
"""

import cv2
import numpy as np
import os

# -- Calibrated Disease Spectral Profiles -------------------------------------
DISEASE_PROFILES = [
    {
        "name": "Bacterial Blight / Dark Necrosis",
        "ranges": [
            (np.array([0,   30,   0]),   np.array([180, 255,  55])),   # Very dark / black necrotic tissue
            (np.array([10,  40,  40]),   np.array([25,  255,  85])),   # Dark burnt brown
        ]
    },
    {
        "name": "Leaf Rust / Orange Pustules",
        "ranges": [
            (np.array([5,   70,  50]),   np.array([22,  255, 220])),   # Vibrant cinnamon/orange rust
            (np.array([165, 70,  50]),   np.array([180, 255, 220])),   # Deep reddish pustules
        ]
    },
    {
        "name": "Early Blight / Chlorotic Halo",
        "ranges": [
            (np.array([18,  90,  90]),   np.array([32,  255, 255])),   # Yellowish chlorotic rings
        ]
    },
    {
        "name": "Powdery Mildew / White Mycelium",
        "ranges": [
            (np.array([0,   0,  160]),   np.array([180,  45, 240])),   # Chalky white/gray mold dusting
        ]
    },
    {
        "name": "Anthracnose / Sunken Lesions",
        "ranges": [
            (np.array([8,   40,  50]),   np.array([24,  150, 150])),   # Tan / grey-brown sunken spots
        ]
    },
    {
        "name": "Sugarcane Red Rot / Crimson Lesions",
        "ranges": [
            (np.array([0,   120,  70]),   np.array([10,  255, 230])),  # Crimson red lesion bands
            (np.array([170, 120,  70]),   np.array([180, 255, 230])),  # Deep red midrib streaks
        ]
    },
    {
        "name": "Wheat Yellow / Stripe Rust",
        "ranges": [
            (np.array([18,  140, 120]),  np.array([28,  255, 255])),   # Brilliant yellow-orange stripe uredia
        ]
    },
    {
        "name": "Cotton Leaf Curl / Vein Thickening",
        "ranges": [
            (np.array([28,   40, 110]),  np.array([42,  180, 240])),   # Enation / yellow-green mottled curling
        ]
    },
    {
        "name": "Chilli Dieback / Anthracnose Necrosis",
        "ranges": [
            (np.array([12,   60,  40]),  np.array([24,  240, 120])),   # Straw-colored necrotic tip dieback
        ]
    },
]

# -- Nutrient Deficiency Spectral Profiles (HSV) --------------------------------
# Detect macro/micro nutrient deficiencies from foliar color signatures.
# Each profile includes: name, visual symptom description, HSV ranges,
# recommended fertilizer, and organic alternative.
NUTRIENT_DEFICIENCY_PROFILES = [
    {
        "nutrient": "Nitrogen (N)",
        "symptom": "Uniform pale yellow-green chlorosis on older/lower leaves",
        "ranges": [
            (np.array([22, 30, 140]), np.array([40, 120, 255])),   # Pale washed-out yellow-green
            (np.array([25, 15, 160]), np.array([38,  80, 255])),   # Very faint green, desaturated
        ],
        "fertilizer": "Urea (46-0-0) @ 50-65 kg/ha or DAP; foliar spray: 2% Urea solution",
        "organic": "Neem cake @ 250 kg/ha, Vermicompost, Green manure (Dhaincha/Sesbania)",
        "severity_threshold": {"watch": 3.0, "deficient": 8.0, "critical": 18.0}
    },
    {
        "nutrient": "Phosphorus (P)",
        "symptom": "Purple/reddish-violet tint on leaves and stems (anthocyanin buildup)",
        "ranges": [
            (np.array([135, 40, 30]),  np.array([170, 200, 160])),  # Purple-violet foliage
            (np.array([125, 30, 40]),  np.array([145, 180, 130])),  # Reddish-purple undertone
        ],
        "fertilizer": "SSP (16% P₂O₅) @ 100 kg/ha or DAP (18-46-0) @ 50 kg/ha",
        "organic": "Bone meal @ 200 kg/ha, Rock phosphate, PSB (Phosphate Solubilizing Bacteria)",
        "severity_threshold": {"watch": 2.0, "deficient": 6.0, "critical": 14.0}
    },
    {
        "nutrient": "Potassium (K)",
        "symptom": "Marginal leaf scorch — brown necrotic edges on older leaves",
        "ranges": [
            (np.array([8,  50,  40]),  np.array([22, 200, 140])),   # Brown scorched leaf margins
            (np.array([10, 70,  30]),  np.array([25, 230, 100])),   # Dark tan marginal necrosis
        ],
        "fertilizer": "MOP / Muriate of Potash (0-0-60) @ 40-60 kg/ha; SOP for sensitive crops",
        "organic": "Wood ash @ 500 kg/ha, Banana stem compost, Coconut husk ash",
        "severity_threshold": {"watch": 2.5, "deficient": 7.0, "critical": 15.0}
    },
    {
        "nutrient": "Iron (Fe)",
        "symptom": "Interveinal chlorosis — yellow between dark green veins on young leaves",
        "ranges": [
            (np.array([22, 60, 170]),  np.array([38, 180, 255])),   # Bright yellow interveinal zones
            (np.array([20, 80, 180]),  np.array([35, 200, 255])),   # Vivid yellow chlorotic patches
        ],
        "fertilizer": "Chelated Iron EDTA (Fe-EDTA 12%) foliar spray @ 0.5%; Ferrous sulphate @ 5g/L",
        "organic": "Ferrous sulphate + citric acid drench; compost tea with iron-rich amendments",
        "severity_threshold": {"watch": 2.0, "deficient": 5.0, "critical": 12.0}
    },
    {
        "nutrient": "Magnesium (Mg)",
        "symptom": "Interveinal yellowing on older/middle leaves with green veins retained",
        "ranges": [
            (np.array([20, 40, 150]),  np.array([35, 140, 240])),   # Yellow-green interveinal on old leaves
            (np.array([24, 30, 160]),  np.array([38, 110, 245])),   # Pale yellowish between veins
        ],
        "fertilizer": "Magnesium sulphate (MgSO₄) foliar @ 2% or soil @ 25 kg/ha",
        "organic": "Dolomite lime @ 200 kg/ha, Epsom salt foliar spray @ 1%",
        "severity_threshold": {"watch": 2.5, "deficient": 6.0, "critical": 13.0}
    },
    {
        "nutrient": "Zinc (Zn)",
        "symptom": "White/bleached bands or pale whitish-yellow patches on young leaves",
        "ranges": [
            (np.array([0,   0, 180]),  np.array([180, 25, 245])),   # Near-white bleached leaf tissue
            (np.array([18, 10, 190]),  np.array([35,  40, 250])),   # Whitish-yellow pale bands
        ],
        "fertilizer": "Zinc sulphate (ZnSO₄ 21%) foliar @ 0.5% or soil @ 25 kg/ha",
        "organic": "Zinc-enriched compost, Chelated Zn foliar spray, IISR Zn biofertilizer",
        "severity_threshold": {"watch": 1.5, "deficient": 4.0, "critical": 10.0}
    },
    {
        "nutrient": "Sulphur (S)",
        "symptom": "Uniform pale yellow on newest/youngest leaves (unlike N which affects old leaves)",
        "ranges": [
            (np.array([25, 25, 170]),  np.array([38,  90, 255])),   # Pale yellow on new growth
            (np.array([28, 15, 180]),  np.array([40,  70, 250])),   # Light greenish-yellow, low sat
        ],
        "fertilizer": "Gypsum (CaSO₄) @ 200 kg/ha or Ammonium sulphate (24% S) @ 50 kg/ha",
        "organic": "Elemental sulphur @ 20 kg/ha, mustard cake, sulphur-rich compost",
        "severity_threshold": {"watch": 2.0, "deficient": 5.0, "critical": 11.0}
    },
]

# Calibrated healthy foliage bounds:
_LOWER_HEALTHY_GREEN = np.array([25, 25, 25])
_UPPER_HEALTHY_GREEN = np.array([95, 255, 255])

# Specular highlight threshold (sunlight reflection on waxy leaf cuticles)
_LOWER_GLARE = np.array([0, 0, 195])
_UPPER_GLARE = np.array([180, 30, 255])


class PlantImagePreprocessor:
    """
    Advanced, calibrated image preprocessing module for plant disease diagnostics.
    """

    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size
        self._clahe_standard = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self._clahe_boost = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))

    def preprocess_and_segment(self, image_path, segmentation_mode="smart_adaptive", sensitivity="balanced", clahe_mode="standard"):
        """
        Full diagnostic preprocessing pipeline.
        
        Parameters:
        -----------
        image_path        : str, path to foliage image
        segmentation_mode : 'smart_adaptive' or 'full_frame'
        sensitivity       : 'balanced', 'high_specificity' (conservative), or 'early_warning'
        clahe_mode        : 'standard' or 'boost'
        """
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"Could not load image at {image_path}")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # 1. Aspect-Ratio Letterbox Resize
        resized_rgb = self._resize_with_aspect_ratio(image_rgb)

        # 2. CLAHE Local Contrast Normalization
        clahe_engine = self._clahe_boost if clahe_mode == "boost" else self._clahe_standard
        enhanced_rgb = self._apply_clahe(resized_rgb, clahe_engine)

        # 3. Bilateral Edge-Preserving Denoising
        denoised_rgb = cv2.bilateralFilter(enhanced_rgb, d=9, sigmaColor=75, sigmaSpace=75)

        # 4. Foliar Segmentation
        if segmentation_mode == "full_frame":
            h, w = denoised_rgb.shape[:2]
            leaf_mask = np.ones((h, w), dtype=np.uint8) * 255
            leaf_segmented = denoised_rgb.copy()
        else:
            leaf_mask, leaf_segmented = self._segment_leaf(denoised_rgb)

        # 5. Calibrated Multi-Disease Pathology Extraction
        healthy_mask, diseased_mask, disease_report = self._extract_infection_masks(
            leaf_segmented, leaf_mask, sensitivity=sensitivity
        )

        # 6. Quantitative Infection Metric Calculation
        infection_pct = self.calculate_infection_level(leaf_mask, diseased_mask)

        # 7. Nutrient Deficiency Color Analysis
        deficiency_report = self._extract_deficiency_masks(
            leaf_segmented, leaf_mask, healthy_mask, diseased_mask
        )

        # 8. Normalized Float Tensor for Neural Inference [0, 1]
        normalized_tensor = leaf_segmented.astype(np.float32) / 255.0

        return {
            'normalized_tensor':    normalized_tensor,
            'leaf_mask':            leaf_mask,
            'healthy_mask':         healthy_mask,
            'diseased_mask':        diseased_mask,
            'infection_percentage': infection_pct,
            'disease_report':       disease_report,
            'deficiency_report':    deficiency_report,
            'original_resized':     resized_rgb,
            'leaf_segmented':       leaf_segmented,
            'segmentation_mode':    segmentation_mode,
            'sensitivity':          sensitivity
        }

    # -- Internal Processing Methods ------------------------------------------

    def _resize_with_aspect_ratio(self, image):
        """Fits image inside target_size with black letterbox boundary."""
        h, w = image.shape[:2]
        tw, th = self.target_size
        scale = min(tw / w, th / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((th, tw, 3), dtype=np.uint8)
        x0, y0 = (tw - nw) // 2, (th - nh) // 2
        canvas[y0:y0+nh, x0:x0+nw] = resized
        return canvas

    def _apply_clahe(self, image_rgb, clahe_engine):
        """Enhances local foliar texture on LAB L-channel."""
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = clahe_engine.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    def _segment_leaf(self, image_rgb):
        """
        Smart adaptive leaf segmentation combining LAB chromatic thresholding
        and largest connected morphological component.
        """
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        _, a, _ = cv2.split(lab)

        # Otsu threshold on 'a' channel (green is low a)
        _, mask_otsu = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # HSV Green fallback in case background is also non-standard
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        mask_hsv = cv2.inRange(hsv, np.array([20, 20, 20]), np.array([100, 255, 255]))
        combined_coarse = cv2.bitwise_or(mask_otsu, mask_hsv)

        # Keep largest connected component (main leaf organ)
        mask = self._keep_largest_component(combined_coarse)

        # Clean-up with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Fill internal holes to preserve internal necrotic spots
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            largest = max(cnts, key=cv2.contourArea)
            solid_mask = np.zeros_like(mask)
            cv2.drawContours(solid_mask, [largest], -1, 255, -1)
            mask = solid_mask

        # Fallback safeguard: if mask occupies <5% of image, return full image
        total_px = mask.shape[0] * mask.shape[1]
        if cv2.countNonZero(mask) < 0.05 * total_px:
            mask = np.ones_like(mask) * 255

        segmented = cv2.bitwise_and(image_rgb, image_rgb, mask=mask)
        return mask, segmented

    @staticmethod
    def _keep_largest_component(binary_mask):
        """Retains only the primary largest connected component."""
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
        if num_labels <= 1:
            return binary_mask
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        out = np.zeros_like(binary_mask)
        out[labels == largest] = 255
        return out

    def _extract_infection_masks(self, segmented_leaf_rgb, total_leaf_mask, sensitivity="balanced"):
        """
        Calibrated multi-pathology color analysis.
        - Identifies healthy chlorophyll foliage (including natural veins & lighter green).
        - Filters out specular highlights / glare from disease consideration.
        - Matches genuine disease profiles (Necrosis, Rust, Chlorosis, Mildew, Anthracnose).
        - Enforces spatial cluster clustering to eliminate isolated sensor noise.
        """
        hsv = cv2.cvtColor(segmented_leaf_rgb, cv2.COLOR_RGB2HSV)
        total_leaf_px = max(cv2.countNonZero(total_leaf_mask), 1)

        # 1. Healthy green tissue mask
        green_raw = cv2.inRange(hsv, _LOWER_HEALTHY_GREEN, _UPPER_HEALTHY_GREEN)
        healthy_mask = cv2.bitwise_and(green_raw, total_leaf_mask)

        # 2. Specular glare / reflection mask (exclude from disease)
        glare_raw = cv2.inRange(hsv, _LOWER_GLARE, _UPPER_GLARE)
        glare_mask = cv2.bitwise_and(glare_raw, total_leaf_mask)

        # 3. Minimum lesion cluster area based on sensitivity
        if sensitivity == "early_warning":
            min_cluster_px = 6
        elif sensitivity == "high_specificity":
            min_cluster_px = 25
        else:  # balanced
            min_cluster_px = 12

        combined_disease_mask = np.zeros_like(total_leaf_mask)
        disease_report = []

        for profile in DISEASE_PROFILES:
            profile_raw = np.zeros_like(total_leaf_mask)
            for (lo, hi) in profile["ranges"]:
                partial = cv2.inRange(hsv, lo, hi)
                profile_raw = cv2.bitwise_or(profile_raw, partial)

            # Confine within leaf boundary and remove healthy & glare tissue
            profile_leaf = cv2.bitwise_and(profile_raw, total_leaf_mask)
            profile_leaf = cv2.bitwise_and(profile_leaf, cv2.bitwise_not(healthy_mask))
            profile_leaf = cv2.bitwise_and(profile_leaf, cv2.bitwise_not(glare_mask))

            # Filter out single-pixel noise via connected components
            filtered_profile = self._filter_small_clusters(profile_leaf, min_area=min_cluster_px)
            px = cv2.countNonZero(filtered_profile)
            pct = round(px / total_leaf_px * 100, 2)

            if pct >= 0.15:  # Only report if meaningful lesion presence (>0.15%)
                disease_report.append({
                    "name": profile["name"],
                    "pixel_count": px,
                    "pct_of_leaf": pct
                })
                combined_disease_mask = cv2.bitwise_or(combined_disease_mask, filtered_profile)

        # Re-verify healthy mask: everything on leaf not confirmed as disease or glare is preserved healthy
        healthy_mask = cv2.bitwise_and(total_leaf_mask, cv2.bitwise_not(combined_disease_mask))

        return healthy_mask, combined_disease_mask, disease_report

    def _extract_deficiency_masks(self, segmented_leaf_rgb, total_leaf_mask, healthy_mask, diseased_mask):
        """
        Nutrient deficiency color analysis on foliar tissue.
        
        Analyzes the non-diseased leaf area for color signatures that indicate
        macro/micro nutrient deficiencies (N, P, K, Fe, Mg, Zn, S).
        
        Returns a list of detected deficiency dicts with:
          nutrient, symptom, pct_of_leaf, severity, severity_css,
          fertilizer, organic
        """
        hsv = cv2.cvtColor(segmented_leaf_rgb, cv2.COLOR_RGB2HSV)
        total_leaf_px = max(cv2.countNonZero(total_leaf_mask), 1)

        # Analyze only the non-diseased, non-glare leaf tissue
        glare_raw = cv2.inRange(hsv, _LOWER_GLARE, _UPPER_GLARE)
        glare_mask = cv2.bitwise_and(glare_raw, total_leaf_mask)

        # Tissue available for deficiency analysis = leaf minus disease minus glare
        analysis_zone = cv2.bitwise_and(total_leaf_mask, cv2.bitwise_not(diseased_mask))
        analysis_zone = cv2.bitwise_and(analysis_zone, cv2.bitwise_not(glare_mask))

        deficiency_report = []

        for profile in NUTRIENT_DEFICIENCY_PROFILES:
            profile_raw = np.zeros_like(total_leaf_mask)
            for (lo, hi) in profile["ranges"]:
                partial = cv2.inRange(hsv, lo, hi)
                profile_raw = cv2.bitwise_or(profile_raw, partial)

            # Confine within analysis zone (leaf - disease - glare)
            profile_leaf = cv2.bitwise_and(profile_raw, analysis_zone)

            # Remove the healthy saturated green from deficiency consideration
            profile_leaf = cv2.bitwise_and(profile_leaf, cv2.bitwise_not(healthy_mask))

            # Filter noise
            filtered = self._filter_small_clusters(profile_leaf, min_area=10)
            px = cv2.countNonZero(filtered)
            pct = round(px / total_leaf_px * 100, 2)

            # Only report if above minimum threshold (0.5% of leaf)
            if pct >= 0.5:
                thresholds = profile["severity_threshold"]
                if pct >= thresholds["critical"]:
                    severity, severity_css = "Critical", "deficiency-critical"
                elif pct >= thresholds["deficient"]:
                    severity, severity_css = "Deficient", "deficiency-deficient"
                elif pct >= thresholds["watch"]:
                    severity, severity_css = "Watch", "deficiency-watch"
                else:
                    severity, severity_css = "Normal", "deficiency-normal"

                deficiency_report.append({
                    "nutrient": profile["nutrient"],
                    "symptom": profile["symptom"],
                    "pixel_count": px,
                    "pct_of_leaf": pct,
                    "severity": severity,
                    "severity_css": severity_css,
                    "fertilizer": profile["fertilizer"],
                    "organic": profile["organic"],
                })

        # Sort by severity (Critical > Deficient > Watch > Normal)
        severity_order = {"Critical": 0, "Deficient": 1, "Watch": 2, "Normal": 3}
        deficiency_report.sort(key=lambda d: (severity_order.get(d["severity"], 4), -d["pct_of_leaf"]))

        return deficiency_report

    @staticmethod
    def _filter_small_clusters(binary_mask, min_area=12):
        """Removes isolated speckles and retains only coherent lesion clusters."""
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
        out = np.zeros_like(binary_mask)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                out[labels == i] = 255
        return out

    @staticmethod
    def calculate_infection_level(total_leaf_mask, diseased_mask):
        """Infection % = diseased pixels / total leaf pixels * 100."""
        total = cv2.countNonZero(total_leaf_mask)
        if total == 0:
            return 0.0
        diseased = cv2.countNonZero(diseased_mask)
        return round(diseased / total * 100.0, 2)
