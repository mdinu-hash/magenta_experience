import React from 'react'

const WHY_BOXES = [
  'Trusted European provider',
  'Over 25 years of expertise',
  '1,500+ global AI and data experts',
  '28 billion+ data assets',
]

export default function FinalAnswer({ text }) {
  return (
    <div className="final-answer">
      <h2 className="final-answer__title">Why T-Systems</h2>

      <p className="final-answer__mission">
        Our mission is to help organizations not just use AI, but continuously
        improve it, delivering trustworthy, scalable, and high-impact solutions
        that drive productivity, innovation, and real business outcomes.
      </p>

      <div className="final-answer__boxes">
        {WHY_BOXES.map((box) => (
          <div key={box} className="final-answer__box">
            {box}
          </div>
        ))}
      </div>

      <div className="final-answer__agent-text">
        {text.split('\n').map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    </div>
  )
}
