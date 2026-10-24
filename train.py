import os
import cv2
import time
import numpy as np
import joblib
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Configuration
DATASET_DIR = "dataset"
MODELS_DIR = "models"
SAMPLES_PER_CLASS = 120      # balanced across all 79 active crop & pathology classes
MIN_SAMPLES_PER_CLASS = 10   # skip folders with fewer than this many images
PCA_COMPONENTS = 128
RANDOM_STATE = 42
JOBLIB_COMPRESS = ('zlib', 3)  # compress saved models (keeps files small for GitHub)

def extract_image_features(img_bgr):
    """
    Extracts high-discriminative multi-space color histogram and spatial features:
    - 3D HSV Color Histogram (8x8x8 = 512 bins, normalized)
    - 3D RGB Color Histogram (8x8x8 = 512 bins, normalized)
    - 32x32 Spatial Color Representation (3072 normalized float values)
    Total dimension: 4,096 features.
    """
    if img_bgr is None:
        return None
        
    # 1. HSV Histogram
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    hist_hsv = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
    hist_hsv = cv2.normalize(hist_hsv, hist_hsv).flatten()
    
    # 2. RGB Histogram
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    hist_rgb = cv2.calcHist([rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist_rgb = cv2.normalize(hist_rgb, hist_rgb).flatten()
    
    # 3. Spatial Color Grid (32x32x3)
    spatial = cv2.resize(rgb, (32, 32)).flatten().astype(np.float32) / 255.0
    
    return np.concatenate([hist_hsv, hist_rgb, spatial])

def load_data(max_per_class=SAMPLES_PER_CLASS):
    X = []
    y = []
    classes = {}
    
    if not os.path.exists(DATASET_DIR):
        print(f"Error: Directory '{DATASET_DIR}' does not exist.")
        return None, None, None

    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')

    # Filter to only folders with at least MIN_SAMPLES_PER_CLASS real images
    class_names = sorted([
        d for d in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, d))
        and len([
            f for f in os.listdir(os.path.join(DATASET_DIR, d))
            if f.lower().endswith(valid_exts)
        ]) >= MIN_SAMPLES_PER_CLASS
    ])

    if len(class_names) == 0:
        print(f"Warning: No valid class folders found in '{DATASET_DIR}'.")
        return None, None, None

    print(f"Found {len(class_names)} active pathology classes (>={MIN_SAMPLES_PER_CLASS} images each). Loading balanced subset (max {max_per_class} per class)...")
    t0 = time.time()

    for idx, class_name in enumerate(class_names):
        classes[idx] = class_name
        class_dir = os.path.join(DATASET_DIR, class_name)
        img_files = [f for f in os.listdir(class_dir) if f.lower().endswith(valid_exts)][:max_per_class]
        
        for img_name in img_files:
            try:
                img_path = os.path.join(class_dir, img_name)
                img = cv2.imread(img_path)
                feat = extract_image_features(img)
                if feat is not None:
                    X.append(feat)
                    y.append(idx)
            except Exception as e:
                pass

    print(f"Loaded {len(X)} feature vectors across {len(classes)} classes in {time.time()-t0:.2f}s.")
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32), classes

def train_all_models():
    print("=" * 60)
    print("[*] Plant Pathology Machine Learning Training Pipeline")
    print("=" * 60)
    
    X, y, classes = load_data()
    if X is None or len(X) == 0:
        print("Error: No data available for training.")
        return

    # Train / Test Stratified Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )
    print(f"Training set: {len(X_train)} samples | Test set: {len(X_test)} samples")

    # 1. Dimensionality Reduction via PCA
    print(f"\n1. Fitting PCA with {PCA_COMPONENTS} components (with whitening)...")
    t_pca = time.time()
    n_comp = min(PCA_COMPONENTS, len(X_train))
    pca = PCA(n_components=n_comp, whiten=True, random_state=RANDOM_STATE)
    X_train_pca = pca.fit_transform(X_train)
    X_test_pca = pca.transform(X_test)
    var_exp = float(np.sum(pca.explained_variance_ratio_))
    print(f"   PCA fitted in {time.time()-t_pca:.2f}s. Explained Variance Ratio: {var_exp:.2%}")

    # Ensure models directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pca, os.path.join(MODELS_DIR, 'pca.joblib'), compress=JOBLIB_COMPRESS)
    joblib.dump(classes, os.path.join(MODELS_DIR, 'classes.joblib'), compress=JOBLIB_COMPRESS)
    print(f"   Saved 'pca.joblib' and 'classes.joblib' to '{MODELS_DIR}/'")

    # 2. Train Calibrated Support Vector Machine (SVM)
    print("\n2. Training Calibrated Support Vector Machine (SVM)...")
    t_svm = time.time()
    base_svc = SVC(kernel='rbf', C=10.0, gamma='scale', random_state=RANDOM_STATE)
    svm = CalibratedClassifierCV(estimator=base_svc, cv=3)
    svm.fit(X_train_pca, y_train)
    svm_acc = accuracy_score(y_test, svm.predict(X_test_pca))
    print(f"   SVM Training Time: {time.time()-t_svm:.2f}s | Test Accuracy: {svm_acc:.2%}")
    joblib.dump(svm, os.path.join(MODELS_DIR, 'svm.joblib'), compress=JOBLIB_COMPRESS)
    print(f"   Saved 'svm.joblib' to '{MODELS_DIR}/'")

    # 3. Train Multilayer Perceptron (MLP) Neural Network
    print("\n3. Training Multilayer Perceptron (MLP Neural Network)...")
    t_mlp = time.time()
    mlp = MLPClassifier(
        hidden_layer_sizes=(256, 128),
        activation='relu',
        solver='adam',
        alpha=0.0001,
        learning_rate_init=0.003,
        max_iter=400,
        early_stopping=True,
        n_iter_no_change=20,
        random_state=RANDOM_STATE
    )
    mlp.fit(X_train_pca, y_train)
    mlp_acc = accuracy_score(y_test, mlp.predict(X_test_pca))
    print(f"   MLP Training Time: {time.time()-t_mlp:.2f}s | Test Accuracy: {mlp_acc:.2%}")
    joblib.dump(mlp, os.path.join(MODELS_DIR, 'mlp.joblib'), compress=JOBLIB_COMPRESS)
    print(f"   Saved 'mlp.joblib' to '{MODELS_DIR}/'")

    # 4. Train K-Nearest Neighbors (KNN)
    print("\n4. Training K-Nearest Neighbors (KNN)...")
    t_knn = time.time()
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
    knn.fit(X_train_pca, y_train)
    knn_acc = accuracy_score(y_test, knn.predict(X_test_pca))
    print(f"   KNN Training Time: {time.time()-t_knn:.2f}s | Test Accuracy: {knn_acc:.2%}")
    joblib.dump(knn, os.path.join(MODELS_DIR, 'knn.joblib'), compress=JOBLIB_COMPRESS)
    print(f"   Saved 'knn.joblib' to '{MODELS_DIR}/'")

    # 5. Train Random Forest (RF)
    print("\n5. Training Random Forest Classifier...")
    t_rf = time.time()
    rf = RandomForestClassifier(n_estimators=100, max_depth=20, random_state=RANDOM_STATE)
    rf.fit(X_train_pca, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test_pca))
    print(f"   Random Forest Training Time: {time.time()-t_rf:.2f}s | Test Accuracy: {rf_acc:.2%}")
    joblib.dump(rf, os.path.join(MODELS_DIR, 'rf.joblib'), compress=JOBLIB_COMPRESS)
    print(f"   Saved 'rf.joblib' to '{MODELS_DIR}/'")

    print("\n" + "=" * 60)
    print("[*] MODEL BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"1. Support Vector Machine (SVM): {svm_acc:.2%}")
    print(f"2. Multilayer Perceptron (MLP):  {mlp_acc:.2%}")
    print(f"3. Random Forest (RF):           {rf_acc:.2%}")
    print(f"4. K-Nearest Neighbors (KNN):    {knn_acc:.2%}")
    print("=" * 60)
    print(f"All models successfully trained and stored in '{MODELS_DIR}/'!\n")

if __name__ == "__main__":
    train_all_models()
