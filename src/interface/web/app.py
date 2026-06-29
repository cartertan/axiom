import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

import pdfplumber
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from axiom import get_agent, load_config
from src.agents.council_orchestrator import run_council
from src.benchmark.logger import BenchmarkLogger
from src.core.memory import AxiomMemory
from src.core.ollama_client import OllamaClient, OllamaConnectionError
from src.core.orchestrator import Orchestrator
from src.core.profile import ProfileLoader
from src.core.router import TaskRouter
from src.rag.retriever import PKIRetriever
from src.voice.stt import SpeechToText, SpeechToTextError
from src.voice.tts import TextToSpeech, TextToSpeechError

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
benchmark_logger = BenchmarkLogger()
pki_retriever = PKIRetriever()
orchestrator = Orchestrator(client, benchmark_logger)


class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = "single"


class CouncilRequest(BaseModel):
    question: str
    quick: bool = False
    save_vault: bool = False
    force_complex: bool = False


class SynthesizeRequest(BaseModel):
    text: str


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return JSONResponse(status_code=400, content={"error": "message cannot be empty"})

    orch_cfg = config.get("orchestration", {})
    task_type = router.classify(req.message)
    mode = req.mode or "single"

    # Auto-upgrade to ensemble for multi_model_tasks when mode is not set explicitly
    if mode == "single":
        multi_tasks = orch_cfg.get("multi_model_tasks", [])
        if task_type in multi_tasks:
            mode = "ensemble"

    try:
        if mode in ("ensemble", "pipeline", "debate"):
            start = time.time()
            if mode == "ensemble":
                models = orch_cfg.get("ensemble", {}).get("default_models", [])
                synth = orch_cfg.get("ensemble", {}).get("synthesiser", models[0])
                result = orchestrator.run_ensemble(task_type, req.message, models, synth)
                latency = round(time.time() - start, 2)
                return {
                    "response": result["final"],
                    "task_type": task_type,
                    "model": f"[ensemble: {', '.join(models)}]",
                    "latency": latency,
                    "individual_responses": result["individual_responses"],
                }
            elif mode == "pipeline":
                seq = orch_cfg.get("pipeline", {}).get("default_sequence", [])
                result = orchestrator.run_pipeline(task_type, req.message, seq)
                latency = round(time.time() - start, 2)
                return {
                    "response": result["final"],
                    "task_type": task_type,
                    "model": f"[pipeline: {' → '.join(seq)}]",
                    "latency": latency,
                    "stages": result["stages"],
                }
            else:  # debate
                models = orch_cfg.get("debate", {}).get("default_models", [])
                judge = orch_cfg.get("debate", {}).get("judge", models[0])
                result = orchestrator.run_debate(task_type, req.message, models, judge)
                latency = round(time.time() - start, 2)
                return {
                    "response": result["final"],
                    "task_type": task_type,
                    "model": f"[debate: {', '.join(models)}]",
                    "latency": latency,
                    "round1": result["round1"],
                }
        else:
            agent = get_agent(task_type, config, profile, memory, client, pki_retriever)
            model, _, _ = router.get_model_for_task(task_type)
            start = time.time()
            response = agent.run(req.message, task_type)
            latency = round(time.time() - start, 2)
            return {
                "response": response,
                "task_type": task_type,
                "model": model,
                "latency": latency,
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


@app.post("/council")
def council(req: CouncilRequest):
    if not req.question.strip():
        return JSONResponse(status_code=400, content={"error": "question cannot be empty"})
    start = time.time()
    try:
        result = run_council(
            question=req.question,
            quick=req.quick,
            save_vault=req.save_vault,
            force_complex=req.force_complex,
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    duration = round(time.time() - start, 2)
    roles = [
        {
            "role": r["role"],
            "model": r["model"],
            "content": r["content"],
            "where_run": r.get("where_run", "local"),
        }
        for r in result["responses"]
    ]
    reviewer = result["reviewer"]
    return {
        "question": result["question"],
        "roles": roles,
        "reviewer": reviewer["content"],
        "vault_path": result.get("saved_to"),
        "duration_seconds": duration,
    }


@app.post("/voice/transcribe")
def voice_transcribe(file: UploadFile = File(...)):
    try:
        stt = SpeechToText(config)
    except SpeechToTextError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})

    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    fd_in, tmp_in = tempfile.mkstemp(suffix=suffix)
    os.close(fd_in)
    try:
        with open(tmp_in, "wb") as f:
            f.write(file.file.read())

        # whisper-cli needs 16 kHz mono WAV; convert non-WAV uploads via ffmpeg
        if suffix.lower() != ".wav":
            fd_wav, tmp_wav = tempfile.mkstemp(suffix=".wav")
            os.close(fd_wav)
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_in, "-ar", "16000", "-ac", "1", tmp_wav],
                    check=True,
                    capture_output=True,
                )
                text = stt.transcribe_file(tmp_wav)
            except subprocess.CalledProcessError:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Audio conversion failed. Is ffmpeg installed? brew install ffmpeg"},
                )
            finally:
                if os.path.exists(tmp_wav):
                    os.unlink(tmp_wav)
        else:
            text = stt.transcribe_file(tmp_in)

        return {"text": text}
    except SpeechToTextError as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(tmp_in):
            os.unlink(tmp_in)


@app.post("/voice/synthesize")
def voice_synthesize(req: SynthesizeRequest):
    if not req.text.strip():
        return JSONResponse(status_code=400, content={"error": "text cannot be empty"})
    try:
        tts = TextToSpeech(config)
    except TextToSpeechError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})

    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        tts.save_audio(req.text, tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        return Response(content=audio_bytes, media_type="audio/wav")
    except TextToSpeechError as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
