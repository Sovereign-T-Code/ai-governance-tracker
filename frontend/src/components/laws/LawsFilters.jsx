import { JURISDICTION_LABELS, JURISDICTION_COLORS, STATUS_COLORS } from '../../utils/filters'
import { BINDING_TYPE_LABELS, BINDING_TYPE_COLORS } from '../../utils/lawsFilters'

function PillGroup({ label, options, active, onToggle, colorMap, labelMap }) {
  if (!options.length) return null
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-gray-500 dark:text-gray-400 shrink-0">{label}:</span>
      {options.map((opt) => {
        const isActive = active.includes(opt)
        const color = colorMap?.[opt] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
        const displayLabel = labelMap?.[opt] || opt
        return (
          <button
            key={opt}
            onClick={() => onToggle(opt)}
            className={`text-xs px-2 py-0.5 rounded font-medium transition-opacity border
              ${isActive
                ? `${color} border-transparent`
                : 'bg-transparent border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-400'
              }`}
          >
            {displayLabel}
          </button>
        )
      })}
    </div>
  )
}

export default function LawsFilters({ filters, options, onChange }) {
  function toggle(key, value) {
    onChange((prev) => {
      const arr = prev[key] || []
      const next = arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value]
      return { ...prev, [key]: next }
    })
  }

  const hasActive = !!(filters.jurisdiction?.length || filters.status?.length || filters.bindingType?.length)

  return (
    <div className="flex flex-col gap-2">
      <PillGroup
        label="Jurisdiction"
        options={options.jurisdictions}
        active={filters.jurisdiction || []}
        onToggle={(v) => toggle('jurisdiction', v)}
        colorMap={JURISDICTION_COLORS}
        labelMap={JURISDICTION_LABELS}
      />
      <PillGroup
        label="Status"
        options={options.statuses}
        active={filters.status || []}
        onToggle={(v) => toggle('status', v)}
        colorMap={STATUS_COLORS}
      />
      <PillGroup
        label="Type"
        options={options.bindingTypes}
        active={filters.bindingType || []}
        onToggle={(v) => toggle('bindingType', v)}
        colorMap={BINDING_TYPE_COLORS}
        labelMap={BINDING_TYPE_LABELS}
      />
      {hasActive && (
        <button
          onClick={() => onChange((prev) => ({ ...prev, jurisdiction: [], status: [], bindingType: [] }))}
          className="self-start text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
