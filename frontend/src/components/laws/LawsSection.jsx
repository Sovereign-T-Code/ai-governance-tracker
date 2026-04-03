import { useState, useMemo } from 'react'
import useLaws from '../../hooks/useLaws'
import { filterLaws, extractLawFilterOptions } from '../../utils/lawsFilters'
import LawCard from './LawCard'
import LawsFilters from './LawsFilters'

const DEFAULT_FILTERS = {
  q: '',
  jurisdiction: [],
  status: [],
  bindingType: [],
}

export default function LawsSection() {
  const { laws, loading, error } = useLaws()
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

  const options = useMemo(() => extractLawFilterOptions(laws), [laws])
  const filtered = useMemo(() => filterLaws(laws, filters), [laws, filters])

  if (loading) {
    return (
      <div className="py-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Loading laws...
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-12 text-center text-red-500 text-sm">
        Failed to load laws: {error}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <input
        type="search"
        placeholder="Search laws..."
        value={filters.q}
        onChange={(e) => setFilters((prev) => ({ ...prev, q: e.target.value }))}
        className="w-full max-w-md px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />

      {/* Filters */}
      <LawsFilters filters={filters} options={options} onChange={setFilters} />

      {/* Count */}
      <div className="text-xs text-gray-500 dark:text-gray-400">
        Showing {filtered.length} of {laws.length} laws
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="py-12 text-center text-gray-400 dark:text-gray-500 text-sm">
          No laws match your filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((law) => (
            <LawCard key={law.id} law={law} />
          ))}
        </div>
      )}
    </div>
  )
}
