from pathlib import Path
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .providers import get_provider, ProviderError

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
ASSETS = ROOT / "ai" / "assets"
app = FastAPI(title="o1ai", version="1.0.0")

class ChatRequest(BaseModel):
    messages: list[dict[str, str]] = Field(min_length=1)

@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/health")
async def health():
    return {"ok": True, "name": "o1ai", "version": "1.0.0"}

@app.get("/api/models")
async def models():
    files = []
    for p in ASSETS.rglob("*"):
        if p.is_file():
            files.append({"name": p.name, "path": str(p.relative_to(ASSETS)), "bytes": p.stat().st_size})
    return {"chat_provider": "configured" if os.getenv('NADOS_PROVIDER') == 'openai_compatible' else "demo", "local_assets": files}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        text = await get_provider().chat(req.messages)
        return {"message": {"role": "assistant", "content": text}}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model provider error: {exc}")

@app.get("/assets/{path:path}")
async def asset(path: str):
    target = (ASSETS / path).resolve()
    if ASSETS.resolve() not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(target)

app.mount("/", StaticFiles(directory=FRONTEND), name="static")
