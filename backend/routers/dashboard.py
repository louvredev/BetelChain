from fastapi import APIRouter, Header, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Dict, Optional

from config import settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_supabase_client() -> Client:
    """Lazy initialize Supabase client"""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration is missing"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class WarehouseSummaryResponse(BaseModel):
    warehouse_id: str
    farmers_count: int
    dominant_grade: Optional[str]
    dominant_grade_ratio: float
    grades_breakdown: Dict[str, int]
    total_spent: float
    total_sacks: int


@router.get("/warehouse-summary", response_model=WarehouseSummaryResponse)
async def get_warehouse_summary(
    x_warehouse_id: str = Header(..., alias="X-Warehouse-ID")
):
    """
    Summary per warehouse:
    - farmers_count: petani aktif yang registered_by_warehouse = warehouse_id
    - total_spent: total amount payment approved untuk transaksi di warehouse ini
    - total_sacks: total harvest_records untuk transaksi di warehouse ini
    - grades_breakdown: jumlah karung per grade A/B/C
    - dominant_grade + ratio: grade terbanyak + persentasenya
    """
    try:
        supabase = get_supabase_client()

        # 1) Farmers count (aktif) per warehouse
        farmers_res = supabase.table("farmers") \
            .select("id", count="exact") \
            .eq("registered_by_warehouse", x_warehouse_id) \
            .eq("is_active", True) \
            .execute()
        farmers_count = farmers_res.count or 0

        # 2) Total spent (payments approved untuk transaksi di warehouse ini)
        # Join payments -> transactions via FKs di Supabase
        payments_res = supabase.table("payments") \
            .select("amount, transactions!inner(warehouse_id)") \
            .eq("transactions.warehouse_id", x_warehouse_id) \
            .eq("status", "approved") \
            .execute()

        total_spent = 0.0
        if payments_res.data:
            for row in payments_res.data:
                total_spent += float(row["amount"])

        # 3) Harvest: total sacks + grades breakdown
        harvest_res = supabase.table("harvest_records") \
            .select("grade, transactions!inner(warehouse_id)") \
            .eq("transactions.warehouse_id", x_warehouse_id) \
            .execute()

        grades_breakdown = {"A": 0, "B": 0, "C": 0}
        total_sacks = 0

        if harvest_res.data:
            for row in harvest_res.data:
                grade = row.get("grade")
                if grade in grades_breakdown:
                    grades_breakdown[grade] += 1
                    total_sacks += 1

        # 4) Dominant grade + ratio
        dominant_grade = None
        dominant_grade_ratio = 0.0
        if total_sacks > 0:
            dominant_grade = max(
                grades_breakdown.keys(),
                key=lambda g: grades_breakdown[g]
            )
            dominant_grade_ratio = grades_breakdown[dominant_grade] / total_sacks

        return WarehouseSummaryResponse(
            warehouse_id=x_warehouse_id,
            farmers_count=farmers_count,
            dominant_grade=dominant_grade,
            dominant_grade_ratio=dominant_grade_ratio,
            grades_breakdown=grades_breakdown,
            total_spent=total_spent,
            total_sacks=total_sacks
        )

    except HTTPException:
        raise
    except Exception as e:
        print("Error in get_warehouse_summary:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch warehouse summary")
