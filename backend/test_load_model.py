# test_load_model.py
import joblib
import json
import numpy as np
import cv2

print("Testing full model...\n")

# Load model
print("1️⃣ Loading model...")
model = joblib.load("models/model_svm_karung.joblib")
print("   ✅ Model loaded\n")

# Load metadata
print("2️⃣ Loading metadata...")
with open("models/model_meta.json", "r") as f:
    meta = json.load(f)
classes = meta["classes"]
grades = meta["grades"]
print(f"   ✅ Classes: {classes}")
print(f"   ✅ Grades: {grades}\n")

# Create dummy image
print("3️⃣ Creating dummy image...")
dummy_img = np.random.randint(0, 255, (259, 194, 3), dtype=np.uint8)
print(f"   ✅ Image shape: {dummy_img.shape}\n")

# Extract features
print("4️⃣ Extracting features...")
from models.sack_detector import extract_features_v2
features = extract_features_v2(dummy_img)
print(f"   ✅ Features shape: {features.shape}\n")

# Predict
print("5️⃣ Predicting...")
result = model.predict(features.reshape(1, -1))
probs = model.predict_proba(features.reshape(1, -1))
print(f"   ✅ Prediction: {result[0]} ({classes[result[0]]})")
print(f"   ✅ Probabilities: {probs[0]}\n")

print("✅ ALL OK!")

