from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional

from schemas.betelchain import PaymentResponse
from config import settings

router = APIRouter(prefix="/api/payments", tags=["payments"])

def get_supabase_client() -> Client:
    """Lazy initialize Supabase client"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase configuration is missing"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class PaymentCreateRequest(BaseModel):
    transaction_id: str
    payment_type: str  # "initial" atau "remaining"
    amount: float
    payment_method: str
    payment_note: Optional[str] = None


class PaymentStatusUpdateRequest(BaseModel):
    status: str  # "approved", "rejected", "pending"


class PaymentResponse(BaseModel):
    id: str
    transaction_id: str
    payment_type: str
    amount: float
    payment_method: str
    status: str
    payment_date: str


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment: PaymentCreateRequest,
    x_warehouse_id: str = Header(...)
):
    """
    Warehouse membuat payment record (biasanya initial payment)
    
    Request:
    - transaction_id: ID transaction
    - payment_type: "initial" atau "remaining"
    - amount: Jumlah uang
    - payment_method: Cara pembayaran (Bank Transfer, Cash, dll)
    """
    try:
        supabase = get_supabase_client()
        
        # Validate transaction exists
        txn_check = supabase.table("transactions").select("id, warehouse_id").eq(
            "id", payment.transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        
        # Validate warehouse authorization
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized for this transaction")
        
        # Create payment
        response = supabase.table("payments").insert({
            "transaction_id": payment.transaction_id,
            "payment_type": payment.payment_type,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "payment_note": payment.payment_note,
            "status": "pending",  # Default status
            "payment_date": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create payment")
        
        data = response.data[0]
        return PaymentResponse(
            id=data["id"],
            transaction_id=data["transaction_id"],
            payment_type=data["payment_type"],
            amount=data["amount"],
            payment_method=data["payment_method"],
            status=data["status"],
            payment_date=data["payment_date"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str):
    """Get detail payment"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("payments").select("*").eq(
            "id", payment_id
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        data = response.data[0]
        return PaymentResponse(
            id=data["id"],
            transaction_id=data["transaction_id"],
            payment_type=data["payment_type"],
            amount=data["amount"],
            payment_method=data["payment_method"],
            status=data["status"],
            payment_date=data["payment_date"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{transaction_id}/list")
async def list_payments(transaction_id: str):
    """Get semua payments untuk satu transaction"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("payments").select("*").eq(
            "transaction_id", transaction_id
        ).order("payment_date", desc=True).execute()
        
        return {
            "transaction_id": transaction_id,
            "count": len(response.data),
            "payments": response.data
        }
    
    except Exception as e:
        print(f"Error fetching payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{payment_id}/approve")
async def approve_payment(
    payment_id: str,
    update: PaymentStatusUpdateRequest,
    x_warehouse_id: str = Header(...)
):
    """
    Admin approve/reject payment
    Status berubah dari "pending" → "approved" atau "rejected"
    Auto-update transaction payment_status berdasarkan total approved
    """
    try:
        supabase = get_supabase_client()
        
        # Validate status
        if update.status not in ["approved", "rejected", "pending"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        # Get payment
        payment_check = supabase.table("payments").select("*").eq(
            "id", payment_id
        ).execute()
        
        if not payment_check.data:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        payment = payment_check.data[0]
        transaction_id = payment["transaction_id"]
        
        # Validate transaction & authorization
        txn_check = supabase.table("transactions").select("*").eq(
            "id", transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # 1. Update payment status
        payment_response = supabase.table("payments").update({
            "status": update.status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", payment_id).execute()
        
        if not payment_response.data:
            raise HTTPException(status_code=400, detail="Failed to update payment")
        
        # 2. Calculate total approved payments
        all_payments_response = supabase.table("payments").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        all_payments = all_payments_response.data or []
        total_approved = sum(
            float(p["amount"]) for p in all_payments if p.get("status") == "approved"
        )
        
        # 3. Determine new payment_status for transaction
        total_price = txn.get("total_price") or 0
        
        if total_price == 0:
            new_payment_status = "unpaid"
            payment_completed_at = None
        elif total_approved >= total_price:
            new_payment_status = "paid"
            payment_completed_at = datetime.utcnow().isoformat()
        elif total_approved > 0:
            new_payment_status = "partial"
            payment_completed_at = None
        else:
            new_payment_status = "unpaid"
            payment_completed_at = None
        
        # 4. Update transaction payment_status
        txn_update = supabase.table("transactions").update({
            "payment_status": new_payment_status,
            "payment_completed_at": payment_completed_at if new_payment_status == "paid" else txn.get("payment_completed_at")
        }).eq("id", transaction_id).execute()
        
        if not txn_update.data:
            raise HTTPException(status_code=400, detail="Failed to update transaction")
        
        return {
            "success": True,
            "message": f"Payment {update.status}",
            "payment_id": payment_id,
            "payment_status": update.status,
            "transaction_id": transaction_id,
            "transaction_payment_status": new_payment_status,
            "total_approved": total_approved,
            "total_price": total_price
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transaction/{transaction_id}/summary")
async def get_payment_summary(transaction_id: str):
    """
    Get ringkasan payment untuk transaction
    Lihat total paid, remaining, status
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
        
        # Get payments
        payment_response = supabase.table("payments").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        payments = payment_response.data or []
        
        # Calculate totals
        initial_paid = sum(
            float(p["amount"]) for p in payments 
            if p["payment_type"] == "initial" and p["status"] == "approved"
        )
        remaining_paid = sum(
            float(p["amount"]) for p in payments 
            if p["payment_type"] == "remaining" and p["status"] == "approved"
        )
        total_paid = initial_paid + remaining_paid
        total_price = txn["total_price"]
        remaining_needed = max(0, total_price - total_paid)
        
        # Payment breakdown by status
        payment_by_status = {
            "approved": len([p for p in payments if p["status"] == "approved"]),
            "pending": len([p for p in payments if p["status"] == "pending"]),
            "rejected": len([p for p in payments if p["status"] == "rejected"])
        }
        
        return {
            "transaction_id": transaction_id,
            "total_price": total_price,
            "initial_paid": initial_paid,
            "remaining_paid": remaining_paid,
            "total_paid": total_paid,
            "remaining_needed": remaining_needed,
            "payment_percentage": round((total_paid / total_price * 100), 2) if total_price > 0 else 0,
            "payment_status": txn["payment_status"],
            "payment_by_status": payment_by_status,
            "total_payments": len(payments),
            "payments": payments
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching payment summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
