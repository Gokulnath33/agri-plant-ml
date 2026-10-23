"""
database.py
===========
MongoDB interface for ASSPA application.
Performance fixes:
  - Single shared MongoClient (connection pool) — no new TCP handshake per request.
  - Fast PBKDF2-HMAC-SHA256 hashing via hashlib (50k rounds, ~10ms)
    instead of passlib pbkdf2_sha256 (default 29000 rounds + overhead).
  - Backward-compatible: old passlib hashes verified transparently on first login,
    then silently migrated to the fast format.
"""

import hashlib
import hmac
import os
import secrets
from pymongo import MongoClient
from datetime import datetime

# ── Singleton connection pool ──────────────────────────────────────────────────
# MongoClient is thread-safe and manages an internal connection pool.
# Create it ONCE at import time so every request reuses existing sockets.
_client = None
_db_instance = None

def _get_db():
    global _client, _db_instance
    if _db_instance is None:
        try:
            _client = MongoClient(
                "mongodb://localhost:27017/",
                serverSelectionTimeoutMS=3000,  # fail fast if mongo is down
                connectTimeoutMS=3000,
                socketTimeoutMS=5000,
                maxPoolSize=20,           # up to 20 reused sockets
                minPoolSize=2,            # keep 2 warm connections always
            )
            _db_instance = _client["pesticide_app_db"]
        except Exception as e:
            print(f"[DB] Connection error: {e}")
            return None
    return _db_instance


# Keep old name for any code that already calls get_database_connection()
def get_database_connection():
    return _get_db()


# ── Password hashing (fast, built-in hashlib) ──────────────────────────────────
_HASH_ROUNDS = 50_000   # ~10 ms on modest hardware — instant feel, still secure

def _hash_password(password: str) -> str:
    """Hash a plaintext password. Returns 'pbkdf2fast$<hex-salt>$<hex-dk>'."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _HASH_ROUNDS)
    return f"pbkdf2fast${salt.hex()}${dk.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    """Verify plaintext password against stored hash (new or legacy passlib format)."""
    if stored.startswith("pbkdf2fast$"):
        # New fast format
        try:
            _, salt_hex, dk_hex = stored.split("$")
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(dk_hex)
            attempt = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _HASH_ROUNDS)
            return hmac.compare_digest(attempt, expected)
        except Exception:
            return False
    else:
        # Legacy passlib format — try with passlib, then migrate
        try:
            from passlib.hash import pbkdf2_sha256 as _plib
            return _plib.verify(password, stored)
        except Exception:
            return False


# ── User management ────────────────────────────────────────────────────────────

def create_user(user_data):
    """Registers a new farmer/user with extended agricultural and location metadata."""
    db = _get_db()
    if db is None:
        return False, "Database connection failed."

    users_collection = db["users"]
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "").strip()

    if not username or not password:
        return False, "Username and password are required."

    if users_collection.find_one({"username": username}):
        return False, "Username already exists. Please choose a different username."

    hashed_password = _hash_password(password)

    record = {
        "name": user_data.get("name", "").strip(),
        "username": username,
        "password": hashed_password,
        "phone": user_data.get("phone", "").strip(),
        "country": user_data.get("country", "India").strip(),
        "state": user_data.get("state", "").strip(),
        "district": user_data.get("district", "").strip(),
        "crop_field": user_data.get("crop_field", "").strip(),
        "language": user_data.get("language", "ta").strip(),
        "approved": False,
        "created_at": datetime.now().isoformat()
    }

    users_collection.insert_one(record)
    return True, "Registration successful! Your account is pending admin approval."


def verify_user(username, password):
    """Verify credentials. Auto-migrates legacy passlib hashes to fast format."""
    db = _get_db()
    if db is None:
        return False, False, "Database Error", None

    users_collection = db["users"]
    user = users_collection.find_one({"username": username})

    if user:
        stored = user["password"]
        is_valid = _verify_password(password, stored)

        if not is_valid:
            return False, False, "Invalid Credentials", None

        # Silently migrate legacy passlib hash → fast format on successful login
        if not stored.startswith("pbkdf2fast$"):
            new_hash = _hash_password(password)
            users_collection.update_one(
                {"username": username},
                {"$set": {"password": new_hash}}
            )

        is_approved = user.get("approved", False)
        if not is_approved:
            return True, False, "Your account is currently pending administrator approval. Please contact the administrator.", None

        profile = {
            "name": user.get("name", username),
            "username": username,
            "phone": user.get("phone", ""),
            "country": user.get("country", "India"),
            "state": user.get("state", ""),
            "district": user.get("district", ""),
            "crop_field": user.get("crop_field", ""),
            "language": user.get("language", "ta")
        }
        return True, True, "Login Successful", profile

    return False, False, "User not found", None


def update_user_language(username, language):
    """Updates the preferred language for a user."""
    db = _get_db()
    if db is not None:
        db["users"].update_one({"username": username}, {"$set": {"language": language}})
        return True
    return False


def reset_password(username, new_password):
    """Resets the password for an existing user by username."""
    db = _get_db()
    if db is None:
        return False, "Database connection failed."

    users_collection = db["users"]
    user = users_collection.find_one({"username": username})

    if not user:
        return False, "Username not found. Please check your username and try again."

    if not new_password or len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    hashed_password = _hash_password(new_password)
    users_collection.update_one(
        {"username": username},
        {"$set": {"password": hashed_password}}
    )
    return True, "Password has been reset successfully! You can now sign in with your new password."


def ensure_admin_exists():
    db = _get_db()
    if db is not None:
        users = db["users"]
        if not users.find_one({"username": "admin"}):
            users.insert_one({
                "name": "System Administrator",
                "username": "admin",
                "password": _hash_password("admin123"),
                "phone": "+91 98765 43210",
                "country": "India",
                "state": "National",
                "district": "Headquarters",
                "crop_field": "All Crops",
                "language": "en",
                "approved": True,
                "created_at": datetime.now().isoformat()
            })


def get_all_users_stats():
    db = _get_db()
    if db is None:
        return []
    users_collection = db["users"]
    history_collection = db["history"]

    stats = []
    for user in users_collection.find({}, {"password": 0}):
        u_name = user["username"]
        count = history_collection.count_documents({"username": u_name})
        
        raw_created = user.get("created_at", "")
        formatted_datetime = "N/A"
        if raw_created:
            try:
                formatted_datetime = str(raw_created)[:19].replace("T", " ")
            except Exception:
                formatted_datetime = str(raw_created)
        elif "_id" in user and hasattr(user["_id"], "generation_time"):
            try:
                formatted_datetime = user["_id"].generation_time.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        stats.append({
            "name": user.get("name", u_name),
            "username": u_name,
            "phone": user.get("phone", "N/A"),
            "country": user.get("country", "India"),
            "state": user.get("state", "N/A"),
            "district": user.get("district", "N/A"),
            "crop_field": user.get("crop_field", "General Crops"),
            "approved": user.get("approved", False),
            "analysis_count": count,
            "created_at": formatted_datetime,
            "created_date": formatted_datetime[:10] if formatted_datetime != "N/A" else "N/A"
        })
    return stats


def get_pending_users():
    """Returns all users waiting for admin approval."""
    db = _get_db()
    if db is None:
        return []
    users_collection = db["users"]
    cursor = users_collection.find({"approved": False}, {"password": 0}).sort("created_at", -1)
    results = []
    for u in cursor:
        raw_created = u.get("created_at", "")
        formatted_datetime = "N/A"
        if raw_created:
            try:
                formatted_datetime = str(raw_created)[:19].replace("T", " ")
            except Exception:
                formatted_datetime = str(raw_created)
        elif "_id" in u and hasattr(u["_id"], "generation_time"):
            try:
                formatted_datetime = u["_id"].generation_time.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        u_copy = dict(u)
        u_copy["_id"] = str(u["_id"]) if "_id" in u else ""
        u_copy["created_at"] = formatted_datetime
        results.append(u_copy)
    return results


def approve_user(username):
    db = _get_db()
    if db is not None:
        db["users"].update_one({"username": username}, {"$set": {"approved": True}})
        return True
    return False


def delete_user(username):
    """Permanently deletes a farmer account and their scan history. Admin account cannot be deleted."""
    if username == "admin":
        return False, "The master administrator account cannot be deleted."
    db = _get_db()
    if db is None:
        return False, "Database connection failed."

    res = db["users"].delete_one({"username": username})
    if res.deleted_count > 0:
        db["history"].delete_many({"username": username})
        return True, f"User @{username} and all associated scan records were permanently deleted."
    return False, f"User @{username} not found."


def update_user(username, update_data):
    """Updates farmer profile details and credentials by administrator."""
    db = _get_db()
    if db is None:
        return False, "Database connection failed."

    users_collection = db["users"]
    existing = users_collection.find_one({"username": username})
    if not existing:
        return False, f"User @{username} not found."

    fields_to_set = {}
    if "name" in update_data and str(update_data["name"]).strip():
        fields_to_set["name"] = str(update_data["name"]).strip()
    if "phone" in update_data:
        fields_to_set["phone"] = str(update_data["phone"]).strip()
    if "crop_field" in update_data:
        fields_to_set["crop_field"] = str(update_data["crop_field"]).strip()
    if "state" in update_data:
        fields_to_set["state"] = str(update_data["state"]).strip()
    if "district" in update_data:
        fields_to_set["district"] = str(update_data["district"]).strip()
    if "country" in update_data:
        fields_to_set["country"] = str(update_data["country"]).strip()
    if "approved" in update_data:
        fields_to_set["approved"] = bool(update_data["approved"])
    if "new_password" in update_data and str(update_data["new_password"]).strip():
        new_pwd = str(update_data["new_password"]).strip()
        if len(new_pwd) < 4:
            return False, "Password must be at least 4 characters long."
        fields_to_set["password"] = _hash_password(new_pwd)

    if not fields_to_set:
        return False, "No fields provided to update."

    users_collection.update_one({"username": username}, {"$set": fields_to_set})
    return True, f"Farmer @{username} details updated successfully."


def save_prediction_history(username, history_data):
    db = _get_db()
    if db is None:
        return False

    history_collection = db["history"]
    history_data["username"] = username
    history_data["timestamp"] = datetime.now().isoformat()
    history_collection.insert_one(history_data)
    return True


def get_user_history(username):
    db = _get_db()
    if db is None:
        return []

    history_collection = db["history"]
    cursor = history_collection.find({"username": username}, {"_id": 0}).sort("timestamp", -1)
    return list(cursor)


def clear_user_history(username):
    db = _get_db()
    if db is not None:
        db["history"].delete_many({"username": username})
        return True
    return False


def seed_user_sample_data(username):
    """Populates diverse, realistic agricultural scan records for rich user analytics."""
    from datetime import timedelta
    import random

    db = _get_db()
    if db is None:
        return False

    history_collection = db["history"]

    sample_records = [
        {
            "crop": "Tomato", "plant_type": "Tomato", "class_name": "Tomato_Early_blight",
            "disease_name": "Early Blight (Target Spot)", "scientific_name": "Alternaria solani",
            "pathogen_type": "Fungal", "is_healthy": False,
            "severity_tier": "Moderate Stage Infection (15 - 40% leaf area)",
            "confidence": 0.962, "algorithm": "PCA + Multilayer Perceptron (MLP)",
            "pesticide": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC", "amount": "1.0 ml / Liter",
            "precautions": "Avoid overhead watering; prune lower leaves",
            "state": "Tamil Nadu", "district": "Coimbatore", "days_ago": 6
        },
        {
            "crop": "Tomato", "plant_type": "Tomato", "class_name": "Tomato_Late_blight",
            "disease_name": "Late Blight", "scientific_name": "Phytophthora infestans",
            "pathogen_type": "Oomycete / Fungal", "is_healthy": False,
            "severity_tier": "Severe / Advanced Infection (> 40% leaf area)",
            "confidence": 0.985, "algorithm": "PCA + Calibrated SVM",
            "pesticide": "Dimethomorph 50% WP (Acrobat)", "amount": "1.0 g / Liter",
            "precautions": "Emergency isolation; destroy collapsing vines",
            "state": "Tamil Nadu", "district": "Coimbatore", "days_ago": 5
        },
        {
            "crop": "Tomato", "plant_type": "Tomato", "class_name": "Tomato_healthy",
            "disease_name": "Healthy Specimen", "scientific_name": "Solanum lycopersicum",
            "pathogen_type": "Healthy", "is_healthy": True,
            "severity_tier": "Healthy Specimen (Optimal Foliar Vigor)",
            "confidence": 0.991, "algorithm": "PCA + Random Forest (RF)",
            "pesticide": "None required", "amount": "0 ml/L",
            "precautions": "Maintain regular drip irrigation and scout monitoring",
            "state": "Tamil Nadu", "district": "Coimbatore", "days_ago": 4
        },
        {
            "crop": "Potato", "plant_type": "Potato", "class_name": "Potato_Early_blight",
            "disease_name": "Early Blight", "scientific_name": "Alternaria solani",
            "pathogen_type": "Fungal", "is_healthy": False,
            "severity_tier": "Mild / Early Stage Infection (1 - 15% leaf area)",
            "confidence": 0.944, "algorithm": "PCA + Calibrated SVM",
            "pesticide": "Mancozeb 75% WP", "amount": "2.5 g / Liter",
            "precautions": "Foliar misting at first sign of concentric spots",
            "state": "Tamil Nadu", "district": "Nilgiris (Ooty)", "days_ago": 3
        },
        {
            "crop": "Potato", "plant_type": "Potato", "class_name": "Potato_Late_blight",
            "disease_name": "Late Blight", "scientific_name": "Phytophthora infestans",
            "pathogen_type": "Oomycete / Fungal", "is_healthy": False,
            "severity_tier": "Moderate Stage Infection (15 - 40% leaf area)",
            "confidence": 0.973, "algorithm": "PCA + Multilayer Perceptron (MLP)",
            "pesticide": "Metalaxyl 8% + Mancozeb 64% WP", "amount": "2.0 g / Liter",
            "precautions": "Hill up soil around potato ridges",
            "state": "Tamil Nadu", "district": "Nilgiris (Ooty)", "days_ago": 3
        },
        {
            "crop": "Apple", "plant_type": "Apple", "class_name": "Apple_Apple_scab",
            "disease_name": "Apple Scab", "scientific_name": "Venturia inaequalis",
            "pathogen_type": "Fungal", "is_healthy": False,
            "severity_tier": "Moderate Stage Infection (15 - 40% leaf area)",
            "confidence": 0.958, "algorithm": "PCA + Random Forest (RF)",
            "pesticide": "Mancozeb 75% WP / Captan 50% WP", "amount": "2.5 g / Liter",
            "precautions": "Rake up and destroy fallen leaf litter",
            "state": "Himachal Pradesh", "district": "Shimla", "days_ago": 2
        },
        {
            "crop": "Apple", "plant_type": "Apple", "class_name": "Apple_healthy",
            "disease_name": "Healthy Specimen", "scientific_name": "Malus domestica",
            "pathogen_type": "Healthy", "is_healthy": True,
            "severity_tier": "Healthy Specimen (Optimal Foliar Vigor)",
            "confidence": 0.982, "algorithm": "PCA + Calibrated SVM",
            "pesticide": "None required", "amount": "0 ml/L",
            "precautions": "Standard orchard maintenance",
            "state": "Himachal Pradesh", "district": "Shimla", "days_ago": 1
        },
        {
            "crop": "Grape", "plant_type": "Grape", "class_name": "Grape_Black_rot",
            "disease_name": "Black Rot", "scientific_name": "Guignardia bidwellii",
            "pathogen_type": "Fungal", "is_healthy": False,
            "severity_tier": "Mild / Early Stage Infection (1 - 15% leaf area)",
            "confidence": 0.938, "algorithm": "PCA + Multilayer Perceptron (MLP)",
            "pesticide": "Mancozeb 75% WP / Kresoxim-methyl 44.3% SC", "amount": "2.5 g / Liter",
            "precautions": "Prune out mummified shriveled grape bunches",
            "state": "Maharashtra", "district": "Nashik", "days_ago": 0
        }
    ]

    now = datetime.now()
    for rec in sample_records:
        rec_copy = dict(rec)
        days = rec_copy.pop("days_ago", 0)
        rec_copy["username"] = username
        rec_copy["timestamp"] = (now - timedelta(days=days, hours=random.randint(1, 10))).isoformat()
        history_collection.insert_one(rec_copy)

    return True