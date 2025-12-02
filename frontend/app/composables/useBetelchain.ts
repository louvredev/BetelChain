import { useSupabase } from './useSupabase'
import type { 
  Transaction, 
  Farmer, 
  Payment, 
  HarvestRecord 
} from '~/types/betelchain'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://betelchain-production-00a4.up.railway.app'

export const useBetelchain = () => {
  const { supabase } = useSupabase()
  const user = ref(null)

  // Get warehouse ID from localStorage
  const getWarehouseId = async () => {
    const warehouseId = useState('warehouseId', () => {
      if (process.server) return '51b51eb1-2552-431e-b53b-b5bfb856a70b'
      return localStorage.getItem('warehouseId') || '51b51eb1-2552-431e-b53b-b5bfb856a70b'
    })
    
    return warehouseId.value
  }


  // ==================== DASHBOARD ====================

  const getWarehouseDashboard = async () => {
    const warehouseId = await getWarehouseId()

    const response = await fetch(
      `${BACKEND_URL}/api/dashboard/warehouse-summary`,
      {
        method: 'GET',
        headers: {
          'X-Warehouse-ID': warehouseId
        }
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch warehouse summary')
    }

    return response.json() as Promise<{
      warehouse_id: string
      farmers_count: number
      dominant_grade: string | null
      dominant_grade_ratio: number
      grades_breakdown: Record<string, number>
      total_spent: number
      total_sacks: number
    }>
  }

  const getSpentByHour = async (start: string, end: string) => {
  const warehouseId = await getWarehouseId()

  const url = new URL(`${BACKEND_URL}/api/dashboard/spent-by-hour`)
  url.searchParams.set('start', start)
  url.searchParams.set('end', end)

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'X-Warehouse-ID': warehouseId
    }
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch spent by hour')
  }

  return response.json() as Promise<Array<{ hour: string; amount: number }>>
}



  // ==================== FARMERS ====================

  const registerFarmer = async (farmer: {
    full_name: string
    phone: string
    bank_name?: string
    account_number?: string
    account_holder_name?: string
    address?: string
    village?: string
    district?: string
    city?: string
    province?: string
  }) => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(`${BACKEND_URL}/api/farmers/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Warehouse-ID': warehouseId
      },
      body: JSON.stringify(farmer)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to register farmer')
    }

    return response.json() as Promise<Farmer>
  }

  const listFarmers = async () => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(
      `${BACKEND_URL}/api/farmers/warehouse/${warehouseId}/list`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch farmers')
    }

    const data = await response.json()
    return data.farmers as Farmer[]
  }

  const getFarmer = async (farmerId: string) => {
    const response = await fetch(
      `${BACKEND_URL}/api/farmers/${farmerId}`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch farmer')
    }

    return response.json() as Promise<Farmer>
  }

  const deleteFarmer = async (farmerId: string) => {
    const warehouseId = await getWarehouseId()

    const response = await fetch(
      `${BACKEND_URL}/api/farmers/${farmerId}/delete`,
      {
        method: 'DELETE',
        headers: {
          'X-Warehouse-ID': warehouseId
        }
      }
    )

    if (!response.ok) {
      let msg = 'Failed to delete farmer'
      try {
        const err = await response.json()
        msg = err.detail || err.message || msg
      } catch {
        // ignore parse error
      }
      throw new Error(msg)
    }

    try {
      return await response.json()
    } catch {
      return null
    }
  }


  // ==================== TRANSACTIONS ====================

  const createTransaction = async (transaction: {
    farmer_id: string
    initial_price: number
  }) => {
    const warehouseId = await getWarehouseId()

    const response = await fetch(`${BACKEND_URL}/api/transactions/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Warehouse-ID': warehouseId
      },
      body: JSON.stringify(transaction)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create transaction')
    }

    return response.json()
  }

  const listTransactions = async () => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(
      `${BACKEND_URL}/api/transactions/warehouse/${warehouseId}/list`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch transactions')
    }

    const data = await response.json()
    return data.transactions as Transaction[]
  }

  const getTransaction = async (transactionId: string) => {
    const response = await fetch(
      `${BACKEND_URL}/api/transactions/${transactionId}`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch transaction')
    }

    return response.json() as Promise<Transaction>
  }

  const startRecording = async (transactionId: string) => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(
      `${BACKEND_URL}/api/transactions/${transactionId}/start-recording`,
      {
        method: 'POST',
        headers: {
          'X-Warehouse-ID': warehouseId
        }
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to start recording')
    }

    return response.json()
  }

  const completeRecording = async (transactionId: string) => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(
      `${BACKEND_URL}/api/transactions/${transactionId}/complete-recording`,
      {
        method: 'POST',
        headers: {
          'X-Warehouse-ID': warehouseId
        }
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to complete recording')
    }

    return response.json()
  }

  const getTransactionSummary = async (transactionId: string) => {
    const response = await fetch(
      `${BACKEND_URL}/api/transactions/${transactionId}/summary`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch transaction summary')
    }

    return response.json()
  }

  // ==================== HARVEST ====================

  const detectAndSaveHarvest = async (
    transactionId: string,
    file: File
  ) => {
    const warehouseId = await getWarehouseId()
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('transaction_id', transactionId)

    const response = await fetch(
      `${BACKEND_URL}/api/ml-harvest/detect-and-save`,
      {
        method: 'POST',
        headers: {
          'X-Warehouse-ID': warehouseId
        },
        body: formData
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to detect and save harvest')
    }

    return response.json() as Promise<HarvestRecord>
  }

  const getHarvestSummary = async (transactionId: string) => {
    const response = await fetch(
      `${BACKEND_URL}/api/ml-harvest/transaction/${transactionId}/harvest-summary`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch harvest summary')
    }

    return response.json()
  }

  // ==================== PAYMENTS ====================

  // BARU: Get payment untuk satu transaction (singular)
  const getPaymentByTransaction = async (transactionId: string) => {
    const response = await fetch(
      `${BACKEND_URL}/api/payments/transaction/${transactionId}`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch payment')
    }

    const data = await response.json()
    return data.payment as Payment | null
  }

  // UPDATE: Create payment - transaction_id wajib, hapus payment_type
  const createPayment = async (payment: {
    transaction_id: string
    amount: number
    payment_method: string
    payment_note?: string
  }) => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(`${BACKEND_URL}/api/payments/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Warehouse-ID': warehouseId
      },
      body: JSON.stringify(payment)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create payment')
    }

    return response.json() as Promise<Payment>
  }

  const getPaymentSummary = async (transactionId: string) => {
    const response = await fetch(
      `${BACKEND_URL}/api/payments/transaction/${transactionId}/summary`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch payment summary')
    }

    return response.json()
  }

  const approvePayment = async (paymentId: string, status: string) => {
    const warehouseId = await getWarehouseId()
    
    const response = await fetch(
      `${BACKEND_URL}/api/payments/${paymentId}/approve`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Warehouse-ID': warehouseId
        },
        body: JSON.stringify({ status })
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to approve payment')
    }

    return response.json() as Promise<Payment>
  }

  const getFarmersPaymentSummary = async () => {
    const warehouseId = await getWarehouseId()

    const response = await fetch(
      `${BACKEND_URL}/api/dashboard/farmers-payment-summary`,
      {
        method: 'GET',
        headers: {
          'X-Warehouse-ID': warehouseId
        }
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch farmers payment summary')
    }

    return response.json() as Promise<Array<{
      id: string
      farmer_code: string
      full_name: string
      phone: string | null
      bank_name: string | null
      is_active: boolean
      totalTransactions: number
      totalPaid: number
      totalOutstanding: number
    }>>
  }


  return {
    // Farmers
    registerFarmer,
    listFarmers,
    getFarmer,
    deleteFarmer,
    // Transactions
    createTransaction,
    listTransactions,
    getTransaction,
    startRecording,
    completeRecording,
    getTransactionSummary,
    // Harvest
    detectAndSaveHarvest,
    getHarvestSummary,
    // Payments
    getPaymentByTransaction,
    createPayment,
    getPaymentSummary,
    approvePayment,
    // Dashboard
    getWarehouseDashboard,
    getSpentByHour,
    getFarmersPaymentSummary
  }
}
