"""
models.py
=========
Machine Learning Architecture for Automated Site-Specific Pesticide Application:
1. Principal Component Analysis (PCA): Dimensionality reduction of high-dimensional feature vectors.
2. Support Vector Machine (SVM): Multi-class leaf pathology classifier (Bacterial Blight, Leaf Rust, Anthracnose, Late Blight, Healthy).
3. Multilayer Perceptron (MLP) with Backpropagation: Multi-sensor fusion engine (SVM output + Thermal Index + Environmental Sensor Telemetry -> Severity Tier).
"""

import os
import joblib
import warnings
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neural_network import MLPClassifier

# Silence deprecation / convergence warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Constants & Class Labels
PATHOLOGY_CLASSES = [
    "Healthy",
    "Bacterial Blight",
    "Leaf Rust",
    "Anthracnose",
    "Late Blight"
]

SEVERITY_TIERS = [
    "Mild",
    "Moderate",
    "Severe"
]


class PCADimensionalityReducer:
    """
    Principal Component Analysis (PCA) feature compression engine.
    Reduces high-dimensional Gabor + Color histogram feature vectors into principal components.
    """
    def __init__(self, n_components: int = 32, whiten: bool = True, random_state: int = 42):
        self.n_components = n_components
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components, whiten=whiten, random_state=random_state)
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> "PCADimensionalityReducer":
        X_scaled = self.scaler.fit_transform(X)
        self.pca.fit(X_scaled)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("PCA model is not fitted yet. Call fit() before transform().")
        X_scaled = self.scaler.transform(X)
        return self.pca.transform(X_scaled)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

    def get_explained_variance_ratio(self) -> float:
        if not self.is_fitted:
            return 0.0
        return float(np.sum(self.pca.explained_variance_ratio_))

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump({"scaler": self.scaler, "pca": self.pca, "is_fitted": self.is_fitted}, filepath)

    def load(self, filepath: str) -> "PCADimensionalityReducer":
        data = joblib.load(filepath)
        self.scaler = data["scaler"]
        self.pca = data["pca"]
        self.is_fitted = data["is_fitted"]
        return self


class PlantPathologySVMClassifier:
    """
    Support Vector Machine (SVM) Multi-Class Pathology Classifier.
    Employs Radial Basis Function (RBF) kernel with Calibrated Probability Estimation.
    """
    def __init__(
        self,
        C: float = 10.0,
        gamma: str = "scale",
        class_names: Optional[List[str]] = None,
        random_state: int = 42
    ):
        self.class_names = class_names or PATHOLOGY_CLASSES
        base_svc = SVC(
            C=C,
            kernel="rbf",
            gamma=gamma,
            decision_function_shape="ovr",
            class_weight="balanced",
            random_state=random_state
        )
        self.classifier = CalibratedClassifierCV(estimator=base_svc, cv=3)
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "PlantPathologySVMClassifier":
        self.classifier.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classifier.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.classifier.predict_proba(X)

    def predict_single(self, X_sample: np.ndarray) -> Dict[str, Any]:
        """Runs single-sample inference and returns structured prediction dictionary."""
        if X_sample.ndim == 1:
            X_sample = np.expand_dims(X_sample, axis=0)

        probs = self.predict_proba(X_sample)[0]
        pred_idx = int(np.argmax(probs))
        predicted_class = self.class_names[pred_idx]
        confidence = float(probs[pred_idx])

        class_probabilities = {}
        for i, name in enumerate(self.class_names):
            class_probabilities[name] = round(float(probs[i]), 4)

        return {
            "predicted_class": predicted_class,
            "class_index": pred_idx,
            "confidence": round(confidence * 100, 2),
            "class_probabilities": class_probabilities,
            "probability_vector": probs.tolist()
        }

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump({
            "classifier": self.classifier,
            "class_names": self.class_names,
            "is_fitted": self.is_fitted
        }, filepath)

    def load(self, filepath: str) -> "PlantPathologySVMClassifier":
        data = joblib.load(filepath)
        self.classifier = data["classifier"]
        self.class_names = data["class_names"]
        self.is_fitted = data["is_fitted"]
        return self


class MultiSensorFusionMLP:
    """
    Multilayer Perceptron (MLP) Neural Network with Backpropagation.
    Fuses:
    1. SVM Pathology Probabilities (5 features)
    2. Thermal Heatmap Indices & Temperature Delta (3 features)
    3. Environmental Microclimate Telemetry: Temp, Humidity, Soil Moisture, Solar Flux (4 features)
    
    Total Input Dimension: 12 features
    Output: Severity Tier ('Mild', 'Moderate', 'Severe') with Softmax Probabilities.
    """
    def __init__(
        self,
        hidden_layer_sizes: Tuple[int, ...] = (64, 32),
        activation: str = "relu",
        solver: str = "adam",
        alpha: float = 0.0001,
        max_iter: int = 800,
        random_state: int = 42
    ):
        self.scaler = StandardScaler()
        self.mlp = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            solver=solver,
            alpha=alpha,
            learning_rate_init=0.005,
            max_iter=max_iter,
            early_stopping=True,
            n_iter_no_change=30,
            random_state=random_state
        )
        self.severity_classes = SEVERITY_TIERS
        self.is_fitted = False

    def build_fusion_vector(
        self,
        svm_probabilities: np.ndarray,
        thermal_metrics: Dict[str, float],
        environmental_telemetry: Dict[str, float]
    ) -> np.ndarray:
        """
        Constructs the unified 12-dimensional sensor fusion vector.
        """
        # 1. SVM Probabilities (5 elements)
        svm_arr = np.asarray(svm_probabilities, dtype=np.float32).flatten()
        if len(svm_arr) != 5:
            padded = np.zeros(5, dtype=np.float32)
            padded[:min(5, len(svm_arr))] = svm_arr[:5]
            svm_arr = padded

        # 2. Thermal Heatmap Metrics (3 elements)
        cwsi = float(thermal_metrics.get("cwsi_index", 0.3))
        canopy_temp_delta = float(thermal_metrics.get("canopy_temp_delta", 1.0))
        necrosis_ratio = float(thermal_metrics.get("necrosis_ratio", 0.1))
        thermal_arr = np.array([cwsi, canopy_temp_delta, necrosis_ratio], dtype=np.float32)

        # 3. Environmental Sensor Telemetry (4 elements)
        ambient_temp = float(environmental_telemetry.get("ambient_temp_c", 28.0))
        relative_humidity = float(environmental_telemetry.get("relative_humidity_pct", 65.0))
        soil_moisture = float(environmental_telemetry.get("soil_moisture_pct", 55.0))
        solar_radiation = float(environmental_telemetry.get("solar_radiation_w_m2", 500.0))
        env_arr = np.array([ambient_temp, relative_humidity, soil_moisture, solar_radiation], dtype=np.float32)

        return np.concatenate([svm_arr, thermal_arr, env_arr])

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MultiSensorFusionMLP":
        X_scaled = self.scaler.fit_transform(X)
        self.mlp.fit(X_scaled, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.mlp.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.mlp.predict_proba(X_scaled)

    def predict_single(
        self,
        svm_probabilities: np.ndarray,
        thermal_metrics: Dict[str, float],
        environmental_telemetry: Dict[str, float]
    ) -> Dict[str, Any]:
        """Runs multi-sensor MLP neural fusion and produces severity assessment."""
        fusion_vec = self.build_fusion_vector(
            svm_probabilities, thermal_metrics, environmental_telemetry
        )
        X_in = np.expand_dims(fusion_vec, axis=0)
        X_scaled = self.scaler.transform(X_in)
        probs = self.mlp.predict_proba(X_scaled)[0]
        pred_idx = int(np.argmax(probs))
        severity = self.severity_classes[pred_idx]
        confidence = float(probs[pred_idx])

        severity_probs = {}
        for i, s_tier in enumerate(self.severity_classes):
            severity_probs[s_tier] = round(float(probs[i]), 4)

        return {
            "severity_tier": severity,
            "severity_confidence": round(confidence * 100, 2),
            "severity_probabilities": severity_probs,
            "fusion_features": {
                "cwsi_index": thermal_metrics.get("cwsi_index", 0.0),
                "canopy_temp_delta": thermal_metrics.get("canopy_temp_delta", 0.0),
                "relative_humidity_pct": environmental_telemetry.get("relative_humidity_pct", 0.0),
                "soil_moisture_pct": environmental_telemetry.get("soil_moisture_pct", 0.0)
            }
        }

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump({
            "mlp": self.mlp,
            "scaler": self.scaler,
            "severity_classes": self.severity_classes,
            "is_fitted": self.is_fitted
        }, filepath)

    def load(self, filepath: str) -> "MultiSensorFusionMLP":
        data = joblib.load(filepath)
        self.mlp = data["mlp"]
        self.scaler = data["scaler"]
        self.severity_classes = data["severity_classes"]
        self.is_fitted = data["is_fitted"]
        return self
