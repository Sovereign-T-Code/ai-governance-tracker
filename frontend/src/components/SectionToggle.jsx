/**
 * Top-level section switcher: "Tracker" vs "Laws".
 */

const SECTIONS = [
  { key: '', label: 'Tracker' },
  { key: 'laws', label: 'Laws' },
]

export default function SectionToggle({ current, onChange }) {
  return (
    <div className="flex border border-gray-200 dark:border-gray-800 rounded overflow-hidden">
      {SECTIONS.map((s) => (
        <button
          key={s.key}
          onClick={() => onChange(s.key)}
          className={`px-3 py-1.5 text-xs font-medium transition-colors
            ${current === s.key
              ? 'bg-blue-600 text-white'
              : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
        >
          {s.label}
        </button>
      ))}
    </div>
  )
}
