import datetime
import json
import os
import uuid
from typing import Annotated, Any, Literal, Optional, Sequence

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from pydantic import BaseModel
from typing_extensions import TypedDict

from data_layer import solutions as ALL_SOLUTIONS

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# langsmith
LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY')
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGSMITH_ENDPOINT'] = "https://api.smith.langchain.com"
langsmith_project_name = "magenta-experience"
os.environ['LANGSMITH_PROJECT'] = langsmith_project_name

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

SolutionTitle = Literal[
    "Industrial AI Cloud",
    "AI Solution Factory",
    "AI Foundation Services",
    "Artificial Intelligence and Data Analytics",
    "AI on Google Cloud",
    "UiPath AI-as-a-Service",
    "Big Data Analytics",
    "Data Intelligence Hub",
    "Data Spaces",
    "Data Mesh",
    "Magenta Digital Product Passport",
]


GREETING = "Please briefly describe your problem."


class AgentState(TypedDict):
    current_user_message: str           # first message at invocation; subsequent answers via interrupt()
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
    solutions: list[dict]               # all 11: title + content
    is_question_needed: bool
    nr_questions_asked: int             # capped at 3
    recommended_solutions: list[dict]   # titles selected by orchestrator
    final_answer: Optional[str]          # formatted answer shown to the user


class OrchestratorOutput(TypedDict):
    is_question_needed: bool
    recommended_solution_titles: list[SolutionTitle]  # 1–2 items


class SolutionAnswerModel(BaseModel):
    title: str
    summary: str   # 1–3 sentences from solution content
    why: str       # 1–2 sentences: why this customer needs it


class FinalOutputModel(BaseModel):
    solutions: list[SolutionAnswerModel]


class QuestionOutput(BaseModel):
    question: str


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_chat_history(chat_history: Sequence[BaseMessage]) -> str:
    """Convert a list of BaseMessages into a plain Human/AI dialogue string."""
    parts = []
    for m in chat_history:
        if isinstance(m, HumanMessage):
            parts.append(f"Human: {m.content}")
        elif isinstance(m, AIMessage):
            parts.append(f"AI: {m.content}")
    return "\n".join(parts)


def create_solutions_list(solutions: list[dict]) -> str:
    """Format all solutions as a numbered list of title + full content."""
    return "\n".join(f"- {s['title']}: {s['content']}" for s in solutions)

def create_config(run_name: str, is_new_thread: bool = False, thread_id: str = None):
    """Create a config dict for LangGraph graph invocations.

    Args:
        run_name:      Descriptive name shown in LangSmith (timestamp appended).
        is_new_thread: True  → generate a fresh thread_id (new conversation).
                       False → reuse the provided thread_id (resume conversation).
        thread_id:     Existing thread_id to reuse. Ignored when is_new_thread=True.

    Returns:
        (config, thread_id)

    Examples:
        config, thread_id = create_config("magenta_agent", is_new_thread=True)
        config, _ = create_config("magenta_agent", thread_id=thread_id)
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    full_run_name = f"{run_name} {timestamp}"

    if is_new_thread or not thread_id:
        thread_id = str(uuid.uuid4())

    config = {
        "run_name": full_run_name,
        "configurable": {"thread_id": thread_id},
    }

    return config, thread_id


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def reset_state(state: AgentState) -> dict:
    """Initialise the conversation state.

    The graph is invoked with {"current_user_message": "<user text>"}.
    reset_state builds the opening chat_history as:
        AIMessage:    GREETING ("Please briefly describe your problem.")
        HumanMessage: current_user_message

    Subsequent human turns are captured via interrupt() inside ask_question,
    which also appends both the AI question and the user's answer to chat_history.
    """
    return {
        "current_user_message": state["current_user_message"],
        "chat_history": [
            AIMessage(content=GREETING),
            HumanMessage(content=state["current_user_message"]),
        ],
        "solutions": ALL_SOLUTIONS,
        "nr_questions_asked": 0,
        "is_question_needed": True,
        "recommended_solutions": [],
        "final_answer": None,
    }


def orchestrator(state: AgentState) -> dict:
    """Decide whether to ask another clarifying question or recommend solutions.

    Flow:
    1. If nr_questions_asked >= 3, skip the LLM and force is_question_needed=False.
    2. Otherwise, run the LLM chain with the full solution portfolio and conversation
       history to get a structured decision.
    3. If asking a question, increment nr_questions_asked in the returned state.
    4. If recommending, store the selected solution titles in recommended_solutions.

    LangGraph automatically merges the returned dict into AgentState.
    """
    # Programmatic cap — no LLM call needed
    if state["nr_questions_asked"] >= 3:
        return {"is_question_needed": False}

    prompt = ChatPromptTemplate.from_template(
        """You are an expert T-Systems solution advisor.
Your job is to decide whether you need to ask one more clarifying question to the customer,
or whether you have enough information to recommend 1–2 solutions from the portfolio.

Available portfolio solutions:
{solutions}

Conversation so far:
{chat_history}

Step 1: Decide whether you have enough information to recommend 1–2 solutions from the portfolio.
If you have enough context to make a confident recommendation, set is_question_needed = false,
otherwise if more context is needed, set it to true.

Step 2: If is_question_needed = false, list your recommended 1-2 portfolio solution titles.
Important: Include just the titles.

Output:
- is_question_needed: false or true.
- recommended_solution_titles: your recommended 1-2 solution titles. Empty list if is_question_needed = true."""
    )

    chain = prompt | llm.with_structured_output(OrchestratorOutput)
    result = chain.invoke({
        "solutions": create_solutions_list(state["solutions"]),
        "chat_history": create_chat_history(state["chat_history"]),
    })

    updates = {"is_question_needed": result["is_question_needed"]}

    if result["is_question_needed"]:
        updates["nr_questions_asked"] = state["nr_questions_asked"] + 1
    else:
        updates["recommended_solutions"] = [
            {"title": t} for t in result["recommended_solution_titles"]
        ]

    return updates


def ask_question(state: AgentState) -> dict:
    """Generate one clarifying question, send it to the user via interrupt,
    and return both the question and the user's answer as new chat history."""
    prompt = ChatPromptTemplate.from_template(
        """You are an expert T-Systems solution advisor.
Based on the conversation so far, ask ONE concise, open-ended clarifying question
to better understand the customer's needs and suggest suitable solutions from the portfolio. 

Important: Output just the question, ask the question directly.

Available solutions in portfolio:
{solutions}

Conversation so far:
{chat_history}"""
    )

    chain = prompt | llm.with_structured_output(QuestionOutput)
    result = chain.invoke({
        "solutions": create_solutions_list(state["solutions"]),
        "chat_history": create_chat_history(state["chat_history"]),
    })
    question = result.question

    user_answer = interrupt(question)

    return {
        "chat_history": [AIMessage(content=question), HumanMessage(content=user_answer)],
    }


def generate_answer(state: AgentState) -> dict:
    """Filter the recommended solutions from the full portfolio, then call the LLM
    to produce a per-solution summary and personalised 'why' for the customer."""
    # Filter solutions inline — no separate node needed
    titles = {r["title"] for r in state["recommended_solutions"]}
    filtered = [s for s in ALL_SOLUTIONS if s["title"] in titles]
    solutions_text = "\n\n".join(f"### {s['title']}\n{s['content']}" for s in filtered)

    prompt = ChatPromptTemplate.from_template(
        """You are an expert T-Systems solution advisor.
Based on the conversation and the solution descriptions below, produce a structured answer that explains the solution briefly and why the solution is a fit for customer's needs.

Conversation:
{chat_history}

Solutions to recommend:
{solutions}

For each solution, output:
- summary: 1–3 sentences capturing the core value of the solution. Maximum 200 characters.
- why: 1–2 sentences explaining specifically why THIS customer needs this solution, referencing their stated needs."""
    )

    chain = prompt | llm.with_structured_output(FinalOutputModel)
    result = chain.invoke({
        "chat_history": create_chat_history(state["chat_history"]),
        "solutions": solutions_text,
    })

    final_answer = json.dumps({
        "solutions": [
            {"title": sol.title, "summary": sol.summary, "why": sol.why}
            for sol in result.solutions
        ]
    })

    return {"final_answer": final_answer}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_orchestrator(state: AgentState) -> str:
    if state["is_question_needed"]:
        return "ask_question"
    return "generate_answer"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    builder = StateGraph(AgentState)

    builder.add_node("reset_state", reset_state)
    builder.add_node("orchestrator", orchestrator)
    builder.add_node("ask_question", ask_question)
    builder.add_node("generate_answer", generate_answer)

    builder.add_edge(START, "reset_state")
    builder.add_edge("reset_state", "orchestrator")

    builder.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {"ask_question": "ask_question", "generate_answer": "generate_answer"},
    )
    builder.add_edge("ask_question", "orchestrator")   # back-edge after question answered
    builder.add_edge("generate_answer", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()

