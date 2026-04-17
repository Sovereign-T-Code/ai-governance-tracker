import { useMemo, useState } from 'react'
import { JURISDICTION_COLORS, STATUS_COLORS, JURISDICTION_LABELS } from '../utils/filters'

/**
 * Vertical timeline view — entries grouped by month, sorted descending.
 * Color-coded by jurisdiction. Pure CSS, no charting library.
 */

const ITEMS_PER_PAGE = 50

export default function Timeline({ entries }) {
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE)

  // Group entries by month
  const groups = useMemo(() => {
    const sorted = [...entries].sort(
      (a, b) => (b.date_last_action || '').localeCompare(a.date_last_action || '')
    )

    const map = new Map()
    for (const entry of sorted) {
      const date = entry.date_last_action || entry.date_introduced || ''
      const month = date ? date.slice(0, 7) : 'Unknown'
      const label = date
        ? new Date(date + 'T00:00:00').toLocaleDateString('en-CA', { year: 'numeric', month: 'long' })
        : 'Date Unknown'

      if (!map.has(month)) {
        map.set(month, { label, entries: [] })
      }
      map.get(month).entries.push(entry)
    }

    return [...map.values()]
  }, [entries])

  // Flatten for counting
  const totalVisible = useMemo(() => {
    let count = 0
    for (const g of groups) count += g.entries.length
    return count
  }, [groups])

  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        No entries match your filters.
      </div>
    )
  }

  let rendered = 0

  return (
    <div>
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-300 dark:bg-gray-700" />

        {groups.map((group) => {
          if (rendered >= visibleCount) return null

          return (
            <div key={group.label} className="mb-6">
              {/* Month header */}
              <div className="relative flex items-center mb-3 ml-4 pl-6">
                <div className="absolute left-[-4px] w-3 h-3 rounded-full bg-gray-400 dark:bg-gray-500" />
                <h3 className="text-sm font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  {group.label}
                </h3>
                <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
                  ({group.entries.length})
                </span>
              </div>

              {/* Entries for this month */}
              <div className="space-y-2 ml-4 pl-6">
                {group.entries.map((entry) => {
                  if (rendered >= visibleCount) return null
                  rendered++

                  const jurColors = JURISDICTION_COLORS[entry.jurisdiction_code] ||
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  const statusColors = STATUS_COLORS[entry.status] ||
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'

                  return (
                    <div
                      key={entry.id}
                      className="relative border border-gray-200 dark:border-gray-800 rounded p-3
                                 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors"
                    >
                      {/* Connector dot */}
                      <div className="absolute left-[-26px] top-4 w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400" />

                      {/* Title */}
                      <a
                        href={entry.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
                      >
                        {entry.title}
                      </a>

                      {/* Badges */}
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${jurColors}`}>
                          {JURISDICTION_LABELS[entry.jurisdiction_code] || entry.jurisdiction_code}
                        </span>
                        {entry.status && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${statusColors}`}>
                            {entry.status}
                          </span>
                        )}
                        {entry.domains?.map((d) => (
                          <span
                            key={d}
                            className="px-1.5 py-0.5 rounded text-[10px]
                                       bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                          >
                            {d}
                          </span>
                        ))}
                      </div>

                      {/* Date + source */}
                      <div className="mt-1 text-[10px] text-gray-400 dark:text-gray-500">
                        {entry.date_last_action || 'No date'} · {entry.source_name}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Load more button */}
      {rendered < totalVisible && (
        <div className="text-center mt-4">
          <button
            onClick={() => setVisibleCount((c) => c + ITEMS_PER_PAGE)}
            className="px-4 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded
                       hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Load more ({totalVisible - rendered} remaining)
          </button>
        </div>
      )}
    </div>
  )
}
