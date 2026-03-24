import React, { useState, useRef, useEffect } from 'react'
import { useChat } from './hooks/useChat'
import FinalAnswer from './components/FinalAnswer'

export default function App() {
  const { messages, loading, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <span className="header__logo">T-Systems</span>
        <button className="header__clear" onClick={clearChat}>
          Clear Chat
        </button>
      </header>

      {/* Chat window */}
      <main className="chat-window">
        {messages.length === 0 && (
          <div className="chat-window__empty">
            Please briefly describe your problem.
          </div>
        )}

        {messages.map((msg, i) => {
          if (msg.role === 'answer') {
            return <FinalAnswer key={i} text={msg.text} />
          }
          return (
            <div key={i} className={`message message--${msg.role}`}>
              {msg.text}
            </div>
          )
        })}

        <div ref={bottomRef} />
      </main>

      {/* Input bar */}
      <form className="input-bar" onSubmit={handleSubmit}>
        <input
          className="input-bar__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
          autoFocus
        />
        <button
          className="input-bar__btn"
          type="submit"
          disabled={loading || !input.trim()}
        >
          {loading ? '…' : '→'}
        </button>
      </form>
    </div>
  )
}
