from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

print("Testing Supabase connection...\n")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"URL: {url}\n")

if not url or not key:
    print("❌ Missing credentials!")
    exit(1)

supabase = create_client(url, key)
print("✅ Supabase client created\n")

# STEP 1: Create transaction
print("STEP 1: Creating transaction...")
print("-" * 60)

transaction_id = str(uuid.uuid4())
transaction_data = {
    "id": transaction_id,
    "warehouse_id": str(uuid.uuid4()),  # Dummy warehouse ID
    "status": "in_progress",
    "started_at": datetime.utcnow().isoformat()
}

print(f"Transaction ID: {transaction_id}")
print(f"Data: {transaction_data}\n")

try:
    tx_response = supabase.table("transactions").insert(transaction_data).execute()
    print("✅ Transaction created!")
    print(f"Response: {tx_response.data}\n")
except Exception as e:
    print(f"❌ Error creating transaction: {e}\n")
    exit(1)

# STEP 2: Create harvest record
print("STEP 2: Creating harvest record...")
print("-" * 60)

harvest_data = {
    "transaction_id": transaction_id,  # ← Reference ke transaction yang baru dibuat
    "grade": "B",
    "sack_color": "yellow",
    "weight_kg": 100.0,
    "detected_by": "camera_ml",
    "detection_confidence": 96.47,
    "recorded_at": datetime.utcnow().isoformat()
}

print(f"Data: {harvest_data}\n")

try:
    harvest_response = supabase.table("harvest_records").insert(harvest_data).execute()
    print("✅ Harvest record created!")
    print(f"Response: {harvest_response.data}\n")
except Exception as e:
    print(f"❌ Error creating harvest record: {e}\n")
    exit(1)

print("="*60)
print("✅ FULL TEST PASSED!")
print("="*60)

