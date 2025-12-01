from fastapi import APIRouter, Header, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from typing import List


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

class SpentByHourItem(BaseModel):
  hour: datetime
  amount: float


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

@router.get("/spent-by-hour", response_model=List[SpentByHourItem])
async def get_spent_by_hour(
  start: datetime,
  end: datetime,
  x_warehouse_id: str = Header(..., alias="X-Warehouse-ID")
):
  """
  Total spent per jam (payments approved) untuk satu warehouse,
  antara start dan end (UTC).
  """
  try:
    supabase = get_supabase_client()

    # Ambil raw payments dulu (filter status + warehouse via transaksi)
    payments_res = supabase.table("payments") \
      .select("amount, payment_date, transactions!inner(warehouse_id)") \
      .eq("transactions.warehouse_id", x_warehouse_id) \
      .eq("status", "approved") \
      .gte("payment_date", start.isoformat()) \
      .lte("payment_date", end.isoformat()) \
      .execute()

    rows = payments_res.data or []

    # Group by hour di Python (date_trunc('hour'))
    buckets: dict[str, float] = {}

    for row in rows:
      payment_date = row.get("payment_date")
      amount = float(row.get("amount") or 0)

      if not payment_date:
        continue

      dt = datetime.fromisoformat(payment_date.replace("Z", "+00:00"))
      dt_hour = dt.replace(minute=0, second=0, microsecond=0)
      key = dt_hour.isoformat()

      buckets[key] = buckets.get(key, 0.0) + amount

    # Convert ke list terurut by hour
    items: List[SpentByHourItem] = []
    for key in sorted(buckets.keys()):
      items.append(SpentByHourItem(
        hour=datetime.fromisoformat(key),
        amount=buckets[key]
      ))

    return items

  except HTTPException:
    raise
  except Exception as e:
    print("Error in get_spent_by_hour:", e)
    raise HTTPException(status_code=500, detail="Failed to fetch spent by hour")
