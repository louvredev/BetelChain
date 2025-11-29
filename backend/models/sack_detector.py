import joblib
import json
import numpy as np
import cv2
import os
from typing import Dict, Optional

class SackColorSVM:
    def __init__(self, model_path: str, meta_path: str, features_path: Optional[str] = None):
        self.model = None
        self.metadata = None
        self.extract_features_func = None
        
        self._load_model(model_path)
        self._load_metadata(meta_path)
        self._load_feature_extractor(features_path)
    
    def _load_model(self, model_path: str):
        try:
            if not os.path.isabs(model_path):
                model_path = os.path.join(os.getcwd(), model_path)
            
            print(f"🔄 Loading model from {model_path}...")
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            self.model = joblib.load(model_path)
            print("   ✅ Model loaded")
        except Exception as e:
            print(f"   ❌ Error loading model: {e}")
            raise
    
    def _load_metadata(self, meta_path: str):
        try:
            if not os.path.isabs(meta_path):
                meta_path = os.path.join(os.getcwd(), meta_path)
            
            print(f"🔄 Loading metadata from {meta_path}...")
            
            if not os.path.exists(meta_path):
                raise FileNotFoundError(f"Metadata file not found: {meta_path}")
            
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
            
            print("   ✅ Metadata loaded")
            print(f"   - Classes: {self.metadata['classes']}")
            print(f"   - Grades: {self.metadata['grades']}")
        except Exception as e:
            print(f"   ❌ Error loading metadata: {e}")
            raise
    
    def _load_feature_extractor(self, features_path: Optional[str]):
        # For now, use manual implementation (skip .dill)
        print("🔄 Using manual feature extraction...")
        self.extract_features_func = extract_features_v2_fallback
        print("   ✅ Manual feature extractor ready")
    
    def predict(self, img_rgb: np.ndarray) -> Dict:
        try:
            features = self.extract_features_func(img_rgb).reshape(1, -1)
            pred_idx = int(self.model.predict(features)[0])
            probs = self.model.predict_proba(features)[0]
            
            warna = self.metadata["classes"][pred_idx]
            grade = self.metadata["grades"][pred_idx]
            confidence = float(probs[pred_idx] * 100)
            
            prob_dict = {
                self.metadata["classes"][i]: round(float(probs[i]) * 100, 2)
                for i in range(len(self.metadata["classes"]))
            }
            
            return {
                "warna": warna,
                "grade": grade,
                "confidence": round(confidence, 2),
                "probabilities": prob_dict
            }
        
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            raise


def extract_features_v2_fallback(image: np.ndarray) -> np.ndarray:
    try:
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8) if image.max() <= 1 else image.astype(np.uint8)
        
        img_resized = cv2.resize(image, (128, 128))
        
        mean_rgb = img_resized.mean(axis=(0, 1)).astype(np.float32)
        std_rgb = img_resized.std(axis=(0, 1)).astype(np.float32)
        
        try:
            hsv = cv2.cvtColor(img_resized, cv2.COLOR_RGB2HSV)
        except:
            hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
        
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
    
    except Exception as e:
        print(f"Error in feature extraction: {e}")
        raise


_detector = None

def get_detector(model_path: str, meta_path: str, features_path: Optional[str] = None) -> SackColorSVM:
    global _detector
    if _detector is None:
        _detector = SackColorSVM(model_path, meta_path, features_path)
    return _detector

