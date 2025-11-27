from fastapi import APIRouter, File, UploadFile, HTTPException
from datetime import datetime
import cv2
import numpy as np

from schemas.detection import DetectionResponse
from models.sack_detector import get_detector
from config import settings

router = APIRouter(prefix="/api/detect", tags=["detection"])

@router.post("/sack", response_model=DetectionResponse)
async def detect_sack(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        print(f"\n📤 File: {file.filename}")
        contents = await file.read()
        
        if not contents:
            raise HTTPException(status_code=400, detail="File empty")
        
        print(f"   Size: {len(contents)} bytes")
        
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        print(f"   Decoded: {img.shape}")
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        print(f"   🔍 Detecting...")
        detector = get_detector(
            settings.model_path,
            settings.meta_path
        )
        result = detector.predict(img_rgb)
        
        print(f"   ✅ Result: {result['warna']} ({result['grade']}) - {result['confidence']}%\n")
        
        return DetectionResponse(
            **result,
            detected_at=datetime.utcnow().isoformat() + "Z"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sack-base64", response_model=DetectionResponse)
async def detect_sack_base64(data: dict):
    try:
        if "image" not in data:
            raise HTTPException(status_code=400, detail="Missing 'image' field")
        
        base64_str = data["image"]
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        
        import base64
        image_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        detector = get_detector(
            settings.model_path,
            settings.meta_path
        )
        result = detector.predict(img_rgb)
        
        return DetectionResponse(
            **result,
            detected_at=datetime.utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

