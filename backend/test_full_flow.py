import requests
import json
import uuid

BASE_URL = "http://localhost:8000"
IMAGE_PATH = "/home/achlismy/Downloads/kuning22.jpeg"

print("\n" + "="*60)
print("FULL FLOW TEST")
print("="*60)

# STEP 0: CREATE TRANSACTION
print("\n0️⃣ CREATE TRANSACTION")
print("-" * 60)

transaction_id = str(uuid.uuid4())
from datetime import datetime

# Assume transaction sudah ada di DB (atau buat via API jika ada)
# Untuk sekarang, gunakan UUID yang valid
print(f"Transaction ID: {transaction_id}\n")

# STEP 1: DETECT
print("1️⃣ DETECT IMAGE")
print("-" * 60)

with open(IMAGE_PATH, "rb") as f:
    files = {"file": f}
    detect_response = requests.post(f"{BASE_URL}/api/detect/sack", files=files)

print(f"Status: {detect_response.status_code}")
detect_result = detect_response.json()
print(json.dumps(detect_result, indent=2))

# Extract results
warna_map = {"merah": "red", "kuning": "yellow", "hijau": "green"}
sack_color = warna_map[detect_result["warna"]]
grade = detect_result["grade"]
confidence = detect_result["confidence"]

# STEP 2: SAVE TO SUPABASE
print("\n2️⃣ SAVE TO SUPABASE")
print("-" * 60)

harvest_data = {
    "transaction_id": transaction_id,  # ← Gunakan transaction yang sudah ada
    "grade": grade,
    "sack_color": sack_color,
    "weight_kg": 100.0,
    "detection_confidence": confidence
}

print(f"Payload:")
print(json.dumps(harvest_data, indent=2))

harvest_response = requests.post(
    f"{BASE_URL}/api/harvest/record",
    json=harvest_data
)

print(f"\nStatus: {harvest_response.status_code}")
harvest_result = harvest_response.json()
print(json.dumps(harvest_result, indent=2))

# STEP 3: QUERY RESULTS
print("\n3️⃣ QUERY RESULTS")
print("-" * 60)

query_response = requests.get(f"{BASE_URL}/api/harvest/records/{transaction_id}")
print(f"Status: {query_response.status_code}")
print(json.dumps(query_response.json(), indent=2))

# STEP 4: GET STATS
print("\n4️⃣ STATISTICS")
print("-" * 60)

stats_response = requests.get(f"{BASE_URL}/api/harvest/stats")
print(json.dumps(stats_response.json(), indent=2))

print("\n" + "="*60)
print("✅ FULL FLOW COMPLETE!")
print("="*60 + "\n")

