#!/usr/bin/env python3

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from src.decode import DEFAULT_CHUNK_SIZE, DEFAULT_MODEL_PATH, DecodeError, VoskDecoder


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc


class ServiceInfoResponse(BaseModel):
    service: str = Field(default="DockerWithVosk API")
    status: str = Field(default="ok")


class HealthResponse(BaseModel):
    status: str
    model_path: str
    recognizer_pool_size: int
    chunk_size: int


class DecodeResponse(BaseModel):
    filename: str | None
    content_type: str | None
    result: Any
    partials: list[Any] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    decoder = VoskDecoder(
        model_path=os.getenv("VOSK_MODEL_PATH", DEFAULT_MODEL_PATH),
        recognizer_pool_size=_get_int_env("VOSK_RECOGNIZER_POOL_SIZE", 4),
        words=_get_bool_env("VOSK_WORDS", True),
        chunk_size=_get_int_env("VOSK_CHUNK_SIZE", DEFAULT_CHUNK_SIZE),
    )
    app.state.decoder = decoder
    yield


app = FastAPI(
    title="DockerWithVosk API",
    version="0.1.0",
    description="REST API for Vosk-based WAV transcription.",
    lifespan=lifespan,
)


def get_decoder(request: Request) -> VoskDecoder:
    decoder = getattr(request.app.state, "decoder", None)
    if decoder is None:
        raise RuntimeError("Decoder is not initialized.")
    return decoder


@app.get("/", response_model=ServiceInfoResponse)
async def root() -> ServiceInfoResponse:
    return ServiceInfoResponse()


@app.get("/health", response_model=HealthResponse)
async def healthcheck(request: Request) -> HealthResponse:
    decoder = get_decoder(request)
    return HealthResponse(
        status="ok",
        model_path=decoder.model_path,
        recognizer_pool_size=decoder._pool_size,
        chunk_size=decoder.chunk_size,
    )


@app.post("/decode", response_model=DecodeResponse, status_code=status.HTTP_200_OK)
async def decode_audio(
    request: Request,
    file: UploadFile = File(...),
) -> DecodeResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")

    decoder = get_decoder(request)
    uploaded_audio = await file.read()
    if not uploaded_audio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        payload = await decoder.decode_upload(uploaded_audio)
    except DecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return DecodeResponse(
        filename=file.filename,
        content_type=file.content_type,
        result=payload["result"],
        partials=payload["partials"],
    )
