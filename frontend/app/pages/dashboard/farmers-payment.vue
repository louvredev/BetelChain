<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { upperFirst } from 'scule'
import { getPaginationRowModel } from '@tanstack/table-core'
import type { Row } from '@tanstack/table-core'
import type { Farmer } from '~/types/betelchain'

definePageMeta({
  layout: 'dashboard'
})

const { getFarmersPaymentSummary } = useBetelchain()
const toast = useToast()
const table = useTemplateRef('table')

// Filter untuk nama / kode farmer
const columnFilters = ref([{
  id: 'full_name',
  value: ''
}])
const columnVisibility = ref()
const rowSelection = ref({})

// Data summary farmers + payments dari backend
const farmerData = ref<any[]>([])
const status = ref<'idle' | 'pending' | 'success' | 'error'>('idle')

const fetchFarmers = async () => {
  status.value = 'pending'
  try {
    const data = await getFarmersPaymentSummary()
    farmerData.value = data
    status.value = 'success'
  } catch (error: any) {
    status.value = 'error'
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to fetch farmers payment summary',
      color: 'red'
    })
  }
}


await fetchFarmers()

function getRowItems (row: Row<any>) {
  return [
    {
      type: 'label',
      label: 'Actions'
    },
    {
      label: 'Copy farmer ID',
      icon: 'i-lucide-copy',
      onSelect() {
        navigator.clipboard.writeText(row.original.id.toString())
        toast.add({
          title: 'Copied to clipboard',
          description: 'Farmer ID copied to clipboard'
        })
      }
    },
    {
      type: 'separator'
    },
    {
      label: 'View transactions',
      icon: 'i-lucide-list',
      onSelect() {
        navigateTo(`/dashboard/transactions?farmer_id=${row.original.id}`)
      }
    },
    {
      label: 'View payments',
      icon: 'i-lucide-wallet'
    }
  ]
}

const columns: TableColumn<any>[] = [
  {
    id: 'select',
    header: ({ table }) =>
      h(resolveComponent('UCheckbox'), {
        'modelValue': table.getIsSomePageRowsSelected()
          ? 'indeterminate'
          : table.getIsAllPageRowsSelected(),
        'onUpdate:modelValue': (value: boolean | 'indeterminate') =>
          table.toggleAllPageRowsSelected(!!value),
        'ariaLabel': 'Select all'
      }),
    cell: ({ row }) =>
      h(resolveComponent('UCheckbox'), {
        'modelValue': row.getIsSelected(),
        'onUpdate:modelValue': (value: boolean | 'indeterminate') => row.toggleSelected(!!value),
        'ariaLabel': 'Select row'
      })
  },
  {
    accessorKey: 'farmer_code',
    header: 'Code'
  },
  {
    accessorKey: 'full_name',
    header: 'Name'
  },
  {
    accessorKey: 'phone',
    header: 'Phone'
  },
  {
    accessorKey: 'bank_name',
    header: 'Bank'
  },
  {
    accessorKey: 'totalTransactions',
    header: 'Transactions',
    cell: ({ row }) => {
      const UBadge = resolveComponent('UBadge')
      return h(UBadge, { color: 'blue', variant: 'subtle' }, () => row.original.totalTransactions)
    }
  },
  {
    accessorKey: 'totalPaid',
    header: 'Total Paid',
    cell: ({ row }) => formatCurrency(row.original.totalPaid)
  },
  {
    accessorKey: 'totalOutstanding',
    header: 'Outstanding',
    cell: ({ row }) => formatCurrency(row.original.totalOutstanding)
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const UButton = resolveComponent('UButton')
      const UDropdownMenu = resolveComponent('UDropdownMenu')

      return h(
        'div',
        { class: 'text-right' },
        h(
          UDropdownMenu,
          {
            content: {
              align: 'end'
            },
            items: getRowItems(row)
          },
          () =>
            h(UButton, {
              icon: 'i-lucide-ellipsis-vertical',
              color: 'neutral',
              variant: 'ghost',
              class: 'ml-auto'
            })
        )
      )
    }
  }
]

const statusFilter = ref<'all' | 'active' | 'inactive'>('all')

watch(() => statusFilter.value, (newVal) => {
  if (!table.value?.tableApi) return

  const statusColumn = table.value.tableApi.getColumn('is_active')
  if (!statusColumn) return

  if (newVal === 'all') {
    statusColumn.setFilterValue(undefined)
  } else {
    statusColumn.setFilterValue(newVal === 'active')
  }
})

const pagination = ref({
  pageIndex: 0,
  pageSize: 10
})

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value || 0)
}

const onRegisterSuccess = () => {
  fetchFarmers()}
</script>

<template>
  <UDashboardPanel id="farmers-payment">
    <template #header>
      <UDashboardNavbar title="Farmers & Payments">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <DashboardFarmersRegisterModal @success="onRegisterSuccess" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex flex-wrap items-center justify-between gap-1.5">
        <!-- Filter by name/code -->
        <UInput
          :model-value="(table?.tableApi?.getColumn('full_name')?.getFilterValue() as string)"
          class="max-w-sm"
          icon="i-lucide-search"
          placeholder="Filter farmers by name or code..."
          @update:model-value="val => {
            table?.tableApi?.getColumn('full_name')?.setFilterValue(val)
          }"
        />

        <div class="flex flex-wrap items-center gap-1.5">
          <!-- Delete Button -->
            <DashboardFarmersDeleteModal
              :count="table?.tableApi?.getFilteredSelectedRowModel().rows.length || 0"
              :selected-ids="table?.tableApi?.getFilteredSelectedRowModel().rows.map((r: any) => r.original.id) || []"
              @deleted="fetchFarmers"
            >

            <template #default="{ open }">
              <UButton
                v-if="table?.tableApi?.getFilteredSelectedRowModel().rows.length"
                label="Delete"
                color="error"
                variant="subtle"
                icon="i-lucide-trash"
                @click="open()"
              >
                <template #trailing>
                  <UKbd>
                    {{ table?.tableApi?.getFilteredSelectedRowModel().rows.length }}
                  </UKbd>
                </template>
              </UButton>
            </template>
          </DashboardFarmersDeleteModal>
          
          <!-- Column visibility menu (optional, sama seperti customers) -->
          <UDropdownMenu
            :items="
              table?.tableApi
                ?.getAllColumns()
                .filter((column: any) => column.getCanHide?.())
                .map((column: any) => ({
                  label: upperFirst(column.id),
                  type: 'checkbox' as const,
                  checked: column.getIsVisible?.(),
                  onUpdateChecked(checked: boolean) {
                    table?.tableApi?.getColumn(column.id)?.toggleVisibility(!!checked)
                  },
                  onSelect(e?: Event) {
                    e?.preventDefault()
                  }
                }))
            "
            :content="{ align: 'end' }"
          >
            <UButton
              label="Display"
              color="neutral"
              variant="outline"
              trailing-icon="i-lucide-settings-2"
            />
          </UDropdownMenu>        
        </div>
      </div>

      <UTable
        ref="table"
        v-model:column-filters="columnFilters"
        v-model:column-visibility="columnVisibility"
        v-model:row-selection="rowSelection"
        v-model:pagination="pagination"
        :pagination-options="{
          getPaginationRowModel: getPaginationRowModel()
        }"
        class="shrink-0 mt-4"
        :data="farmerData"
        :columns="columns"
        :loading="status === 'pending'"
        :ui="{
          base: 'table-fixed border-separate border-spacing-0',
          thead: '[&>tr]:bg-elevated/50 [&>tr]:after:content-none',
          tbody: '[&>tr]:last:[&>td]:border-b-0',
          th: 'py-2 first:rounded-l-lg last:rounded-r-lg border-y border-default first:border-l last:border-r',
          td: 'border-b border-default',
          separator: 'h-0'
        }"
      />

      <div class="flex items-center justify-between gap-3 border-t border-default pt-4 mt-auto">
        <div class="text-sm text-muted">
          {{ table?.tableApi?.getFilteredSelectedRowModel().rows.length || 0 }} of
          {{ table?.tableApi?.getFilteredRowModel().rows.length || 0 }} row(s) selected.
        </div>

        <div class="flex items-center gap-1.5">
          <UPagination
            :default-page="(table?.tableApi?.getState().pagination.pageIndex || 0) + 1"
            :items-per-page="table?.tableApi?.getState().pagination.pageSize"
            :total="table?.tableApi?.getFilteredRowModel().rows.length"
            @update:page="(p: number) => table?.tableApi?.setPageIndex(p - 1)"
          />
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>
