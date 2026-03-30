/**
 * Tab group for switching between Table, Timeline, and News views.
 * Current view is stored in URL params via useFilterParams.
 */

const VIEWS = [
  { key: 'table', label: 'Table' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'news', label: 'News' },
]

export default function ViewToggle({ current, onChange }) {
  return (
    <div className="flex border border-gray-200 dark:border-gray-800 rounded overflow-hidden">
      {VIEWS.map((view) => (
        <button
          key={view.key}
          onClick={() => onChange(view.key)}
          className={`px-3 py-1.5 text-xs font-medium transition-colors
            ${current === view.key
              ? 'bg-blue-600 text-white'
              : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
        >
          {view.label}
        </button>
      ))}
    </div>
  )
}
