import { useMemo } from 'react'
import useEntries from './hooks/useEntries'
import useFilterParams from './hooks/useFilterParams'
import { filterEntries, extractFilterOptions } from './utils/filters'
import DataTable from './components/DataTable'
import Timeline from './components/Timeline'
import NewsFeed from './components/NewsFeed'
import ViewToggle from './components/ViewToggle'
import SearchBar from './components/SearchBar'
import Filters from './components/Filters'
import ThemeToggle from './components/ThemeToggle'

export default function App() {
  const { entries, meta, loading, error } = useEntries()
  const { filters, setFilters, toggleArrayFilter, clearFilters } = useFilterParams()

  // Extract filter options from all entries (not filtered ones)
  const options = useMemo(() => extractFilterOptions(entries), [entries])

  // Apply filters
  const filtered = useMemo(() => filterEntries(entries, filters), [entries, filters])

  const currentView = filters.view || 'table'

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500 dark:text-gray-400">
        Loading...
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center text-red-500">
        Failed to load data: {error}
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <h1 className="text-lg font-bold whitespace-nowrap">AI Governance Tracker</h1>
          <div className="flex-1 max-w-md">
            <SearchBar
              value={filters.q}
              onChange={(q) => setFilters((prev) => ({ ...prev, q }))}
            />
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 px-4 py-4">
        <div className="max-w-7xl mx-auto space-y-4">
          {/* View toggle + Filters row */}
          <div className="flex flex-col sm:flex-row sm:items-start gap-3">
            <ViewToggle
              current={currentView}
              onChange={(view) => setFilters((prev) => ({ ...prev, view }))}
            />
            <div className="flex-1">
              <Filters
                filters={filters}
                toggleArrayFilter={toggleArrayFilter}
                setFilters={setFilters}
                options={options}
                clearFilters={clearFilters}
              />
            </div>
          </div>

          {/* Entry count */}
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Showing {filtered.length} of {entries.length} entries
          </div>

          {/* Active view */}
          {currentView === 'table' && <DataTable entries={filtered} />}
          {currentView === 'timeline' && <Timeline entries={filtered} />}
          {currentView === 'news' && <NewsFeed entries={filtered} />}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 px-4 py-3 text-xs text-gray-400 dark:text-gray-500">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span>
            Last updated: {meta?.last_run
              ? new Date(meta.last_run).toLocaleDateString('en-CA', {
                  year: 'numeric', month: 'short', day: 'numeric',
                  hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
                })
              : 'Unknown'}
          </span>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-gray-600 dark:hover:text-gray-300"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  )
}
