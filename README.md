# magenta_experience

An AI assistant for T-Systems that engages customers in a short conversation to understand their needs, then recommends the most relevant AI solutions from the T-Systems portfolio with personalized reasoning.

# Stack

Frontend: React
Backend: Python + FastAPI
Streaming: SSE (server-sent events)
Agent framework: LangGraph
LLM: anthropic API (sonnet 4.6 - The best combination of speed and intelligence)
Deployment: digitalocean
Observability: langsmith

# Data layer

11 solutions. ex of signature:

{
    'title':'Industrial AI Cloud',
    'link': 'https://www.t-systems.com/de/en/artificial-intelligence/solutions/industrial-ai-cloud',
    'content':"""
The cloud for industrial AI – fast, sovereign, and scalable.
Are you looking for a powerful and sovereign AI platform?
With the Industrial AI Cloud, we – together with NVIDIA – offer a high-performance AI cloud for enterprises, research institutions, and the public sector. The platform is independent, GDPR-compliant, and meets all requirements of the EU AI Act.

Do these challenges sound familiar?
Industrial AI requires massive computing power, valid data, reliable platforms, security, compliance and control
Industrial AI use in Europe is predominantly based on US or Chinese models with risky dependencies
Rapid development of AI infrastructure under European law needed

How we solve your problem:
The Industrial AI Cloud provides access to extensive GPU resources for the training, development and operation of AI models
It is suited for compute-intensive applications such as 3D graphics, digital twins, and metaverse scenarios
Thanks to high-speed connectivity and flexible booking models, the Industrial AI Cloud supports both pilot projects and mission-critical production systems

Germany’s AI infrastructure: powerful, sovereign, scalable
10.000 GPUs: boost Germany’s AI compute power by 50%
Unique time-to-market: immediately available and quickly scalable
Maximum sovereignty: due to the highest safety and quality requirements according to German and European law
Cost efficient: cheaper than building it yourself, pricing on eye level with the hyperscalers

Your benefits: maximum performance without compromise
Deutsche Telekom and NVIDIA unite to deliver a sovereign, high-performance AI cloud for Europe’s industrial and regulated sectors—powered by NVIDIA hardware, renewable energy, and trusted EU infrastructure—enabling AI training, digital twins, and automation at scale.

AI sovereignty for Europe - now available for all industries
Benefit from the latest NVIDIA technology and the experience of a European provider that ensures maximum sovereignty.
"""
}

# Agentic AI layer

```
                             [BEGIN]
                                │
                                ▼
                    ┌────────────────────────┐
             ┌─────►│      orchestrator      │
             │      │ ───────────────────── │
             │      │  Decide: clarify or    │
             │      │  recommend?            │
             │      └───────────┬────────────┘
             │                  │
             │       ┌──────────┴──────────┐
             │       │                     │
             │    CLARIFY             RECOMMEND
             │       │                     │
             │       ▼                     ▼
             │  ┌─────────────┐   ┌─────────────────────┐
             │  │ ask_question│   │   generate_answer   │
             │  │ ─────────── │   │ ─────────────────── │
             │  │  Generate   │   │  Create structured  │
             │  │  clarifying │   │  answer             │
             │  │  question   │   └──────────┬──────────┘
             │  └──────┬──────┘              │
             │         │                     │
             │  Reuse Thread                 ▼
             └─────────┘                   [END]
              Human In The Loop
```

# Structured output

1) Why T-Systems

2) Recommended T-Systems solutions

3) Why

