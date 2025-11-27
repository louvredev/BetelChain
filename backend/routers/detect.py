from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from datetime import datetime
import os

from schemas.detection import DetectionResponse
from models.sack_detector import get_detector
from config import settings

router = APIRouter(prefix="/api/detect", tags=["detection"])

@router.post("/sack", response_model=DetectionResponse)
async def detect_sack(file: UploadFile = File(...)):
    """
    Detect sack color dari uploaded image
    
    ### Input:
    - file: Image file (JPEG/PNG)
    
    ### Output:
    ```
    {
      "warna": "merah",
      "grade": "A",
      "confidence": 95.5,
      "probabilities": {
        "merah": 95.5,
        "kuning": 3.2,
        "hijau": 1.3
      },
      "detected_at": "2025-11-26T16:00:00Z"
    }
    ```
    """
    try:
        # Validasi file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Read & decode image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Failed to decode image")
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Load detector & predict
        detector = get_detector(settings.model_path)
        result = detector.predict(img_rgb)
        
        return DetectionResponse(
            **result,
            detected_at=datetime.utcnow().isoformat() + "Z"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/sack-base64", response_model=DetectionResponse)
async def detect_sack_base64(data: dict):
    """
    Detect sack color dari base64 image
    
    ### Input:
    ```
    {
      "image": "data:image/jpeg;base64,..."
    }
    ```
    """
    try:
        if "image" not in data:
            raise HTTPException(status_code=400, detail="Missing 'image' field")
        
        base64_str = data["image"]
        
        # Remove data URL prefix if exists
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        
        # Decode
        import base64
        image_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Predict
        detector = get_detector(settings.model_path)
        result = detector.predict(img_rgb)
        
        return DetectionResponse(
            **result,
            detected_at=datetime.utcnow().isoformat() + "Z"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        detector = get_detector(settings.model_path)
        return {
            "status": "healthy",
            "model_loaded": detector is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }

