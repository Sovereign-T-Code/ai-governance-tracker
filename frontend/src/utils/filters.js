/**
 * Client-side filter, sort, and search logic for entries.
 */

/**
 * Apply all active filters to the entries array.
 */
export function filterEntries(entries, filters) {
  let result = entries

  // Full-text search
  if (filters.q) {
    const q = filters.q.toLowerCase()
    result = result.filter((e) => {
      const text = `${e.title} ${e.summary} ${e.last_action_summary}`.toLowerCase()
      return text.includes(q)
    })
  }

  // Jurisdiction filter
  if (filters.jurisdiction?.length) {
    result = result.filter((e) => filters.jurisdiction.includes(e.jurisdiction_code))
  }

  // Status filter
  if (filters.status?.length) {
    result = result.filter((e) => filters.status.includes(e.status))
  }

  // Domain filter (entry matches if any of its domains are selected)
  if (filters.domain?.length) {
    result = result.filter((e) =>
      e.domains?.some((d) => filters.domain.includes(d))
    )
  }

  // Date range filter on date_last_action
  if (filters.from) {
    result = result.filter((e) => e.date_last_action >= filters.from)
  }
  if (filters.to) {
    result = result.filter((e) => e.date_last_action <= filters.to)
  }

  return result
}

/**
 * Extract unique values for filter dropdowns from the entries data.
 */
export function extractFilterOptions(entries) {
  const jurisdictions = new Set()
  const statuses = new Set()
  const domains = new Set()

  for (const e of entries) {
    if (e.jurisdiction_code) jurisdictions.add(e.jurisdiction_code)
    if (e.status) statuses.add(e.status)
    if (e.domains) e.domains.forEach((d) => domains.add(d))
  }

  return {
    jurisdictions: [...jurisdictions].sort(),
    statuses: [...statuses].sort(),
    domains: [...domains].sort(),
  }
}

/** Map jurisdiction codes to display labels */
export const JURISDICTION_LABELS = {
  'CA-FED': 'Canada — Federal',
  'CA-ON': 'Canada — Ontario',
  'CA-QC': 'Canada — Quebec',
  'US-FED': 'United States — Federal',
  'EU': 'European Union',
  'INTL': 'International',
}

/** Colors for jurisdiction badges */
export const JURISDICTION_COLORS = {
  'CA-FED': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'CA-ON': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'CA-QC': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'US-FED': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'EU': 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
}

/** Colors for status badges */
export const STATUS_COLORS = {
  'Proposed': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  'In Progress': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'Passed/Adopted': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  'In Force': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  'Withdrawn/Defeated': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
}
