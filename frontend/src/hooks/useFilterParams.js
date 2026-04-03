import { useState, useCallback, useEffect } from 'react'

/**
 * Custom hook that syncs filter state with URL query parameters.
 * Filters persist in the URL so views are shareable and bookmarkable.
 *
 * Param format:
 *   ?q=term&jurisdiction=CA-FED,US-FED&status=Proposed&domain=Privacy&from=2025-01-01&to=2025-12-31&view=table
 */

const ARRAY_PARAMS = ['jurisdiction', 'status', 'domain']
const STRING_PARAMS = ['q', 'from', 'to', 'view', 'section']

function parseParams() {
  const params = new URLSearchParams(window.location.search)
  const result = {}

  for (const key of ARRAY_PARAMS) {
    const val = params.get(key)
    result[key] = val ? val.split(',').filter(Boolean) : []
  }

  for (const key of STRING_PARAMS) {
    result[key] = params.get(key) || ''
  }

  return result
}

function buildSearch(filters) {
  const params = new URLSearchParams()

  for (const key of ARRAY_PARAMS) {
    if (filters[key]?.length) {
      params.set(key, filters[key].join(','))
    }
  }

  for (const key of STRING_PARAMS) {
    if (filters[key]) {
      params.set(key, filters[key])
    }
  }

  const str = params.toString()
  return str ? `?${str}` : ''
}

const DEFAULT_FILTERS = {
  q: '',
  jurisdiction: [],
  status: [],
  domain: [],
  from: '',
  to: '',
  view: 'table',
  section: '',
}

export default function useFilterParams() {
  const [filters, setFiltersState] = useState(() => {
    const parsed = parseParams()
    return { ...DEFAULT_FILTERS, ...parsed }
  })

  const setFilters = useCallback((updater) => {
    setFiltersState((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : { ...prev, ...updater }
      return next
    })
  }, [])

  // Sync filters -> URL (replaceState to avoid polluting history)
  useEffect(() => {
    const search = buildSearch(filters)
    const currentSearch = window.location.search || ''
    if (search !== currentSearch) {
      window.history.replaceState(null, '', window.location.pathname + search)
    }
  }, [filters])

  const toggleArrayFilter = useCallback((key, value) => {
    setFilters((prev) => {
      const arr = prev[key] || []
      const next = arr.includes(value)
        ? arr.filter((v) => v !== value)
        : [...arr, value]
      return { ...prev, [key]: next }
    })
  }, [setFilters])

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS)
  }, [setFilters])

  return { filters, setFilters, toggleArrayFilter, clearFilters }
}
