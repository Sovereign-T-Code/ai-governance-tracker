import { useState } from 'react'
import { JURISDICTION_LABELS } from '../utils/filters'

/**
 * Multi-select filter panel for jurisdiction, status, and domain.
 * Plus date range inputs. Collapsible on mobile.
 */
export default function Filters({ filters, toggleArrayFilter, setFilters, options, clearFilters }) {
  const [open, setOpen] = useState(false)

  const hasActiveFilters =
    filters.jurisdiction.length > 0 ||
    filters.status.length > 0 ||
    filters.domain.length > 0 ||
    filters.from ||
    filters.to

  return (
    <div className="border border-gray-200 dark:border-gray-800 rounded">
      {/* Toggle button for mobile */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium
                   hover:bg-gray-50 dark:hover:bg-gray-900 md:hidden"
      >
        <span>
          Filters
          {hasActiveFilters && (
            <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">(active)</span>
          )}
        </span>
        <span>{open ? '▲' : '▼'}</span>
      </button>

      {/* Filter content — always visible on desktop, toggle on mobile */}
      <div className={`p-3 space-y-4 ${open ? '' : 'hidden'} md:block`}>
        <div className="flex flex-wrap gap-6">
          {/* Jurisdiction */}
          <FilterGroup
            label="Jurisdiction"
            options={options.jurisdictions}
            selected={filters.jurisdiction}
            onToggle={(v) => toggleArrayFilter('jurisdiction', v)}
            labelMap={JURISDICTION_LABELS}
          />

          {/* Status */}
          <FilterGroup
            label="Status"
            options={options.statuses}
            selected={filters.status}
            onToggle={(v) => toggleArrayFilter('status', v)}
          />

          {/* Domain */}
          <FilterGroup
            label="Domain"
            options={options.domains}
            selected={filters.domain}
            onToggle={(v) => toggleArrayFilter('domain', v)}
          />

          {/* Date range */}
          <div className="space-y-1">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Date Range
            </div>
            <div className="flex items-center gap-2 text-sm">
              <input
                type="date"
                value={filters.from}
                onChange={(e) => setFilters((prev) => ({ ...prev, from: e.target.value }))}
                className="px-2 py-1 border border-gray-300 dark:border-gray-700 rounded text-xs
                           bg-white dark:bg-gray-900"
              />
              <span className="text-gray-400">to</span>
              <input
                type="date"
                value={filters.to}
                onChange={(e) => setFilters((prev) => ({ ...prev, to: e.target.value }))}
                className="px-2 py-1 border border-gray-300 dark:border-gray-700 rounded text-xs
                           bg-white dark:bg-gray-900"
              />
            </div>
          </div>
        </div>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Clear all filters
          </button>
        )}
      </div>
    </div>
  )
}

function FilterGroup({ label, options, selected, onToggle, labelMap }) {
  return (
    <div className="space-y-1">
      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {label}
      </div>
      <div className="flex flex-wrap gap-1">
        {options.map((opt) => {
          const isActive = selected.includes(opt)
          return (
            <button
              key={opt}
              onClick={() => onToggle(opt)}
              className={`px-2 py-0.5 text-xs rounded-full border transition-colors
                ${isActive
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-transparent text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
            >
              {labelMap?.[opt] || opt}
            </button>
          )
        })}
      </div>
    </div>
  )
}
