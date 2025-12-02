from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional
import uuid

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
    amount: float
    payment_method: str
    payment_note: Optional[str] = None


class PaymentStatusUpdateRequest(BaseModel):
    status: str  # "approved", "rejected", "pending"


class PaymentResponse(BaseModel):
    id: str
    farmer_id: str
    transaction_id: Optional[str]
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
    Buat payment berdasarkan transaction
    Transaction sudah ada, payment hanya perlu amount, method, note
    
    Request:
    - transaction_id: ID transaction yang sudah dibuat
    - amount: Jumlah pembayaran
    - payment_method: Cara pembayaran (cash, transfer, dll)
    - payment_note: Catatan tambahan
    """
    try:
        supabase = get_supabase_client()
        
        # Validate warehouse exists
        warehouse_check = supabase.table("warehouses").select("id").eq(
            "id", x_warehouse_id
        ).execute()
        
        if not warehouse_check.data:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        # Validate transaction exists & belongs to this warehouse
        txn_check = supabase.table("transactions").select("*").eq(
            "id", payment.transaction_id
        ).execute()
        
        if not txn_check.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        txn = txn_check.data[0]
        if txn["warehouse_id"] != x_warehouse_id:
            raise HTTPException(status_code=403, detail="Not authorized for this transaction")
        
        # Create payment
        response = supabase.table("payments").insert({
            "id": str(uuid.uuid4()),
            "farmer_id": txn["farmer_id"],  # Ambil dari transaction
            "transaction_id": payment.transaction_id,
            "amount": float(payment.amount),
            "payment_method": payment.payment_method,
            "payment_note": payment.payment_note,
            "status": "pending",
            "payment_date": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create payment")
        
        data = response.data[0]
        return PaymentResponse(
            id=data["id"],
            farmer_id=data["farmer_id"],
            transaction_id=data["transaction_id"],
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


# Tambah endpoint: GET payment untuk transaction (singular, bukan list)
@router.get("/transaction/{transaction_id}")
async def get_payment_by_transaction(transaction_id: str):
    """Get payment untuk satu transaction (asumsi 1 payment per transaction)"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("payments").select("*").eq(
            "transaction_id", transaction_id
        ).execute()
        
        if not response.data:
            return {
                "transaction_id": transaction_id,
                "payment": None,
                "message": "No payment found for this transaction"
            }
        
        # Return payment pertama (seharusnya hanya 1)
        payment = response.data[0]
        return {
            "transaction_id": transaction_id,
            "payment": payment
        }
    
    except Exception as e:
        print(f"Error fetching payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_all_payments():
    """Get semua payments (untuk tabel di frontend)"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("payments").select("*").order("created_at", desc=True).execute()
        return {
            "count": len(response.data or []),
            "payments": response.data or []
        }
    except Exception as e:
        print(f"Error fetching payments: {e}")
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
            farmer_id=data["farmer_id"],
            transaction_id=data["transaction_id"],
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
            "count": len(response.data or []),
            "payments": response.data or []
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
    Approve atau reject payment
    Status: pending → approved atau rejected
    Jika payment sudah attached ke transaction, update transaction payment_status
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
        transaction_id = payment.get("transaction_id")
        
        # Validate warehouse authorization (jika transaction ada)
        if transaction_id:
            txn_check = supabase.table("transactions").select("*").eq(
                "id", transaction_id
            ).execute()
            
            if not txn_check.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            txn = txn_check.data[0]
            if txn["warehouse_id"] != x_warehouse_id:
                raise HTTPException(status_code=403, detail="Not authorized")
        else:
            # Jika transaction belum ada, validate farmer ownership
            farmer_check = supabase.table("farmers").select("registered_by_warehouse").eq(
                "id", payment["farmer_id"]
            ).execute()
            
            if not farmer_check.data or farmer_check.data[0]["registered_by_warehouse"] != x_warehouse_id:
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # 1. Update payment status
        payment_response = supabase.table("payments").update({
            "status": update.status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", payment_id).execute()
        
        if not payment_response.data:
            raise HTTPException(status_code=400, detail="Failed to update payment")
        
        # 2. Jika transaction ada, update transaction payment_status
        if transaction_id:
            # Calculate total approved payments
            all_payments_response = supabase.table("payments").select("*").eq(
                "transaction_id", transaction_id
            ).execute()
            
            all_payments = all_payments_response.data or []
            total_approved = sum(
                float(p["amount"]) for p in all_payments if p.get("status") == "approved"
            )
            
            # Get transaction to check total_price
            txn_check = supabase.table("transactions").select("*").eq(
                "id", transaction_id
            ).execute()
            txn = txn_check.data[0]
            total_price = txn.get("total_price") or txn.get("initial_price") or 0
            
            # Determine new payment_status (cuma paid atau unpaid)
            if total_approved >= total_price and total_price > 0:
                new_payment_status = "paid"
                payment_completed_at = datetime.utcnow().isoformat()
            else:
                new_payment_status = "unpaid"
                payment_completed_at = None

            # Update transaction
            update_data = {
                "payment_status": new_payment_status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if new_payment_status == "paid":
                update_data["payment_completed_at"] = payment_completed_at

            supabase.table("transactions").update(update_data).eq("id", transaction_id).execute()
           
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
        else:
            # Payment belum attached ke transaction
            return {
                "success": True,
                "message": f"Payment {update.status}",
                "payment_id": payment_id,
                "payment_status": update.status,
                "transaction_id": None,
                "note": "Payment not yet attached to any transaction"
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
        total_approved = sum(
            float(p["amount"]) for p in payments if p.get("status") == "approved"
        )
        total_pending = sum(
            float(p["amount"]) for p in payments if p.get("status") == "pending"
        )
        total_price = txn.get("total_price") or txn.get("initial_price") or 0
        remaining_needed = max(0, total_price - total_approved)
        
        # Payment breakdown by status
        payment_by_status = {
            "approved": len([p for p in payments if p["status"] == "approved"]),
            "pending": len([p for p in payments if p["status"] == "pending"]),
            "rejected": len([p for p in payments if p["status"] == "rejected"])
        }
        
        return {
            "transaction_id": transaction_id,
            "total_price": total_price,
            "total_approved": total_approved,
            "total_pending": total_pending,
            "remaining_needed": remaining_needed,
            "payment_percentage": round((total_approved / total_price * 100), 2) if total_price > 0 else 0,
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
