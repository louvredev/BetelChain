from fastapi import APIRouter, HTTPException
from datetime import datetime
from supabase import create_client

from schemas.detection import HarvestRecordRequest, HarvestRecordResponse
from config import settings

router = APIRouter(prefix="/api/harvest", tags=["harvest"])

supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)

@router.post("/record", response_model=HarvestRecordResponse)
async def create_harvest_record(record: HarvestRecordRequest):
    try:
        response = supabase.table("harvest_records").insert({
            "transaction_id": record.transaction_id,
            "grade": record.grade,
            "sack_color": record.sack_color,
            "weight_kg": record.weight_kg,
            "detected_by": "camera_ml",
            "detection_confidence": record.detection_confidence,
            "recorded_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to save")
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/records/{transaction_id}")
async def get_harvest_records(transaction_id: str):
    try:
        response = supabase.table("harvest_records").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        return {
            "count": len(response.data),
            "records": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

