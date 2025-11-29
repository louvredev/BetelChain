from fastapi import APIRouter, HTTPException
from datetime import datetime
from supabase import create_client, Client

from schemas.detection import HarvestRecordRequest, HarvestRecordResponse
from config import settings

router = APIRouter(prefix="/api/harvest", tags=["harvest"])

def get_supabase_client() -> Client:
    """Lazy initialize Supabase client - error jika URL tidak set"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase configuration is missing"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@router.post("/record", response_model=HarvestRecordResponse)
async def create_harvest_record(record: HarvestRecordRequest):
    """
    Record hasil deteksi karung ke harvest_records table
    """
    try:
        supabase = get_supabase_client()
        
        # Validate transaction exists
        txn_check = supabase.table("transactions").select("id").eq(
            "id", str(record.transaction_id)
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Map warna to sack_color
        color_map = {
            "merah": "red",
            "kuning": "yellow",
            "hijau": "green"
        }
        sack_color = color_map.get(record.sack_color, record.sack_color)
        
        # Insert harvest record
        response = supabase.table("harvest_records").insert({
            "transaction_id": str(record.transaction_id),
            "grade": record.grade,
            "sack_color": sack_color,
            "weight_kg": record.weight_kg,
            "detected_by": "camera_ml",
            "detection_confidence": record.detection_confidence,
            "recorded_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to save record")
        
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
        print(f"Error creating harvest record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/{transaction_id}")
async def get_harvest_records(transaction_id: str):
    """Get semua harvest records untuk satu transaction"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("harvest_records").select("*").eq(
            "transaction_id", transaction_id
        ).order("recorded_at", desc=False).execute()
        
        return {
            "transaction_id": transaction_id,
            "count": len(response.data),
            "records": response.data
        }
    except Exception as e:
        print(f"Error fetching harvest records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{transaction_id}/summary")
async def get_transaction_summary(transaction_id: str):
    """Get summary untuk transaction"""
    try:
        supabase = get_supabase_client()
        
        records = supabase.table("harvest_records").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        if not records.data:
            return {
                "transaction_id": transaction_id,
                "total_weight_kg": 0,
                "total_sacks": 0,
                "grade_breakdown": {"A": 0, "B": 0, "C": 0},
                "confidence_avg": 0
            }
        
        data = records.data
        total_weight = sum(float(r["weight_kg"]) for r in data)
        total_sacks = len(data)
        grade_breakdown = {
            "A": len([r for r in data if r["grade"] == "A"]),
            "B": len([r for r in data if r["grade"] == "B"]),
            "C": len([r for r in data if r["grade"] == "C"])
        }
        confidence_avg = sum(float(r["detection_confidence"]) for r in data) / total_sacks
        
        return {
            "transaction_id": transaction_id,
            "total_weight_kg": round(total_weight, 2),
            "total_sacks": total_sacks,
            "grade_breakdown": grade_breakdown,
            "confidence_avg": round(confidence_avg, 2)
        }
    except Exception as e:
        print(f"Error fetching transaction summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/transaction/{transaction_id}/complete")
async def complete_recording(transaction_id: str):
    """Mark recording sebagai completed"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("transactions").update({
            "recording_status": "completed",
            "recording_completed_at": datetime.utcnow().isoformat()
        }).eq("id", transaction_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "success": True,
            "message": "Recording completed",
            "transaction_id": transaction_id
        }
    except Exception as e:
        print(f"Error completing recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

