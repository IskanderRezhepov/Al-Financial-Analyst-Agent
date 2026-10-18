"""FastAPI backend: tutorial C1 streaming route and local report endpoint."""
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage
from pydantic import BaseModel, Field
import uvicorn

from .agent import build_agent, public_model_error, run_analysis
from .config import model_settings, provider
from .tools import DataUnavailable, resolve_company

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
# SDK network logging is unnecessary and may include sensitive URL details.
logging.getLogger("httpx").setLevel(logging.WARNING)
app = FastAPI(title="AI Financial Analyst Agent", version="1.0.0")


class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=15)
    request: str = Field(default="", max_length=1000)
    include_underwriting: bool = True


class PromptObject(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    id: str
    role: str


class RequestObject(BaseModel):
    prompt: PromptObject
    threadId: str = Field(min_length=1, max_length=100)
    responseId: str


@app.get("/api/health")
def health():
    settings = model_settings() if provider() == "ollama" else None
    return {"status": "ok", "provider": provider(),
            "model": settings["model"] if settings else "Thesys C1",
            "note": "API ready; model and Yahoo availability are verified when analysis runs."}


@app.get("/api/companies")
def companies(q: str = ""):
    try:
        return resolve_company.invoke({"query": q})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    except Exception:
        raise HTTPException(502, "Yahoo company search is unavailable. Enter a ticker directly.") from None


@app.post("/api/analyze")
def analyze(request: AnalysisRequest):
    try:
        return run_analysis(request.ticker, request.request, request.include_underwriting)
    except DataUnavailable as exc:
        raise HTTPException(502, str(exc)) from None
    except ValueError:
        raise HTTPException(422, "Invalid ticker or configuration. Check the ticker and .env provider settings.") from None
    except Exception:
        raise HTTPException(503, "Analysis is temporarily unavailable. Check configuration and retry.") from None


@app.post("/api/chat")
def chat(request: RequestObject):
    # Preserve the tutorial's raw streamed content contract expected by C1Chat.
    if provider() != "thesys":
        raise HTTPException(409, "C1 dynamic chat requires Thesys. Use the local analysis screen with Ollama.")
    try:
        agent = build_agent()
    except Exception:
        raise HTTPException(503, "Set your Thesys API key in OPENAI_API_KEY in .env, then restart.") from None

    def generate():
        try:
            for token, _ in agent.stream(
                {"messages": [HumanMessage(request.prompt.content)]}, stream_mode="messages",
                config={"configurable": {"thread_id": request.threadId or str(uuid4())}, "recursion_limit": 16},
            ):
                if isinstance(token.content, str) and token.type == "AIMessageChunk":
                    yield token.content
        except Exception:
            # A streaming HTTP status cannot be changed after headers have been sent.
            yield "\n" + public_model_error()

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "Connection": "keep-alive"})


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8888)

