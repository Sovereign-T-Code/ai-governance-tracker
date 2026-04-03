import { useState } from 'react'
import { STATUS_COLORS, JURISDICTION_LABELS, JURISDICTION_COLORS } from '../../utils/filters'
import { BINDING_TYPE_LABELS, BINDING_TYPE_COLORS } from '../../utils/lawsFilters'

function formatDate(dateStr) {
  if (!dateStr) return null
  return new Date(dateStr).toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const PROVISIONS_PREVIEW = 3

export default function LawCard({ law }) {
  const [expanded, setExpanded] = useState(false)
  const [provisionsExpanded, setProvisionsExpanded] = useState(false)

  const jurisdictionColor = JURISDICTION_COLORS[law.jurisdiction_code] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
  const jurisdictionLabel = JURISDICTION_LABELS[law.jurisdiction_code] || law.jurisdiction
  const statusColor = STATUS_COLORS[law.status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
  const bindingColor = BINDING_TYPE_COLORS[law.binding_type] || 'bg-gray-100 text-gray-800'
  const bindingLabel = BINDING_TYPE_LABELS[law.binding_type] || law.binding_type

  const provisions = law.key_provisions || []
  const visibleProvisions = provisionsExpanded ? provisions : provisions.slice(0, PROVISIONS_PREVIEW)
  const hiddenCount = provisions.length - PROVISIONS_PREVIEW

  return (
    <div className="border border-gray-200 dark:border-gray-800 rounded-lg p-5 flex flex-col gap-3 bg-white dark:bg-gray-900">
      {/* Badge row */}
      <div className="flex flex-wrap gap-1.5">
        <span className={`text-xs font-medium px-2 py-0.5 rounded ${jurisdictionColor}`}>
          {jurisdictionLabel}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusColor}`}>
          {law.status}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded ${bindingColor}`}>
          {bindingLabel}
        </span>
      </div>

      {/* Title */}
      <div>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 leading-snug">
          {law.title}
        </h2>
        {law.scope && (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
            {law.scope}
          </p>
        )}
      </div>

      {/* Meta row */}
      <div className="flex flex-col gap-0.5 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-800 pt-3">
        {law.date_in_force && (
          <span>In force: <span className="text-gray-700 dark:text-gray-300">{formatDate(law.date_in_force)}</span></span>
        )}
        {law.date_last_amended && (
          <span>Last amended: <span className="text-gray-700 dark:text-gray-300">{formatDate(law.date_last_amended)}</span></span>
        )}
        {law.enforcement_body && (
          <span>Enforced by: <span className="text-gray-700 dark:text-gray-300">{law.enforcement_body}</span></span>
        )}
      </div>

      {/* Key provisions */}
      {provisions.length > 0 && (
        <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
          <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Key provisions</p>
          <ul className="space-y-1">
            {visibleProvisions.map((p, i) => (
              <li key={i} className="text-xs text-gray-600 dark:text-gray-400 flex gap-2">
                <span className="mt-0.5 shrink-0 text-gray-400">•</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
          {!provisionsExpanded && hiddenCount > 0 && (
            <button
              onClick={() => setProvisionsExpanded(true)}
              className="mt-1.5 text-xs text-blue-600 dark:text-blue-400 hover:underline"
            >
              + {hiddenCount} more
            </button>
          )}
        </div>
      )}

      {/* Expanded detail panel */}
      {expanded && (
        <div className="border-t border-gray-100 dark:border-gray-800 pt-3 space-y-2 text-xs text-gray-600 dark:text-gray-400">
          {law.commencement_notes && (
            <div>
              <p className="font-medium text-gray-700 dark:text-gray-300 mb-0.5">Commencement</p>
              <p className="leading-relaxed">{law.commencement_notes}</p>
            </div>
          )}
          {law.applies_to?.length > 0 && (
            <div>
              <p className="font-medium text-gray-700 dark:text-gray-300 mb-0.5">Applies to</p>
              <ul className="space-y-0.5">
                {law.applies_to.map((a, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-0.5 shrink-0 text-gray-400">•</span>
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {law.penalty_range && (
            <div>
              <p className="font-medium text-gray-700 dark:text-gray-300 mb-0.5">Penalties</p>
              <p>{law.penalty_range}</p>
            </div>
          )}
        </div>
      )}

      {/* Action row */}
      <div className="flex items-center justify-between border-t border-gray-100 dark:border-gray-800 pt-3 mt-auto">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
        >
          {expanded ? 'Hide details ↑' : 'Show details ↓'}
        </button>
        <a
          href={law.official_text_url || law.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          Official text →
        </a>
      </div>
    </div>
  )
}
