import { useState, useCallback } from 'react'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [threadId, setThreadId] = useState(null)
  const [loading, setLoading] = useState(false)

  const addMessage = (msg) =>
    setMessages((prev) => [...prev, msg])

  const updateProgress = (text) =>
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (last?.role === 'progress') {
        return [...prev.slice(0, -1), { role: 'progress', text }]
      }
      return [...prev, { role: 'progress', text }]
    })

  const removeProgress = () =>
    setMessages((prev) => prev.filter((m) => m.role !== 'progress'))

  const sendMessage = useCallback(
    async (text) => {
      addMessage({ role: 'user', text })
      setLoading(true)

      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, thread_id: threadId }),
        })

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split('\n\n')
          buffer = parts.pop() // keep any incomplete trailing chunk

          for (const part of parts) {
            const lines = part.split('\n')
            const eventLine = lines.find((l) => l.startsWith('event:'))
            const dataLine = lines.find((l) => l.startsWith('data:'))
            if (!eventLine || !dataLine) continue

            const event = eventLine.replace('event:', '').trim()
            const data = JSON.parse(dataLine.replace('data:', '').trim())

            if (event === 'progress') {
              updateProgress(data.text)
            } else if (event === 'question') {
              removeProgress()
              addMessage({ role: 'agent', text: data.text })
              setThreadId(data.thread_id)
            } else if (event === 'answer') {
              removeProgress()
              addMessage({ role: 'answer', text: data.text })
            } else if (event === 'error') {
              removeProgress()
              addMessage({ role: 'error', text: data.text })
            }
          }
        }
      } catch (err) {
        removeProgress()
        addMessage({ role: 'error', text: err.message })
      } finally {
        setLoading(false)
      }
    },
    [threadId]
  )

  const clearChat = useCallback(() => {
    setMessages([])
    setThreadId(null)
  }, [])

  return { messages, loading, sendMessage, clearChat }
}
