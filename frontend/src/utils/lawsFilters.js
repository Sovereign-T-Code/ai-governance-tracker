/**
 * Client-side filter logic for the Laws section.
 */

export function filterLaws(laws, filters) {
  let result = laws

  if (filters.q) {
    const q = filters.q.toLowerCase()
    result = result.filter((l) => {
      const text = `${l.title} ${l.summary} ${l.scope} ${l.short_title}`.toLowerCase()
      return text.includes(q)
    })
  }

  if (filters.jurisdiction?.length) {
    result = result.filter((l) => filters.jurisdiction.includes(l.jurisdiction_code))
  }

  if (filters.status?.length) {
    result = result.filter((l) => filters.status.includes(l.status))
  }

  if (filters.bindingType?.length) {
    result = result.filter((l) => filters.bindingType.includes(l.binding_type))
  }

  return result
}

export function extractLawFilterOptions(laws) {
  const jurisdictions = new Set()
  const statuses = new Set()
  const bindingTypes = new Set()

  for (const l of laws) {
    if (l.jurisdiction_code) jurisdictions.add(l.jurisdiction_code)
    if (l.status) statuses.add(l.status)
    if (l.binding_type) bindingTypes.add(l.binding_type)
  }

  return {
    jurisdictions: [...jurisdictions].sort(),
    statuses: [...statuses].sort(),
    bindingTypes: [...bindingTypes].sort(),
  }
}

export const BINDING_TYPE_LABELS = {
  binding: 'Binding',
  voluntary: 'Voluntary',
  guideline: 'Guideline',
}

export const BINDING_TYPE_COLORS = {
  binding: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  voluntary: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  guideline: 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200',
}
