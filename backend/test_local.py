import sys
import os
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🧪 LOCAL TESTING - BetelChain ML Service")
print("=" * 70)

# TEST 1: Configuration Loading
print("\n1️⃣  Testing configuration loading...")
try:
    from config import settings
    print("   ✅ Config loaded")
    print(f"   - ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"   - MODEL_PATH: {settings.model_path}")
    print(f"   - META_PATH: {settings.meta_path}")
    print(f"   - FEATURES_PATH: {settings.features_path}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# TEST 2: File Existence Check
print("\n2️⃣  Checking required files...")
required_files = [
    settings.model_path,
    settings.meta_path,
    settings.features_path
]

all_exist = True
for file_path in required_files:
    exists = os.path.exists(file_path)
    status = "✅" if exists else "❌"
    print(f"   {status} {file_path}: {'EXISTS' if exists else 'MISSING'}")
    if not exists:
        all_exist = False

if not all_exist:
    print("\n   ⚠️  Some files missing!")
    sys.exit(1)

# TEST 3: Model & Detector Loading
print("\n3️⃣  Testing model loading...")
try:
    from models.sack_detector import get_detector
    detector = get_detector(
        settings.model_path,
        settings.meta_path,
        settings.features_path
    )
    print("   ✅ Detector initialized")
    print(f"   - Model type: {type(detector.model).__name__}")
    print(f"   - Classes: {detector.metadata['classes']}")
    print(f"   - Grades: {detector.metadata['grades']}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# TEST 4: Single Feature Extraction (tidak loop)
print("\n4️⃣  Testing single feature extraction...")
try:
    img = np.full((259, 194, 3), (255, 0, 0), dtype=np.uint8)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    features = detector.extract_features_func(img_rgb)
    print(f"   ✅ Feature extraction OK - shape: {features.shape}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# TEST 5: Single Prediction
print("\n5️⃣  Testing single prediction...")
try:
    img = np.full((259, 194, 3), (255, 0, 0), dtype=np.uint8)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = detector.predict(img_rgb)
    print(f"   ✅ Prediction OK")
    print(f"      Grade: {result['grade']}, Confidence: {result['confidence']}%")
    print(f"      Probabilities: {result['probabilities']}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# TEST 6: FastAPI App Loading
print("\n6️⃣  Testing FastAPI app loading...")
try:
    from main import app
    print("   ✅ FastAPI app loaded")
    print(f"   - Title: {app.title}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# TEST 7: Response Schemas
print("\n7️⃣  Testing response schemas...")
try:
    from schemas.detection import DetectionResponse
    
    det_resp = DetectionResponse(
        warna="merah",
        grade="A",
        confidence=95.5,
        probabilities={"merah": 95.5, "kuning": 3.0, "hijau": 1.5},
        detected_at="2025-11-29T10:00:00Z"
    )
    print(f"   ✅ DetectionResponse created: {det_resp.grade} ({det_resp.confidence}%)")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\n📝 Next steps:")
print("   1. Run: python main.py")
print("   2. Test endpoints at: http://localhost:8000/docs")
print("   3. Try POST /api/detect/sack with an image file")
print("\n")

