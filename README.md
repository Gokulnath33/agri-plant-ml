# ?? Agri Plant Disease Detection System

A machine learning-powered web application that detects plant diseases from leaf images, provides pesticide recommendations, and generates detailed treatment reports — with multi-language support for all 28 Indian states.

---

## ?? Features

- ?? **Plant Disease Detection** — Upload a leaf image to identify diseases using trained ML models (SVM, KNN, MLP, Random Forest)
- ?? **Pesticide Recommendations** — State-specific pesticide and treatment guidance based on detected disease
- ?? **PDF Report Generation** — Download detailed disease & treatment reports
- ?? **Multi-language Support** — Supports regional Indian languages via `language_packages.py`
- ?? **AgriBot** — Conversational assistant for agriculture-related queries
- ??? **India Agriculture Database** — Curated crop/pest/disease data for all 28 Indian states

---

## ??? Tech Stack

| Layer | Tools |
|---|---|
| **Backend** | Python, Flask |
| **ML Models** | scikit-learn (SVM, KNN, MLP, Random Forest) |
| **Image Processing** | OpenCV, Pillow |
| **Database** | MongoDB, SQLite |
| **Report Generation** | ReportLab |
| **Frontend** | HTML, CSS, JS (Jinja2 templates) |

---

## ?? Project Structure

```
MP-AGRI/
+-- app.py                          # Main Flask application
+-- train.py                        # Model training script
+-- models.py                       # ML model definitions
+-- features.py                     # Feature extraction utilities
+-- plant_image_preprocessor.py     # Image preprocessing pipeline
+-- disease_formatter.py            # Disease info formatting
+-- treatment_protocols.py          # Treatment & pesticide protocols
+-- agri_bot.py                     # AgriBot chatbot logic
+-- agri_pesticides_db.py           # Pesticides database
+-- india_agri_db.py                # India agriculture database
+-- language_packages.py            # Multi-language support
+-- report_generator.py             # PDF report generator
+-- database.py                     # Database utilities
+-- requirements.txt
+-- class_names.txt                 # Disease class labels
+-- data/
¦   +-- cure.json                   # Treatment data
¦   +-- disease_names.json          # Disease label mappings
¦   +-- india_agriculture.db        # SQLite agriculture database
+-- templates/                      # HTML templates
+-- static/                         # CSS, JS, assets
```

> **Note:** The `models/` folder (trained `.joblib` files) and `dataset/` (54,000+ images) are excluded from this repo due to size. Run `train.py` to regenerate models locally.

---

## ?? Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/Gokulnath33/agri-plant-ml.git
cd agri-plant-ml
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Train models (required before running)
```bash
python train.py
```

This generates all required `.joblib` model files inside the `models/` folder.

### 5. Run the application
```bash
python app.py
```

Visit http://localhost:5000 in your browser.

---

## ?? How It Works

1. User uploads a plant leaf image through the web interface
2. The image is preprocessed and features are extracted
3. The ML models classify the disease
4. The system fetches treatment protocols and pesticide recommendations
5. A downloadable PDF report is generated

---

## ?? Testing

```bash
python test_system_e2e.py
```

---

## ????? Author

**Gokul Nath**
GitHub: https://github.com/Gokulnath33

---

## ?? License

This project is for academic/educational purposes (Mini Project — Semester 5, ML).
