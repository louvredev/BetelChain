from pydantic import BaseModel
from typing import Dict, Optional

class DetectionResponse(BaseModel):
    warna: str
    grade: str
    confidence: float
    probabilities: Dict[str, float]
    detected_at: Optional[str] = None

class HarvestRecordRequest(BaseModel):
    transaction_id: str
    grade: str
    sack_color: str
    weight_kg: float = 100.0
    detection_confidence: float

class HarvestRecordResponse(BaseModel):
    id: str
    transaction_id: str
    grade: str
    sack_color: str
    weight_kg: float
    detection_confidence: float
    recorded_at: str

