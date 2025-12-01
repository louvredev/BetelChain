from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional
from schemas.betelchain import TransactionCreateRequest, TransactionResponse
import uuid

from config import settings

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

def get_supabase_client() -> Client:
    """Lazy initialize Supabase client"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase configuration is missing"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def generate_transaction_code() -> str:
    """Generate unique transaction code: TXN{YYYYMMDD}{SEQUENCE}"""
    try:
        supabase = get_supabase_client()
        today = datetime.utcnow().strftime("%Y%m%d")
        
        response = supabase.table("transactions").select("id").like(
            "transaction_code", f"TXN{today}%"
        ).execute()
        
        sequence = len(response.data) + 1
        transaction_code = f"TXN{today}{sequence:04d}"
        
        return transaction_code
    except Exception as e:
        print(f"Error generating transaction code: {e}")
        return f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


class TransactionCreateRequest(BaseModel):
    farmer_id: str
    initial_price: float
    payment_id: Optional[str] = None  # Payment yang sudah dibuat sebelumnya


class TransactionResponse(BaseModel):
    id: str
    transaction_code: str
    farmer_id: str
    warehouse_id: str
    initial_price: float
    total_price: Optional[float]
    payment_status: str
    recording_started_at: Optional[str]
    recording_completed_at: Optional[str]
    created_at: str

@router.post("/create")
async def create_transaction(
    transaction_data: TransactionCreateRequest,
    x_warehouse_id: str = Header(...)
):
    """Create transaction dan attach ke payment jika ada"""
    try:
        supabase = get_supabase_client()
        
        # Validate payment jika ada
        if transaction_data.payment_id:
            payment_check = supabase.table("payments").select("*").eq(
                "id", transaction_data.payment_id
            ).execute()
            
            if not payment_check.data:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            payment = payment_check.data[0]
            if payment["status"] != "approved":
                raise HTTPException(status_code=400, detail="Payment must be approved first")
        
        # Create transaction
        txn_response = supabase.table("transactions").insert({
            "transaction_code": generate_transaction_code(),
            "warehouse_id": x_warehouse_id,
            "farmer_id": transaction_data.farmer_id,
            "initial_price": transaction_data.initial_price,
            "payment_status": "paid" if transaction_data.payment_id else "unpaid",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        txn = txn_response.data[0]
        txn_id = txn["id"]
        
        # Attach payment jika ada
        if transaction_data.payment_id:
            supabase.table("payments").update({
                "transaction_id": txn_id,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", transaction_data.payment_id).execute()
            
            # Set payment_completed_at karena payment sudah approved
            supabase.table("transactions").update({
                "payment_completed_at": datetime.utcnow().isoformat()
            }).eq("id", txn_id).execute()
        
        # Fetch transaction lagi untuk return response yang akurat
        final_response = supabase.table("transactions").select("*").eq(
            "id", txn_id
        ).single().execute()
        
        return final_response.data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """Get detail transaction"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("transactions").select("*").eq(
            "id", transaction_id
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        data = response.data[0]
        return TransactionResponse(
            id=data["id"],
            transaction_code=data["transaction_code"],
            farmer_id=data["farmer_id"],
            warehouse_id=data["warehouse_id"],
            initial_price=data["initial_price"],
            total_price=data["total_price"],
            payment_status=data["payment_status"],
            recording_started_at=data["recording_started_at"],
            recording_completed_at=data["recording_completed_at"],
            created_at=data["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warehouse/{warehouse_id}/list")
async def list_transactions(warehouse_id: str):
    """Get semua transactions dari satu warehouse"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("transactions").select("*").eq(
            "warehouse_id", warehouse_id
        ).order("created_at", desc=True).execute()
        
        return {
            "warehouse_id": warehouse_id,
            "count": len(response.data or []),
            "transactions": response.data or []
        }
    
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{transaction_id}/start-recording")
async def start_recording(
    transaction_id: str,
    x_warehouse_id: str = Header(...)
):
    """
    Mulai proses recording/pencatatan karung untuk transaction
    Set recording_started_at = NOW()
    """
    try:
        supabase = get_supabase_client()
        
        # Check transaction exists & belongs to warehouse
        txn_check = supabase.table("transactions").select("*").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized for this transaction")
        
        # Update recording_started_at
        response = supabase.table("transactions").update({
            "recording_started_at": datetime.utcnow().isoformat()
        }).eq("id", transaction_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to start recording")
        
        data = response.data[0]
        return {
            "success": True,
            "message": "Recording started",
            "transaction_id": transaction_id,
            "recording_started_at": data["recording_started_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{transaction_id}/complete-recording")
async def complete_recording(
    transaction_id: str,
    x_warehouse_id: str = Header(...)
):
    """
    Selesaikan proses recording/pencatatan karung
    Set recording_completed_at = NOW()
    Calculate total_weight_kg dan total_price dari harvest_records
    """
    try:
        supabase = get_supabase_client()
        
        # Check transaction exists & belongs to warehouse
        txn_check = supabase.table("transactions").select("*").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized for this transaction")
        
        # Get harvest records for this transaction
        harvest_response = supabase.table("harvest_records").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        harvest_records = harvest_response.data or []
        
        if not harvest_records:
            raise HTTPException(status_code=400, detail="No harvest records found for this transaction")
        
        # Calculate total weight
        total_weight_kg = sum(float(r["weight_kg"]) for r in harvest_records if r.get("weight_kg"))
        
        # Calculate total price: initial_price per kg * total_weight
        # (Ini bisa disesuaikan sesuai logic bisnis, untuk now pakai initial_price sebagai basis)
        price_per_kg = txn["initial_price"] / 100 if total_weight_kg > 0 else 0
        total_price = price_per_kg * total_weight_kg
        
        # Update transaction
        response = supabase.table("transactions").update({
            "recording_completed_at": datetime.utcnow().isoformat(),
            "total_weight_kg": round(total_weight_kg, 2),
            "total_price": round(total_price, 2)
        }).eq("id", transaction_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to complete recording")
        
        data = response.data[0]
        
        # Calculate grade breakdown
        grade_breakdown = {
            "A": len([r for r in harvest_records if r["grade"] == "A"]),
            "B": len([r for r in harvest_records if r["grade"] == "B"]),
            "C": len([r for r in harvest_records if r["grade"] == "C"])
        }
        
        return {
            "success": True,
            "message": "Recording completed",
            "transaction_id": transaction_id,
            "recording_completed_at": data["recording_completed_at"],
            "total_weight_kg": data["total_weight_kg"],
            "total_price": data["total_price"],
            "total_records": len(harvest_records),
            "grade_breakdown": grade_breakdown
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error completing recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transaction_id}/summary")
async def get_transaction_summary(transaction_id: str):
    """
    Get detail summary transaction:
    - Transaction info
    - Harvest records summary
    - Payment status
    """
    try:
        supabase = get_supabase_client()
        
        # Get transaction
        txn_response = supabase.table("transactions").select("*").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_response.data[0]
        
        # Get farmer info
        farmer_response = supabase.table("farmers").select("*").eq(
            "id", txn["farmer_id"]
        ).execute()
        
        farmer = farmer_response.data[0] if farmer_response.data else {}
        
        # Get harvest records
        harvest_response = supabase.table("harvest_records").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        harvest_records = harvest_response.data or []
        
        # Get payments
        payment_response = supabase.table("payments").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        payments = payment_response.data or []
        
        # Calculate totals
        total_approved_payment = sum(
            float(p["amount"]) for p in payments if p.get("status") == "approved"
        )
        
        grade_breakdown = {
            "A": len([r for r in harvest_records if r["grade"] == "A"]),
            "B": len([r for r in harvest_records if r["grade"] == "B"]),
            "C": len([r for r in harvest_records if r["grade"] == "C"])
        }
        
        return {
            "transaction": {
                "id": txn["id"],
                "transaction_code": txn["transaction_code"],
                "farmer_code": farmer.get("farmer_code"),
                "farmer_name": farmer.get("full_name"),
                "initial_price": txn["initial_price"],
                "total_weight_kg": txn.get("total_weight_kg"),
                "total_price": txn.get("total_price"),
                "payment_status": txn["payment_status"],
                "recording_started_at": txn["recording_started_at"],
                "recording_completed_at": txn["recording_completed_at"],
                "payment_completed_at": txn.get("payment_completed_at"),
                "created_at": txn["created_at"]
            },
            "harvest_summary": {
                "total_records": len(harvest_records),
                "total_weight_kg": txn.get("total_weight_kg"),
                "grade_breakdown": grade_breakdown,
                "average_confidence": round(
                    sum(float(r["detection_confidence"]) for r in harvest_records) / len(harvest_records), 2
                ) if harvest_records else 0
            },
            "payment_summary": {
                "total_approved": total_approved_payment,
                "remaining_needed": max(0, (txn.get("total_price") or 0) - total_approved_payment),
                "total_payments": len(payments),
                "payments": payments
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching transaction summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
