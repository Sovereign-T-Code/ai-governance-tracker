import { useState, useEffect } from 'react'

/**
 * Fetches laws.json at load time.
 * Lazy — only called when the Laws section is first rendered.
 */
export default function useLaws() {
  const [laws, setLaws] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const base = import.meta.env.BASE_URL

    fetch(`${base}data/laws.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`laws.json: ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setLaws(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load laws:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return { laws, loading, error }
}
