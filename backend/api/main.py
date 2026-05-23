import logging
import logging.config

# ─── Logging setup ───────────────────────────────────────────────────────────
# dictConfig is the reliable way to configure logging in a uvicorn app.
# We use stderr (always unbuffered) so output appears immediately in the terminal
# regardless of uvicorn's stdout buffering or --reload subprocess behaviour.
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "pipeline": {
            "format": "%(asctime)s  %(levelname)-8s  %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "pipeline",
        }
    },
    "loggers": {
        "api": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
})

_log = logging.getLogger("api")
_log.info("=== Pipeline logging active ===")

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from api.middleware.logging import LoggingMiddleware
from api.routes import chat, research, plan

# ─── Create the FastAPI app ───────────────────────────────────────────────────

app = FastAPI(
    title="Agentic AI Platform",
    description=(
        "An AI-powered agentic platform with modular skills. "
        "The agent automatically decides whether to invoke the Research Skill, "
        "the Task Planning Skill, or both — based on the user's message."
    ),
    version="1.0.0"
)

# ─── Register Middleware ──────────────────────────────────────────────────────

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─── Root redirect ────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# ─── Register Routes ──────────────────────────────────────────────────────────

app.include_router(chat.router, tags=["Chat"])
app.include_router(research.router, tags=["Skills"])
app.include_router(plan.router, tags=["Skills"])
