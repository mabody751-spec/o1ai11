from pathlib import Path
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .providers import get_provider, ProviderError, SmartDemoProvider

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
ASSETS = ROOT / "ai" / "assets"
app = FastAPI(title="o1ai", version="2.0.0")

class ChatRequest(BaseModel):
    messages: list[dict[str, str]] = Field(min_length=1)

class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = ""

class DescriptionRequest(BaseModel):
    description: str = Field(..., min_length=3)
    language: str = ""

class AlgorithmRequest(BaseModel):
    algorithm: str = Field(..., min_length=2)

class ContextRequest(BaseModel):
    messages: list[dict[str, str]] = Field(default_factory=list)

@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/health")
async def health():
    return {"ok": True, "name": "o1ai", "version": "2.0.0", "mode": "programming+conversation", "capabilities": ["chat", "explain", "format", "debug", "generate", "test", "patterns", "algorithm"]}

@app.get("/api/models")
async def models():
    files = []
    for p in ASSETS.rglob("*"):
        if p.is_file():
            files.append({"name": p.name, "path": str(p.relative_to(ASSETS)), "bytes": p.stat().st_size})
    return {"chat_provider": "configured" if os.getenv('NADOS_PROVIDER') == 'openai_compatible' else "demo", "local_assets": files, "capabilities": ["chat", "code_explain", "code_format", "detect_bugs", "code_generate", "code_test", "code_patterns", "explain_algorithm", "context_analyze"]}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        text = await get_provider().chat(req.messages)
        return {"message": {"role": "assistant", "content": text}}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model provider error: {exc}")

@app.post("/api/code/explain")
async def code_explain(req: CodeRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.code_explain(req.code, req.language)
        else:
            result = await provider.chat([{"role": "user", "content": f"شرح الكود التالي: {req.code}"}])
        return {"explanation": result, "language": req.language or "auto-detected"}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/code/format")
async def code_format(req: CodeRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.code_format(req.code, req.language)
        else:
            result = await provider.chat([{"role": "user", "content": f"Format this {req.language} code: {req.code}"}])
        return {"formatted_code": result, "language": req.language or "auto-detected"}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/code/detect-bugs")
async def detect_bugs(req: CodeRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.detect_bugs(req.code, req.language)
        else:
            result = await provider.chat([{"role": "user", "content": f"Detect bugs in this {req.language} code: {req.code}"}])
        return {"analysis": result, "language": req.language or "auto-detected"}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/code/generate")
async def code_generate(req: DescriptionRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.code_generate(req.description, req.language)
        else:
            result = await provider.chat([{"role": "user", "content": f"Generate code in {req.language}: {req.description}"}])
        return {"code": result, "language": req.language or "auto-detected"}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/code/test")
async def code_test(req: CodeRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.code_test(req.code, req.language)
        else:
            result = await provider.chat([{"role": "user", "content": f"Generate unit tests for this {req.language} code: {req.code}"}])
        return {"tests": result, "language": req.language or "auto-detected"}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/code/patterns")
async def code_patterns(req: DescriptionRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.code_patterns(req.description)
        else:
            result = await provider.chat([{"role": "user", "content": f"Design patterns for {req.description}"}])
        return {"patterns": result}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/algorithm/explain")
async def explain_algorithm(req: AlgorithmRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            result = await provider.explain_algorithm(req.algorithm)
        else:
            result = await provider.chat([{"role": "user", "content": f"Explain the {req.algorithm} algorithm"}])
        return {"explanation": result}
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.post("/api/context/analyze")
async def analyze_context(req: ContextRequest):
    try:
        provider = get_provider()
        if isinstance(provider, SmartDemoProvider):
            context = provider._build_context(req.messages)
            lang = ""
            for m in reversed(req.messages):
                if m.get("role") == "user":
                    lang = provider._detect_language(m["content"])
                    if lang:
                        break
            return {"context": context, "detected_language": lang, "message_count": len(req.messages)}
        return {"context": "Context analysis requires SmartDemoProvider", "message_count": len(req.messages)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")

@app.get("/assets/{path:path}")
async def asset(path: str):
    target = (ASSETS / path).resolve()
    if ASSETS.resolve() not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(target)

app.mount("/", StaticFiles(directory=FRONTEND), name="static")
