import sys
import os
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("Testing basic imports...")
try:
    from config import settings
    from models.sack_detector import get_detector
    print("✅ Imports OK")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("\nTesting detector initialization...")
try:
    detector = get_detector(
        settings.model_path,
        settings.meta_path,
        settings.features_path
    )
    print("✅ Detector initialized")
except Exception as e:
    print(f"❌ Initialization error: {e}")
    sys.exit(1)

print("\nTesting if extract_features_func is callable...")
try:
    func = detector.extract_features_func
    print(f"✅ Function loaded: {func}")
    print(f"   Type: {type(func)}")
    print(f"   Module: {func.__module__ if hasattr(func, '__module__') else 'N/A'}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\nTesting simple numpy operation...")
try:
    img = np.full((259, 194, 3), (255, 0, 0), dtype=np.uint8)
    print(f"✅ Image created: {img.shape}, dtype: {img.dtype}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\nTesting cv2.cvtColor...")
try:
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print(f"✅ Converted to RGB: {img_rgb.shape}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\nTesting resize...")
try:
    img_resized = cv2.resize(img_rgb, (128, 128))
    print(f"✅ Resized: {img_resized.shape}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\nTesting mean calculation...")
try:
    mean_rgb = img_resized.mean(axis=(0, 1)).astype(np.float32)
    print(f"✅ Mean RGB: {mean_rgb}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n✅ ALL BASIC TESTS PASSED")

