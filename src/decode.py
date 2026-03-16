#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import io
import json
import os
import queue
import sys
import threading
import wave
from pathlib import Path
from typing import Any

from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(0)

DEFAULT_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "vosk-ru-model")
DEFAULT_CHUNK_SIZE = 4000


class DecodeError(ValueError):
    pass

class VoskDecoder:
    def __init__(
        self,
        model_path: str | os.PathLike[str] = DEFAULT_MODEL_PATH,
        *,
        recognizer_pool_size: int = 4,
        words: bool = True,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        if recognizer_pool_size <= 0:
            raise ValueError("recognizer_pool_size должен быть > 0")
        if chunk_size <= 0:
            raise ValueError("chunk_size должен быть > 0")

        self.model_path = str(model_path)
        self.words = words
        self.chunk_size = chunk_size
        self._model = Model(self.model_path)
        self._pool_size = recognizer_pool_size
        self._recognizers: dict[int, queue.Queue[KaldiRecognizer]] = {}
        self._pool_init_lock = threading.Lock()

    async def decode_upload(self, uploaded_audio: bytes) -> dict[str, Any]:
        return await asyncio.to_thread(self._decode_bytes_sync, uploaded_audio)

    def decode_file(self, wav_file_path: str | os.PathLike[str]) -> dict[str, Any]:
        with wave.open(str(wav_file_path), "rb") as wf:
            self._validate_wav(wf)
            sample_rate = wf.getframerate()
            return self._decode_wave_reader(wf, sample_rate)

    def _decode_bytes_sync(self, uploaded_audio: bytes) -> dict[str, Any]:
        wav_buffer = io.BytesIO(uploaded_audio)
        try:
            with wave.open(wav_buffer, "rb") as wf:
                self._validate_wav(wf)
                sample_rate = wf.getframerate()
                return self._decode_wave_reader(wf, sample_rate)
        except wave.Error as exc:
            raise DecodeError("Invalid WAV payload.") from exc

    @staticmethod
    def _validate_wav(wf: wave.Wave_read) -> None:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise DecodeError("Аудиофайл должен быть в формате WAV, моно PCM (16 бит).")

    def _decode_wave_reader(self, wf: wave.Wave_read, sample_rate: int) -> dict[str, Any]:
        recognizer = self._acquire_recognizer_sync(sample_rate)
        partials: list[str] = []
        try:
            while True:
                data = wf.readframes(self.chunk_size)
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    partials.append(recognizer.Result())
                else:
                    partials.append(recognizer.PartialResult())

            final_result_raw = recognizer.FinalResult()
            final_payload = json.loads(final_result_raw)
            return {
                "result": final_payload,
                "partials": partials,
            }
        finally:
            self._release_recognizer_sync(sample_rate, recognizer)

    def _ensure_rate_bucket_sync(self, sample_rate: int) -> None:
        if sample_rate in self._recognizers:
            return
        with self._pool_init_lock:
            if sample_rate in self._recognizers:
                return
            recognizer_queue: queue.Queue[KaldiRecognizer] = queue.Queue(maxsize=self._pool_size)
            for _ in range(self._pool_size):
                rec = KaldiRecognizer(self._model, sample_rate)
                rec.SetWords(self.words)
                recognizer_queue.put_nowait(rec)
            self._recognizers[sample_rate] = recognizer_queue

    def _acquire_recognizer_sync(self, sample_rate: int) -> KaldiRecognizer:
        self._ensure_rate_bucket_sync(sample_rate)
        recognizer_queue = self._recognizers[sample_rate]
        return recognizer_queue.get(block=True)

    def _release_recognizer_sync(self, sample_rate: int, recognizer: KaldiRecognizer) -> None:
        if hasattr(recognizer, "Reset"):
            recognizer.Reset()
        recognizer_queue = self._recognizers[sample_rate]
        recognizer_queue.put_nowait(recognizer)


def _main() -> int:
    if len(sys.argv) == 2:
        wav_path = Path(sys.argv[1])
    else:
        wav_path = Path(__file__).resolve().parent / "decoder-test.wav"
    if not wav_path.exists():
        print(f"Файл не найден: {wav_path}")
        return 2

    decoder = VoskDecoder(model_path=DEFAULT_MODEL_PATH, recognizer_pool_size=2)
    try:
        payload = decoder.decode_file(wav_path)
    except DecodeError as exc:
        print(str(exc))
        return 1

    print(json.dumps(payload["result"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
