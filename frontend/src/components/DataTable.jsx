import { useState, useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table'
import { JURISDICTION_COLORS, STATUS_COLORS, JURISDICTION_LABELS } from '../utils/filters'

const columnHelper = createColumnHelper()

const PAGE_SIZE = 25

/**
 * Main data table with sortable columns, pagination, and expandable rows.
 */
export default function DataTable({ entries }) {
  const [sorting, setSorting] = useState([{ id: 'date_last_action', desc: true }])
  const [expandedId, setExpandedId] = useState(null)

  const columns = useMemo(
    () => [
      columnHelper.accessor('title', {
        header: 'Title',
        cell: (info) => {
          const row = info.row.original
          return (
            <a
              href={row.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline"
              title={row.title}
            >
              {row.title.length > 80 ? row.title.slice(0, 77) + '...' : row.title}
            </a>
          )
        },
      }),
      columnHelper.accessor('jurisdiction_code', {
        header: 'Jurisdiction',
        cell: (info) => {
          const code = info.getValue()
          const colors = JURISDICTION_COLORS[code] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
          return (
            <span className={`inline-block px-2 py-0.5 rounded text-xs whitespace-nowrap ${colors}`}>
              {JURISDICTION_LABELS[code] || code}
            </span>
          )
        },
      }),
      columnHelper.accessor('status', {
        header: 'Status',
        cell: (info) => {
          const status = info.getValue()
          const colors = STATUS_COLORS[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
          return (
            <span className={`inline-block px-2 py-0.5 rounded text-xs whitespace-nowrap ${colors}`}>
              {status}
            </span>
          )
        },
      }),
      columnHelper.accessor('domains', {
        header: 'Domains',
        cell: (info) => {
          const domains = info.getValue() || []
          return (
            <div className="flex flex-wrap gap-1">
              {domains.map((d) => (
                <span
                  key={d}
                  className="inline-block px-1.5 py-0.5 rounded text-xs
                             bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                >
                  {d}
                </span>
              ))}
            </div>
          )
        },
        enableSorting: false,
      }),
      columnHelper.accessor('date_last_action', {
        header: 'Last Action',
        cell: (info) => (
          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
            {info.getValue() || '—'}
          </span>
        ),
      }),
    ],
    []
  )

  const table = useReactTable({
    data: entries,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: { pageSize: PAGE_SIZE },
    },
  })

  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        No entries match your filters.
      </div>
    )
  }

  return (
    <div>
      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 dark:border-gray-800 rounded">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-gray-200 dark:border-gray-800">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getCanSort() ? header.column.getToggleSortingHandler() : undefined}
                    className={`px-3 py-2 text-left text-xs font-medium uppercase tracking-wider
                               text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900
                               ${header.column.getCanSort() ? 'cursor-pointer select-none hover:text-gray-700 dark:hover:text-gray-200' : ''}`}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && ' ↑'}
                      {header.column.getIsSorted() === 'desc' && ' ↓'}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => {
              const entry = row.original
              const isExpanded = expandedId === entry.id
              return (
                <Fragment key={row.id}>
                  <tr
                    onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                    className="border-b border-gray-100 dark:border-gray-800/50
                               hover:bg-gray-50 dark:hover:bg-gray-900/50 cursor-pointer transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-3 py-2">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                  {isExpanded && (
                    <tr className="bg-gray-50 dark:bg-gray-900/70">
                      <td colSpan={columns.length} className="px-4 py-3">
                        <div className="space-y-2 text-xs">
                          {entry.summary && (
                            <div>
                              <span className="font-medium text-gray-500 dark:text-gray-400">Summary: </span>
                              <span>{entry.summary}</span>
                            </div>
                          )}
                          {entry.last_action_summary && (
                            <div>
                              <span className="font-medium text-gray-500 dark:text-gray-400">Last Action: </span>
                              <span>{entry.last_action_summary}</span>
                            </div>
                          )}
                          <div>
                            <span className="font-medium text-gray-500 dark:text-gray-400">Introduced: </span>
                            <span>{entry.date_introduced || '—'}</span>
                          </div>
                          <div>
                            <span className="font-medium text-gray-500 dark:text-gray-400">Source: </span>
                            <a
                              href={entry.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 dark:text-blue-400 hover:underline"
                            >
                              {entry.source_name} →
                            </a>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
        <span>
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()} ({entries.length} entries)
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-2 py-1 border border-gray-300 dark:border-gray-700 rounded
                       disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            ← Prev
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="px-2 py-1 border border-gray-300 dark:border-gray-700 rounded
                       disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  )
}

// Need Fragment for the expandable rows
import { Fragment } from 'react'
