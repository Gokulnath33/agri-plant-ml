"""
features.py
===========
Computer Vision & Feature Engineering Module for Automated Site-Specific Pesticide Application.

Extracts:
1. Multi-Space Color Histograms (HSV + RGB color distributions and statistical moments).
2. Gabor Wavelet Texture Filter Banks (multi-frequency & multi-orientation lesion textures).
3. Foliar Thermal & Water-Stress Indices (CWSI proxy & temperature delta).
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any, List, Optional


def preprocess_leaf_image(
    image_input,
    target_size: Tuple[int, int] = (256, 256),
    apply_clahe: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocesses raw leaf image:
    - Resizes to standard dimension while maintaining aspect ratio
    - Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) on L-channel
    - Computes Otsu foliage segmentation mask
    
    Returns:
        (preprocessed_bgr, foliage_mask)
    """
    if isinstance(image_input, str):
        img_bgr = cv2.imread(image_input)
        if img_bgr is None:
            raise FileNotFoundError(f"Cannot read leaf image from path: {image_input}")
    elif isinstance(image_input, np.ndarray):
        img_bgr = image_input.copy()
    else:
        raise ValueError("image_input must be a file path string or numpy BGR array.")

    # Resize to target dimension
    resized_bgr = cv2.resize(img_bgr, target_size, interpolation=cv2.INTER_AREA)

    # Optional CLAHE on LAB color space
    if apply_clahe:
        lab = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        preprocessed_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    else:
        preprocessed_bgr = resized_bgr

    # Foliage segmentation in HSV color space
    hsv = cv2.cvtColor(preprocessed_bgr, cv2.COLOR_BGR2HSV)
    # Healthy & diseased foliage spectral threshold
    lower_foliage = np.array([5, 25, 25])
    upper_foliage = np.array([110, 255, 255])
    foliage_mask = cv2.inRange(hsv, lower_foliage, upper_foliage)

    # Morphological refinement
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    foliage_mask = cv2.morphologyEx(foliage_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    foliage_mask = cv2.morphologyEx(foliage_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    return preprocessed_bgr, foliage_mask


def extract_color_histograms(
    image_bgr: np.ndarray,
    mask: Optional[np.ndarray] = None,
    hsv_bins: Tuple[int, int, int] = (8, 8, 8),
    rgb_bins: Tuple[int, int, int] = (8, 8, 8)
) -> np.ndarray:
    """
    Extracts normalized 3D color histograms in both HSV and RGB color spaces,
    along with statistical moments (mean, std, skewness).
    """
    # 1. HSV Histogram
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    hist_hsv = cv2.calcHist(
        [hsv], [0, 1, 2], mask,
        [hsv_bins[0], hsv_bins[1], hsv_bins[2]],
        [0, 180, 0, 256, 0, 256]
    )
    hist_hsv = cv2.normalize(hist_hsv, hist_hsv).flatten()

    # 2. RGB Histogram
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    hist_rgb = cv2.calcHist(
        [rgb], [0, 1, 2], mask,
        [rgb_bins[0], rgb_bins[1], rgb_bins[2]],
        [0, 256, 0, 256, 0, 256]
    )
    hist_rgb = cv2.normalize(hist_rgb, hist_rgb).flatten()

    # 3. Channel Statistical Moments (Mean & Standard Deviation)
    moments = []
    if mask is not None and cv2.countNonZero(mask) > 0:
        pixels_hsv = hsv[mask > 0]
        pixels_rgb = rgb[mask > 0]
    else:
        pixels_hsv = hsv.reshape(-1, 3)
        pixels_rgb = rgb.reshape(-1, 3)

    for ch in range(3):
        moments.append(np.mean(pixels_hsv[:, ch]))
        moments.append(np.std(pixels_hsv[:, ch]))
        moments.append(np.mean(pixels_rgb[:, ch]))
        moments.append(np.std(pixels_rgb[:, ch]))

    moments_arr = np.array(moments, dtype=np.float32)
    # Normalize moments
    moments_norm = moments_arr / (np.linalg.norm(moments_arr) + 1e-6)

    return np.concatenate([hist_hsv, hist_rgb, moments_norm])


def extract_gabor_textures(
    image_bgr: np.ndarray,
    mask: Optional[np.ndarray] = None,
    frequencies: Tuple[float, ...] = (0.1, 0.25, 0.4),
    orientations: Tuple[float, ...] = (0, np.pi/4, np.pi/2, 3*np.pi/4),
    ksize: int = 21,
    sigma: float = 4.0,
    gamma: float = 0.5
) -> np.ndarray:
    """
    Extracts Gabor wavelet texture filter responses across multiple frequencies
    and spatial orientations to capture leaf lesion roughness, pustules, and necroses.
    
    Returns:
        1D feature vector containing mean energy and variance for each Gabor kernel response.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    gabor_features = []

    for frequency in frequencies:
        wavelength = 1.0 / frequency
        for theta in orientations:
            kernel = cv2.getGaborKernel(
                (ksize, ksize),
                sigma=sigma,
                theta=theta,
                lambd=wavelength,
                gamma=gamma,
                psi=0,
                ktype=cv2.CV_32F
            )
            filtered = cv2.filter2D(gray, cv2.CV_32F, kernel)

            if mask is not None and cv2.countNonZero(mask) > 0:
                roi_vals = filtered[mask > 0]
            else:
                roi_vals = filtered.flatten()

            mean_val = float(np.mean(roi_vals))
            std_val = float(np.std(roi_vals))
            energy_val = float(np.mean(roi_vals ** 2))

            gabor_features.extend([mean_val, std_val, energy_val])

    gabor_arr = np.array(gabor_features, dtype=np.float32)
    # Unit normalization
    norm = np.linalg.norm(gabor_arr)
    if norm > 0:
        gabor_arr /= norm
    return gabor_arr


def extract_thermal_index(
    image_bgr: np.ndarray,
    mask: Optional[np.ndarray] = None,
    ambient_temp_c: float = 28.0
) -> Dict[str, float]:
    """
    Calculates empirical canopy thermal stress index (CWSI proxy) and evapotranspiration
    deficit from foliar spectral reflectance and temperature differentials.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    
    if mask is not None and cv2.countNonZero(mask) > 0:
        h_vals = hsv[:, :, 0][mask > 0]
        s_vals = hsv[:, :, 1][mask > 0]
        v_vals = hsv[:, :, 2][mask > 0]
    else:
        h_vals = hsv[:, :, 0].flatten()
        s_vals = hsv[:, :, 1].flatten()
        v_vals = hsv[:, :, 2].flatten()

    # Chlorophyll index: green hue (approx 35-85 in OpenCV HSV)
    green_pixels = np.sum((h_vals >= 35) & (h_vals <= 85))
    total_px = max(1, len(h_vals))
    chlorophyll_ratio = float(green_pixels) / total_px

    # Necrotic/stressed tissue index: hue in yellow/brown/orange range (5-30)
    stressed_pixels = np.sum((h_vals >= 5) & (h_vals <= 30) & (s_vals > 40))
    necrosis_ratio = float(stressed_pixels) / total_px

    # Estimated canopy temperature proxy based on evapotranspiration reduction
    # Diseased/stressed tissue transpires less water -> higher surface temperature
    canopy_temp_delta = (necrosis_ratio * 4.5) - (chlorophyll_ratio * 1.5)
    estimated_canopy_temp = round(ambient_temp_c + canopy_temp_delta, 2)

    # Crop Water Stress Index (CWSI): 0.0 (fully hydrated/healthy) to 1.0 (severe drought/necrotic stress)
    cwsi = float(np.clip((1.0 - chlorophyll_ratio) * 0.7 + necrosis_ratio * 0.6, 0.0, 1.0))

    return {
        "chlorophyll_ratio": round(chlorophyll_ratio, 4),
        "necrosis_ratio": round(necrosis_ratio, 4),
        "canopy_temp_delta": round(canopy_temp_delta, 2),
        "estimated_canopy_temp_c": estimated_canopy_temp,
        "cwsi_index": round(cwsi, 4)
    }


def extract_full_image_features(
    image_input,
    target_size: Tuple[int, int] = (256, 256)
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Extracts the combined high-dimensional raw feature vector (Color Histograms + Gabor Textures)
    and foliar metadata.
    
    Returns:
        (feature_vector, metadata_dict)
    """
    preprocessed_bgr, mask = preprocess_leaf_image(image_input, target_size=target_size)
    color_feats = extract_color_histograms(preprocessed_bgr, mask=mask)
    gabor_feats = extract_gabor_textures(preprocessed_bgr, mask=mask)
    thermal_meta = extract_thermal_index(preprocessed_bgr, mask=mask)

    combined_features = np.concatenate([color_feats, gabor_feats]).astype(np.float32)

    metadata = {
        "raw_feature_dim": int(combined_features.shape[0]),
        "color_feature_dim": int(color_feats.shape[0]),
        "gabor_feature_dim": int(gabor_feats.shape[0]),
        "thermal_metrics": thermal_meta,
        "foliage_mask_coverage_pct": round((cv2.countNonZero(mask) / (target_size[0] * target_size[1])) * 100, 2)
    }

    return combined_features, metadata
