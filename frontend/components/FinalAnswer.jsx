const WHY_BOXES = [
  'Trusted European provider',
  'Over 25 years of expertise',
  '1,500+ global AI and data experts',
  '28 billion+ data assets',
]

export default function FinalAnswer({ text }) {
  const data = JSON.parse(text)

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

      <h3 className="final-answer__section-title">Solutions Recommended</h3>
      <ul className="final-answer__solutions">
        {data.solutions.map((sol) => (
          <li key={sol.title} className="final-answer__solution">
            <span className="final-answer__solution-title">{sol.title}</span>
            <p className="final-answer__solution-summary">{sol.summary}</p>
          </li>
        ))}
      </ul>

      <h3 className="final-answer__section-title">Why</h3>
      <ul className="final-answer__whys">
        {data.solutions.map((sol) => (
          <li key={sol.title} className="final-answer__why">
            {sol.why}
          </li>
        ))}
      </ul>
    </div>
  )
}
