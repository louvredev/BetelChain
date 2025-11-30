from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional
import uuid
import secrets

from schemas.betelchain import FarmerResponse
from config import settings

router = APIRouter(prefix="/api/farmers", tags=["farmers"])

def get_supabase_client() -> Client:
    """Lazy initialize Supabase client"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase configuration is missing"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def generate_farmer_code(warehouse_id: str) -> str:
    """
    Generate unique farmer code: F{YYYYMMDD}{RANDOM}
    - Contoh: F20251130A1B2C3
    """
    today = datetime.utcnow().strftime("%Y%m%d")
    # 6 karakter hex acak → 16^6 kemungkinan
    rand = secrets.token_hex(3).upper()
    return f"F{today}{rand}"


class FarmerRegisterRequest(BaseModel):
    full_name: str
    phone: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder_name: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None


class FarmerResponse(BaseModel):
    id: str
    farmer_code: str
    full_name: str
    phone: str
    registered_by_warehouse: str


@router.post("/register", response_model=FarmerResponse)
async def register_farmer(
    farmer: FarmerRegisterRequest,
    x_warehouse_id: str = Header(...)
):
    """
    Warehouse register farmer baru
    
    Request:
    - full_name: Nama petani
    - phone: Nomor telepon
    - (optional fields: bank details, address, etc)
    """
    try:
        supabase = get_supabase_client()
        
        # Validate warehouse exists
        warehouse_check = supabase.table("warehouses").select("id").eq(
            "id", x_warehouse_id
        ).execute()
        
        if not warehouse_check.data:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        # Auto-generate farmer code
        farmer_code = generate_farmer_code(x_warehouse_id)
        
        # Create farmer
        response = supabase.table("farmers").insert({
            "id": str(uuid.uuid4()),
            "farmer_code": farmer_code,
            "full_name": farmer.full_name,
            "phone": farmer.phone,
            "bank_name": farmer.bank_name,
            "account_number": farmer.account_number,
            "account_holder_name": farmer.account_holder_name,
            "address": farmer.address,
            "village": farmer.village,
            "district": farmer.district,
            "city": farmer.city,
            "province": farmer.province,
            "registered_by_warehouse": x_warehouse_id,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to register farmer")
        
        data = response.data[0]
        return FarmerResponse(
            id=data["id"],
            farmer_code=data["farmer_code"],
            full_name=data["full_name"],
            phone=data["phone"],
            registered_by_warehouse=data["registered_by_warehouse"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error registering farmer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{farmer_id}", response_model=FarmerResponse)
async def get_farmer(farmer_id: str):
    """Get detail farmer"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("farmers").select("*").eq(
            "id", farmer_id
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        data = response.data[0]
        return FarmerResponse(
            id=data["id"],
            farmer_code=data["farmer_code"],
            full_name=data["full_name"],
            phone=data["phone"],
            registered_by_warehouse=data["registered_by_warehouse"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching farmer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warehouse/{warehouse_id}/list")
async def list_farmers(warehouse_id: str):
    """Get semua farmers dari satu warehouse"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("farmers").select("*").eq(
            "registered_by_warehouse", warehouse_id
        ).execute()
        
        return {
            "warehouse_id": warehouse_id,
            "count": len(response.data),
            "farmers": response.data
        }
    
    except Exception as e:
        print(f"Error fetching farmers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{farmer_id}/update")
async def update_farmer(
    farmer_id: str,
    farmer: FarmerRegisterRequest,
    x_warehouse_id: str = Header(...)
):
    """Update farmer data"""
    try:
        supabase = get_supabase_client()
        
        # Check farmer exists
        farmer_check = supabase.table("farmers").select("*").eq(
            "id", farmer_id
        ).execute()
        
        if not farmer_check.data:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        existing_farmer = farmer_check.data[0]
        
        # Verify warehouse authorization
        if existing_farmer["registered_by_warehouse"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this farmer")
        
        # Update farmer
        response = supabase.table("farmers").update({
            "full_name": farmer.full_name,
            "phone": farmer.phone,
            "bank_name": farmer.bank_name,
            "account_number": farmer.account_number,
            "account_holder_name": farmer.account_holder_name,
            "address": farmer.address,
            "village": farmer.village,
            "district": farmer.district,
            "city": farmer.city,
            "province": farmer.province,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", farmer_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to update farmer")
        
        data = response.data[0]
        return FarmerResponse(
            id=data["id"],
            farmer_code=data["farmer_code"],
            full_name=data["full_name"],
            phone=data["phone"],
            registered_by_warehouse=data["registered_by_warehouse"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating farmer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
