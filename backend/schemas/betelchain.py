from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============================================================================
# FARMERS SCHEMAS
# ============================================================================

class FarmerCreateRequest(BaseModel):
    farmer_code: str
    full_name: str
    phone: Optional[str] = None
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
    phone: Optional[str]
    bank_name: Optional[str]
    account_number: Optional[str]
    account_holder_name: Optional[str]
    address: Optional[str]
    village: Optional[str]
    district: Optional[str]
    city: Optional[str]
    province: Optional[str]
    registered_by_warehouse: str
    is_active: bool
    created_at: str

class FarmerUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder_name: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    is_active: Optional[bool] = None

# ============================================================================
# TRANSACTIONS SCHEMAS
# ============================================================================

class TransactionCreateRequest(BaseModel):
    farmer_id: str
    initial_price: float
    payment_id: Optional[str] = None  # NEW: untuk attach payment


class TransactionStartRecordingRequest(BaseModel):
    """Request untuk mulai pencatatan hasil tani"""
    pass


class TransactionCompleteRecordingRequest(BaseModel):
    """Request untuk selesai pencatatan hasil tani"""
    pass


class TransactionResponse(BaseModel):
    id: str
    transaction_code: str
    warehouse_id: str
    farmer_id: str
    initial_price: float
    total_weight_kg: Optional[float] = None  # CHANGED: optional
    total_price: Optional[float] = None  # CHANGED: optional
    payment_status: str  # unpaid, paid (CHANGED: dari unpaid, partial, paid)
    recording_started_at: Optional[str] = None
    recording_completed_at: Optional[str] = None
    payment_completed_at: Optional[str] = None
    created_at: str


class TransactionDetailResponse(BaseModel):
    """Transaction dengan detail harvest records"""
    id: str
    transaction_code: str
    warehouse_id: str
    farmer_id: str
    initial_price: float
    total_weight_kg: Optional[float] = None
    total_price: Optional[float] = None
    payment_status: str
    recording_started_at: Optional[str]
    recording_completed_at: Optional[str]
    payment_completed_at: Optional[str]
    created_at: str
    harvest_records_count: int
    total_sacks: int
    grade_breakdown: dict  # {"A": int, "B": int, "C": int}


# ============================================================================
# PAYMENTS SCHEMAS
# ============================================================================

class PaymentCreateRequest(BaseModel):
    farmer_id: str  # CHANGED: dari transaction_id ke farmer_id
    amount: float
    payment_method: str
    payment_note: Optional[str] = None
    proof_image_url: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    farmer_id: str  # CHANGED: dari transaction_id ke farmer_id
    transaction_id: Optional[str] = None  # CHANGED: optional, bisa null
    amount: float
    payment_method: str
    payment_note: Optional[str]
    proof_image_url: Optional[str]
    status: str  # pending, approved, rejected (NEW)
    payment_date: str
    created_at: str


class PaymentListResponse(BaseModel):
    farmer_id: str  # CHANGED
    transaction_id: Optional[str] = None  # CHANGED: optional
    total_payments: int
    payments: List[PaymentResponse]  # CHANGED: dari split initial/remaining
    total_amount: float  # NEW

# ============================================================================
# TRANSACTION DETAIL SCHEMAS
# ============================================================================

class TransactionCompleteResponse(BaseModel):
    transaction_id: str
    transaction_code: str
    farmer_id: str
    initial_price: float
    total_weight_kg: float
    total_price: float
    total_sacks: int
    grade_breakdown: dict  # {"A": int, "B": int, "C": int}
    payment_status: str
    message: str

class TransactionSummaryResponse(BaseModel):
    transaction_id: str
    transaction_code: str
    farmer_code: str
    farmer_name: str
    warehouse_id: str
    initial_price: float
    total_weight_kg: float
    total_price: float
    total_sacks: int
    grade_breakdown: dict
    payment_status: str
    initial_payment_received: float
    remaining_payment_needed: float
    recording_started_at: Optional[str]
    recording_completed_at: Optional[str]
    payment_completed_at: Optional[str]
