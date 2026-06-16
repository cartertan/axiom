import time
from pathlib import Path

import pdfplumber
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from axiom import get_agent, load_config
from src.core.memory import AxiomMemory
from src.core.ollama_client import OllamaClient, OllamaConnectionError
from src.core.profile import ProfileLoader
from src.core.router import TaskRouter
from src.rag.retriever import PKIRetriever

_WEB_DIR = Path(__file__).parent

app = FastAPI(title="AXIOM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=_WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=_WEB_DIR / "templates")

config = load_config()
client = OllamaClient(base_url=config.get("ollama_base_url", "http://localhost:11434"))
profile = ProfileLoader()
memory = AxiomMemory()
router = TaskRouter(config)
pki_retriever = PKIRetriever()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return JSONResponse(status_code=400, content={"error": "message cannot be empty"})

    try:
        task_type = router.classify(req.message)
        agent = get_agent(task_type, config, profile, memory, client, pki_retriever)
        model, _, _ = router.get_model_for_task(task_type)

        start = time.time()
        response = agent.run(req.message, task_type)
        latency = time.time() - start

        return {
            "response": response,
            "task_type": task_type,
            "model": model,
            "latency": round(latency, 2),
        }
    except OllamaConnectionError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        with pdfplumber.open(file.file) as pdf:
            text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
        return {"text": text.strip()}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Could not extract PDF text: {e}"})


@app.get("/history")
def history(n: int = 20):
    try:
        return {"interactions": memory.get_recent_interactions(n)}
    except OllamaConnectionError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})
