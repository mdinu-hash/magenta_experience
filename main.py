import json
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command
from pydantic import BaseModel

from agent import create_config, graph

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Magenta Experience API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to frontend origin in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NODE_LABELS = {
    "reset_state": "Thinking...",
    "orchestrator": "Personalizing...",
    "ask_question": "Clarifying...",
    "generate_answer": "Building recommendation...",
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_chat(message: str, thread_id: Optional[str]):
    """Generator that runs the LangGraph and yields SSE-formatted strings.

    First call  (thread_id=None): starts a new thread.
    Follow-up   (thread_id=str):  resumes the graph after an interrupt.

    SSE event types emitted:
        progress  {"text": "Thinking..."}          — node execution label
        question  {"text": "...", "thread_id": "..."} — clarifying question + id for resume
        answer    {"text": "..."}                  — final recommendation string
        error     {"text": "..."}                  — any exception
    """
    try:
        if thread_id:
            config, thread_id = create_config("Run", thread_id=thread_id)
            graph_input = Command(resume=message)
        else:
            config, thread_id = create_config("Run", is_new_thread=True)
            graph_input = {"current_user_message": message}

        for chunk in graph.stream(input=graph_input, config=config, stream_mode="updates"):
            node_name = list(chunk.keys())[0]
            if node_name in NODE_LABELS:
                yield sse("progress", {"text": NODE_LABELS[node_name]})

        # Stream exhausted — inspect final state
        state = graph.get_state(config)

        if state.next:
            # Graph is paused at interrupt() inside ask_question
            question = state.tasks[0].interrupts[0].value
            yield sse("question", {"text": question, "thread_id": thread_id})
        else:
            # Graph reached END
            yield sse("answer", {"text": state.values["final_answer"]})

    except Exception as e:
        yield sse("error", {"text": str(e)})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/chat")
def chat(req: ChatRequest):
    return StreamingResponse(
        stream_chat(req.message, req.thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables Nginx response buffering
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve React app — must be mounted last so API routes take priority
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
