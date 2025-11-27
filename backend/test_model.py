import numpy as np
import cv2

print("Testing feature extraction...\n")

# 1. Create dummy image
print("1️⃣ Creating dummy image...")
dummy_img = np.random.randint(0, 255, (259, 194, 3), dtype=np.uint8)
print(f"   ✅ Image shape: {dummy_img.shape}, dtype: {dummy_img.dtype}\n")

# 2. Test resize
print("2️⃣ Testing resize...")
img_resized = cv2.resize(dummy_img, (128, 128))
print(f"   ✅ Resized shape: {img_resized.shape}\n")

# 3. Test RGB features
print("3️⃣ Testing RGB features...")
mean_rgb = img_resized.mean(axis=(0, 1)).astype(np.float32)
std_rgb = img_resized.std(axis=(0, 1)).astype(np.float32)
print(f"   ✅ Mean RGB: {mean_rgb}")
print(f"   ✅ Std RGB: {std_rgb}\n")

# 4. Test HSV conversion
print("4️⃣ Testing HSV conversion...")
try:
    hsv = cv2.cvtColor(img_resized, cv2.COLOR_RGB2HSV)
    print(f"   ✅ HSV shape: {hsv.shape}\n")
except Exception as e:
    print(f"   ❌ HSV conversion failed: {e}\n")
    exit(1)

# 5. Test HSV features
print("5️⃣ Testing HSV features...")
mean_hsv = hsv.mean(axis=(0, 1)).astype(np.float32)
std_hsv = hsv.std(axis=(0, 1)).astype(np.float32)
print(f"   ✅ Mean HSV: {mean_hsv}")
print(f"   ✅ Std HSV: {std_hsv}\n")

# 6. Test histograms
print("6️⃣ Testing histograms...")
try:
    hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180]).flatten().astype(np.float32)
    hist_h = hist_h / (hist_h.sum() + 1e-7)
    print(f"   ✅ Hist H shape: {hist_h.shape}")
    
    hist_s = cv2.calcHist([hsv], [1], None, [16], [0, 256]).flatten().astype(np.float32)
    hist_s = hist_s / (hist_s.sum() + 1e-7)
    print(f"   ✅ Hist S shape: {hist_s.shape}")
    
    hist_v = cv2.calcHist([hsv], [2], None, [8], [0, 256]).flatten().astype(np.float32)
    hist_v = hist_v / (hist_v.sum() + 1e-7)
    print(f"   ✅ Hist V shape: {hist_v.shape}\n")
except Exception as e:
    print(f"   ❌ Histogram failed: {e}\n")
    exit(1)

# 7. Concatenate features
print("7️⃣ Concatenating features...")
try:
    features = np.concatenate([
        mean_rgb, std_rgb, mean_hsv, std_hsv,
        hist_h, hist_s, hist_v
    ]).astype(np.float32)
    print(f"   ✅ Final features shape: {features.shape}")
    print(f"   ✅ Features dtype: {features.dtype}\n")
except Exception as e:
    print(f"   ❌ Concatenation failed: {e}\n")
    exit(1)

print("✅ ALL TESTS PASSED!")

