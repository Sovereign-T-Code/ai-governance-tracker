import { useState, useEffect, useRef } from 'react'

/**
 * Debounced full-text search bar.
 * Searches across title, summary, and last_action_summary.
 */
export default function SearchBar({ value, onChange }) {
  const [local, setLocal] = useState(value)
  const timerRef = useRef(null)

  // Sync external value changes
  useEffect(() => {
    setLocal(value)
  }, [value])

  const handleChange = (e) => {
    const val = e.target.value
    setLocal(val)

    // Debounce 300ms
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      onChange(val)
    }, 300)
  }

  return (
    <div className="w-full">
      <input
        type="text"
        value={local}
        onChange={handleChange}
        placeholder="Search entries..."
        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded
                   bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100
                   placeholder-gray-400 dark:placeholder-gray-500
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  )
}
