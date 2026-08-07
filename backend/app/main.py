from fastapi import FastAPI

app = FastAPI(
    title="Enterprise AI Integration Agent Platform",
    version="0.1.0",
)


@app.get("/api/v1/live")
async def live():
    return {
        "status": "ok",
        "service": "enterprise-ai-agent"
    }