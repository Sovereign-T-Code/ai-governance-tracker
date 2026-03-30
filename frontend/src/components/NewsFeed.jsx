import { useState, useMemo } from 'react'
import { JURISDICTION_COLORS, JURISDICTION_LABELS } from '../utils/filters'

/**
 * News articles card layout — shows type="news" entries.
 * Sorted by date, most recent first.
 */

const ITEMS_PER_PAGE = 30

export default function NewsFeed({ entries }) {
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE)

  const newsEntries = useMemo(
    () =>
      entries
        .filter((e) => e.type === 'news')
        .sort((a, b) => (b.date_last_action || '').localeCompare(a.date_last_action || '')),
    [entries]
  )

  if (newsEntries.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        No news articles match your filters.
      </div>
    )
  }

  const visible = newsEntries.slice(0, visibleCount)

  return (
    <div>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {visible.map((entry) => {
          const jurColors = JURISDICTION_COLORS[entry.jurisdiction_code] ||
            'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'

          return (
            <article
              key={entry.id}
              className="border border-gray-200 dark:border-gray-800 rounded p-3
                         hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors
                         flex flex-col"
            >
              {/* Source + date */}
              <div className="text-[10px] text-gray-400 dark:text-gray-500 mb-1">
                {entry.source_name} · {entry.date_last_action || 'No date'}
              </div>

              {/* Title */}
              <a
                href={entry.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium leading-snug"
              >
                {entry.title}
              </a>

              {/* Summary snippet */}
              {entry.summary && entry.summary !== entry.title && (
                <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-3">
                  {entry.summary}
                </p>
              )}

              {/* Badges */}
              <div className="flex flex-wrap gap-1 mt-auto pt-2">
                <span className={`px-1.5 py-0.5 rounded text-[10px] ${jurColors}`}>
                  {JURISDICTION_LABELS[entry.jurisdiction_code] || entry.jurisdiction}
                </span>
                {entry.domains?.filter(d => d !== 'General').map((d) => (
                  <span
                    key={d}
                    className="px-1.5 py-0.5 rounded text-[10px]
                               bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                  >
                    {d}
                  </span>
                ))}
              </div>
            </article>
          )
        })}
      </div>

      {/* Load more */}
      {visibleCount < newsEntries.length && (
        <div className="text-center mt-4">
          <button
            onClick={() => setVisibleCount((c) => c + ITEMS_PER_PAGE)}
            className="px-4 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded
                       hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Load more ({newsEntries.length - visibleCount} remaining)
          </button>
        </div>
      )}
    </div>
  )
}
