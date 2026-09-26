"""Authenticated loopback API and bundled browser application."""

from __future__ import annotations

import asyncio
import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from starlette.middleware.trustedhost import TrustedHostMiddleware

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.service import Service
from dockyard.store import BusyError


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SignIn(Body):
    token: str


class Action(Body):
    action: str
    confirmed: bool = False


class LearningEvent(Body):
    event: str


class Note(Body):
    body: str


def create_app(service: Service, origin: str) -> tuple[FastAPI, str]:
    app = FastAPI(title="Dockyard", docs_url=None, redoc_url=None, openapi_url=None)
    nonce = secrets.token_urlsafe(32)
    cookie = secrets.token_urlsafe(32)
    cookie_name = "dockyard_" + secrets.token_hex(5)
    expires = time.monotonic() + 300
    consumed = False
    sign_in_lock = threading.Lock()
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @app.middleware("http")
    async def boundary(request: Request, call_next: Any) -> Response:
        if request.url.path.startswith("/api/"):
            supplied_origin = request.headers.get("origin")
            if supplied_origin is not None and supplied_origin != origin:
                return JSONResponse(
                    {"detail": "This request did not come from the workbench."}, status_code=403
                )
            if request.method not in {"GET", "HEAD"} and (
                supplied_origin != origin or request.headers.get("x-dockyard") != "1"
            ):
                return JSONResponse(
                    {"detail": "A same-origin workbench request is required."}, status_code=403
                )
            if request.url.path != "/api/session":
                received = request.cookies.get(cookie_name, "")
                if not secrets.compare_digest(received, cookie):
                    return JSONResponse(
                        {"detail": "Open Dockyard from its launcher to connect this browser."},
                        status_code=401,
                    )
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RuntimeErrorBase)
    @app.exception_handler(ValueError)
    async def lab_error(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(BusyError)
    async def busy_error(request: Request, error: BusyError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.post("/api/session")
    def sign_in(body: SignIn, response: Response) -> dict[str, bool]:
        nonlocal consumed
        with sign_in_lock:
            if (
                consumed
                or time.monotonic() > expires
                or not secrets.compare_digest(body.token, nonce)
            ):
                raise HTTPException(
                    401, "This one-time sign-in expired or was already used. Relaunch Dockyard."
                )
            consumed = True
        response.set_cookie(cookie_name, cookie, httponly=True, samesite="strict", path="/")
        return {"connected": True}

    @app.get("/api/catalog")
    def catalog() -> dict[str, Any]:
        return service.catalog.index()

    @app.get("/api/state")
    def state() -> dict[str, Any]:
        return {
            "progress": service.store.progress(),
            "labs": [service.public_lab(lab) for lab in service.store.labs()],
            "operations": service.store.operations(),
            "theme": service.store.setting("theme", "dark"),
            "last_unit": service.store.setting("last_unit"),
            "checkpoints": service.store.checkpoints(),
        }

    @app.get("/api/checkpoints/{checkpoint_id}/download")
    def download_checkpoint(checkpoint_id: str) -> FileResponse:
        item = next(
            (entry for entry in service.store.checkpoints() if entry["id"] == checkpoint_id), None
        )
        if not item:
            raise HTTPException(404, "That checkpoint does not exist.")
        directory = service.directory / "checkpoints"
        target = directory / str(item["archive"])
        if (
            target.is_symlink()
            or not target.resolve().is_relative_to(directory.resolve())
            or not target.is_file()
        ):
            raise HTTPException(404, "The checkpoint archive is unavailable.")
        return FileResponse(
            target,
            filename=f"dockyard-{item['unit_id']}-{checkpoint_id[:8]}.zip",
            media_type="application/zip",
        )

    @app.get("/api/doctor")
    def doctor() -> dict[str, Any]:
        return service.doctor()

    @app.get("/api/units/{unit_id}")
    def unit(unit_id: str) -> dict[str, Any]:
        item = service.catalog.get(unit_id)
        return {
            **item.model_dump(mode="json", exclude={"reference", "checks", "prepare", "hints"}),
            "hint_count": len(item.hints),
            "attempts": [
                attempt.model_dump(mode="json") for attempt in service.store.attempts(unit_id)
            ],
            "note": service.store.note(unit_id),
        }

    @app.post("/api/units/{unit_id}/events")
    def learning_event(unit_id: str, body: LearningEvent) -> dict[str, bool]:
        item = service.catalog.get(unit_id)
        if body.event != "viewed":
            raise HTTPException(400, "Use the explicit hint or reference action.")
        service.store.mark(unit_id, "viewed", item.revision)
        service.store.set_setting("last_unit", unit_id)
        return {"saved": True}

    @app.post("/api/units/{unit_id}/hints/{index}")
    def hint(unit_id: str, index: int) -> dict[str, str]:
        item = service.catalog.get(unit_id)
        if not 0 <= index < len(item.hints):
            raise HTTPException(404, "That hint does not exist.")
        service.store.mark(unit_id, "hints", item.revision)
        return {"hint": item.hints[index]}

    @app.post("/api/units/{unit_id}/reference")
    def reference(unit_id: str, body: Action) -> dict[str, str]:
        item = service.catalog.get(unit_id)
        if not body.confirmed:
            raise HTTPException(400, "Confirm that you want to reveal the reference.")
        service.store.mark(unit_id, "reference", item.revision)
        return item.reference

    @app.post("/api/units/{unit_id}/note")
    def note(unit_id: str, body: Note) -> dict[str, bool]:
        service.catalog.get(unit_id)
        service.store.save_note(unit_id, body.body)
        return {"saved": True}

    @app.post("/api/units/{unit_id}/lab")
    def lab_action(unit_id: str, body: Action) -> dict[str, Any]:
        if body.action in {"reset", "clean"} and not body.confirmed:
            raise HTTPException(400, "Confirm this change to the current lab first.")
        if body.action == "terminal":
            return service.open_terminal(unit_id)
        return service.perform(unit_id, body.action)

    @app.post("/api/operations/{operation_id}/cancel")
    def cancel(operation_id: str) -> dict[str, bool]:
        service.cancel(operation_id)
        return {"requested": True}

    @app.get("/api/events")
    async def events(request: Request) -> StreamingResponse:
        async def stream() -> Any:
            last = ""
            while not await request.is_disconnected():
                current = json.dumps(state(), sort_keys=True)
                if current != last:
                    yield f"event: state\ndata: {current}\n\n"
                    last = current
                else:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(stream(), media_type="text/event-stream")

    assets = Path(__file__).parent / "static"

    @app.get("/{path:path}")
    def frontend(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(404, "Unknown API endpoint.")
        target = (assets / path).resolve()
        if not target.is_relative_to(assets.resolve()):
            raise HTTPException(404)
        if target.is_file():
            return FileResponse(target)
        index = assets / "index.html"
        if not index.exists():
            raise HTTPException(
                503, "Build the browser assets before launching this development checkout."
            )
        return FileResponse(index)

    return app, nonce
