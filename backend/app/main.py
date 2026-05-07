"""FastAPI entrypoint for MatchOdds AI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analysis, backtest, games, meta, pipelines


def create_app() -> FastAPI:
    app = FastAPI(
        title="MatchOdds AI API",
        description="REST + SSE backend for the React frontend.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta.router)
    app.include_router(games.router)
    app.include_router(analysis.router)
    app.include_router(backtest.router)
    app.include_router(pipelines.router)

    @app.get("/")
    def root() -> dict:
        return {"name": "MatchOdds AI API", "ok": True}

    return app


app = create_app()
