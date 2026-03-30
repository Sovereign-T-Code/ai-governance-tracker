import { useState, useEffect } from 'react'

/**
 * Fetches entries.json and meta.json at load time.
 * All filtering/sorting happens client-side — no API calls on interaction.
 */
export default function useEntries() {
  const [entries, setEntries] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const base = import.meta.env.BASE_URL

    Promise.all([
      fetch(`${base}data/entries.json`).then((r) => {
        if (!r.ok) throw new Error(`entries.json: ${r.status}`)
        return r.json()
      }),
      fetch(`${base}data/meta.json`).then((r) => {
        if (!r.ok) throw new Error(`meta.json: ${r.status}`)
        return r.json()
      }),
    ])
      .then(([entriesData, metaData]) => {
        setEntries(entriesData)
        setMeta(metaData)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load data:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return { entries, meta, loading, error }
}
