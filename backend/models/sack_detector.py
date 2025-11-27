import dill
import numpy as np
from pathlib import Path
import os

class SackColorSVM:
    """
    Wrapper untuk model SVM dari Colab
    Menggunakan dill.load untuk unpickle model + fungsi
    """
    def __init__(self, package_path: str):
        if not os.path.exists(package_path):
            raise FileNotFoundError(f"Model file not found: {package_path}")
        
        print(f"Loading model from {package_path}...")
        with open(package_path, "rb") as f:
            pkg = dill.load(f)
        
        self.model = pkg["model"]
        self.extract_features = pkg["extract_features"]
        self.classes = pkg["classes"]  # ['merah', 'kuning', 'hijau']
        self.grades = pkg["grades"]    # ['A', 'B', 'C']
        print("✅ Model loaded successfully!")
    
    def predict(self, img_rgb: np.ndarray):
        """
        Predict warna karung dari image RGB
        
        Args:
            img_rgb: numpy array RGB format (height, width, 3)
        
        Returns:
            dict: {
                'warna': 'merah'/'kuning'/'hijau',
                'grade': 'A'/'B'/'C',
                'confidence': float (0-100),
                'probabilities': dict
            }
        """
        try:
            # Extract features V2 (68 dimensi)
            features = self.extract_features(img_rgb).reshape(1, -1)
            
            # Predict
            prediction_idx = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            
            # Get results
            warna = self.classes[prediction_idx]
            grade = self.grades[prediction_idx]
            confidence = probabilities[prediction_idx] * 100
            
            # Get all probabilities
            prob_dict = {
                self.classes[i]: round(probabilities[i] * 100, 2)
                for i in range(len(self.classes))
            }
            
            return {
                "warna": warna,
                "grade": grade,
                "confidence": round(confidence, 2),
                "probabilities": prob_dict
            }
        except Exception as e:
            raise ValueError(f"Prediction error: {str(e)}")

# Singleton
_detector = None

def get_detector(model_path: str):
    global _detector
    if _detector is None:
        _detector = SackColorSVM(model_path)
    return _detector

