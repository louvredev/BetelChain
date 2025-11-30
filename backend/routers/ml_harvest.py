from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form
from datetime import datetime
from supabase import create_client, Client
from typing import Optional
import uuid

from schemas.detection import HarvestRecordResponse
from models.sack_detector import get_detector
from config import settings

router = APIRouter(prefix="/api/ml-harvest", tags=["ml-harvest"])

def get_supabase_client() -> Client:
    """Lazy initialize Supabase client"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase configuration is missing"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@router.post("/detect-and-save", response_model=HarvestRecordResponse)
async def detect_sack_and_save(
    file: UploadFile = File(...),
    transaction_id: str = Form(...),
    x_warehouse_id: str = Header(...)
):
    """
    Detect warna karung + grade dari image, langsung simpan ke harvest_records
    
    Form data:
    - file: Image file (JPG/PNG)
    - transaction_id: ID transaction yang sedang berlangsung
    
    Flow:
    1. Load model & detect
    2. Validate transaction exists & belongs to warehouse
    3. Save ke harvest_records
    4. Return saved record
    """
    try:
        supabase = get_supabase_client()
        
        # Step 1: Validate transaction exists & belongs to this warehouse
        txn_check = supabase.table("transactions").select("id, warehouse_id").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        
        # Check warehouse authorization
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized for this transaction")
        
                # Step 2: Read file & detect
        file_content = await file.read()

        try:
            detector = get_detector(
                settings.model_path,
                settings.meta_path,
                settings.features_path
            )

            # Decode bytes -> image (BGR) -> RGB
            import numpy as np
            import cv2

            nparr = np.frombuffer(file_content, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise ValueError("Failed to decode image")

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # Panggil model.predict
            detection_result = detector.predict(img_rgb)

            # Extract detection data
            warna = detection_result.get("warna", "unknown")
            grade = detection_result.get("grade", "C")
            confidence = detection_result.get("confidence", 0.0)

        except Exception as e:
            print(f"Error during detection: {e}")
            raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
        
        # Map warna to sack_color
        color_map = {
            "merah": "red",
            "kuning": "yellow",
            "hijau": "green",
            "red": "red",
            "yellow": "yellow",
            "green": "green"
        }
        sack_color = color_map.get(warna.lower(), warna.lower())
        
        # Step 3: Save to harvest_records
        harvest_record = {
            "id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "grade": grade,
            "sack_color": sack_color,
            "weight_kg": 100.0,  # Default weight, bisa di-update nanti
            "detection_confidence": float(confidence),
            "recorded_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("harvest_records").insert(harvest_record).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to save harvest record")
        
        data = response.data[0]
        return HarvestRecordResponse(
            id=data["id"],
            transaction_id=data["transaction_id"],
            grade=data["grade"],
            sack_color=data["sack_color"],
            weight_kg=data["weight_kg"],
            detection_confidence=data["detection_confidence"],
            recorded_at=data["recorded_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in detect_and_save: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-detect", response_model=dict)
async def batch_detect_and_save(
    files: list[UploadFile] = File(...),
    transaction_id: str = Form(...),
    x_warehouse_id: str = Header(...)
):
    """
    Detect & save MULTIPLE gambar sekaligus untuk satu transaction
    
    Useful untuk scanning multiple sacks dalam satu batch
    """
    try:
        supabase = get_supabase_client()
        
        # Validate transaction
        txn_check = supabase.table("transactions").select("id, warehouse_id").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized for this transaction")
        
        # Process each file
        saved_records = []
        errors = []
        
        for file in files:
            try:
                file_content = await file.read()

                detector = get_detector(
                    settings.model_path,
                    settings.meta_path,
                    settings.features_path
                )

                import numpy as np
                import cv2

                nparr = np.frombuffer(file_content, np.uint8)
                img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img_bgr is None:
                    raise ValueError("Failed to decode image")

                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

                detection_result = detector.predict(img_rgb)

                warna = detection_result.get("warna", "unknown")
                grade = detection_result.get("grade", "C")
                confidence = detection_result.get("confidence", 0.0)

                
                color_map = {
                    "merah": "red",
                    "kuning": "yellow",
                    "hijau": "green",
                    "red": "red",
                    "yellow": "yellow",
                    "green": "green"
                }
                sack_color = color_map.get(warna.lower(), warna.lower())
                
                harvest_record = {
                    "id": str(uuid.uuid4()),
                    "transaction_id": transaction_id,
                    "grade": grade,
                    "sack_color": sack_color,
                    "weight_kg": 100.0,
                    "detection_confidence": float(confidence),
                    "recorded_at": datetime.utcnow().isoformat(),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                response = supabase.table("harvest_records").insert(harvest_record).execute()
                
                if response.data:
                    saved_records.append({
                        "filename": file.filename,
                        "grade": grade,
                        "sack_color": sack_color,
                        "confidence": confidence,
                        "status": "success"
                    })
                else:
                    errors.append({"filename": file.filename, "error": "Failed to save"})
                    
            except Exception as e:
                errors.append({"filename": file.filename, "error": str(e)})
        
        return {
            "transaction_id": transaction_id,
            "total_files": len(files),
            "successful": len(saved_records),
            "failed": len(errors),
            "saved_records": saved_records,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in batch_detect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{transaction_id}/harvest-summary", response_model=dict)
async def get_harvest_summary(transaction_id: str):
    """
    Get summary dari harvest records untuk satu transaction
    Berguna untuk lihat total karung, grade breakdown, confidence average
    """
    try:
        supabase = get_supabase_client()
        
        # Get transaction
        txn_check = supabase.table("transactions").select("*").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get harvest records
        harvest_response = supabase.table("harvest_records").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        records = harvest_response.data or []
        
        if not records:
            return {
                "transaction_id": transaction_id,
                "total_sacks": 0,
                "total_weight_kg": 0,
                "grade_breakdown": {"A": 0, "B": 0, "C": 0},
                "confidence_avg": 0,
                "records": []
            }
        
        total_weight = sum(float(r["weight_kg"]) for r in records)
        total_sacks = len(records)
        
        grade_breakdown = {
            "A": len([r for r in records if r["grade"] == "A"]),
            "B": len([r for r in records if r["grade"] == "B"]),
            "C": len([r for r in records if r["grade"] == "C"])
        }
        
        confidence_avg = sum(float(r["detection_confidence"]) for r in records) / total_sacks
        
        return {
            "transaction_id": transaction_id,
            "total_sacks": total_sacks,
            "total_weight_kg": round(total_weight, 2),
            "grade_breakdown": grade_breakdown,
            "confidence_avg": round(confidence_avg, 2),
            "records": records
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in harvest_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))