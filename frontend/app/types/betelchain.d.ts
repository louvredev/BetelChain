// Farmer Types
export interface Farmer {
  id: string
  farmer_code: string
  full_name: string
  phone?: string
  bank_name?: string
  account_number?: string
  account_holder_name?: string
  address?: string
  village?: string
  district?: string
  city?: string
  province?: string
  registered_by_warehouse: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

// Transaction Types
export interface Transaction {
  id: string
  transaction_code: string
  warehouse_id: string
  farmer_id: string
  initial_price: number
  total_weight_kg?: number
  total_price?: number
  payment_status: 'unpaid' | 'partial' | 'completed'
  recording_started_at?: string
  recording_completed_at?: string
  payment_completed_at?: string
  created_at: string
  updated_at?: string
  farmer_name?: string | null
  farmer_code?: string | null
}

// Harvest Record Types
export interface HarvestRecord {
  id: string
  transaction_id: string
  grade: 'A' | 'B' | 'C'
  sack_color: string
  weight_kg?: number
  detection_confidence?: number
  image_url?: string
  recorded_at?: string
  created_at: string
}

// Payment Types
export interface Payment {
  id: string
  transaction_id: string
  payment_type: 'initial' | 'remaining'
  amount: number
  proof_image_url?: string
  payment_method: string
  payment_note?: string
  payment_date?: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  updated_at?: string
}

// Summary Types
export interface TransactionSummary {
  transaction: Transaction & { farmer_code: string; farmer_name: string }
  harvest_summary: {
    total_records: number
    total_weight_kg?: number
    grade_breakdown: { A: number; B: number; C: number }
    average_confidence?: number
  }
  payment_summary: {
    total_approved: number
    remaining_needed: number
    total_payments: number
    payments: Payment[]
  }
}

export interface PaymentSummary {
  transaction_id: string
  total_price: number
  initial_paid: number
  remaining_paid: number
  total_paid: number
  remaining_needed: number
  payment_percentage: number
  payment_status: string
  payment_by_status: { approved: number; pending: number; rejected: number }
  total_payments: number
  payments: Payment[]
}
