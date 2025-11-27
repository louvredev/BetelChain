import joblib
import json
import numpy as np
import cv2
import os

def extract_features_v2(image):
    """Manual feature extractor"""
    img_resized = cv2.resize(image, (128, 128))
    
    mean_rgb = img_resized.mean(axis=(0, 1)).astype(np.float32)
    std_rgb = img_resized.std(axis=(0, 1)).astype(np.float32)
    
    hsv = cv2.cvtColor(img_resized, cv2.COLOR_RGB2HSV)
    mean_hsv = hsv.mean(axis=(0, 1)).astype(np.float32)
    std_hsv = hsv.std(axis=(0, 1)).astype(np.float32)
    
    hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180]).flatten().astype(np.float32)
    hist_h = hist_h / (hist_h.sum() + 1e-7)
    
    hist_s = cv2.calcHist([hsv], [1], None, [16], [0, 256]).flatten().astype(np.float32)
    hist_s = hist_s / (hist_s.sum() + 1e-7)
    
    hist_v = cv2.calcHist([hsv], [2], None, [8], [0, 256]).flatten().astype(np.float32)
    hist_v = hist_v / (hist_v.sum() + 1e-7)
    
    features = np.concatenate([
        mean_rgb, std_rgb, mean_hsv, std_hsv,
        hist_h, hist_s, hist_v
    ]).astype(np.float32)
    
    return features

class SackColorSVM:
    def __init__(self, model_path: str, meta_path: str):
        print(f"🔄 Loading model from {model_path}...")
        self.model = joblib.load(model_path)
        print("   ✅ Model loaded")
        
        print(f"🔄 Loading metadata from {meta_path}...")
        with open(meta_path, "r") as f:
            meta = json.load(f)
        self.classes = meta["classes"]
        self.grades = meta["grades"]
        print("   ✅ Metadata loaded")
        
        print("✅ SVM detector ready!")
    
    def predict(self, img_rgb: np.ndarray):
        features = extract_features_v2(img_rgb).reshape(1, -1)
        pred_idx = int(self.model.predict(features)[0])
        probs = self.model.predict_proba(features)[0]
        
        warna = self.classes[pred_idx]
        grade = self.grades[pred_idx]
        confidence = float(probs[pred_idx] * 100)
        
        prob_dict = {
            self.classes[i]: round(float(probs[i]) * 100, 2)
            for i in range(len(self.classes))
        }
        
        return {
            "warna": warna,
            "grade": grade,
            "confidence": round(confidence, 2),
            "probabilities": prob_dict
        }

_detector = None

def get_detector(model_path: str, meta_path: str):
    global _detector
    if _detector is None:
        _detector = SackColorSVM(model_path, meta_path)
    return _detector

