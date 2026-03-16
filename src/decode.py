#!/usr/bin/env python3

import asyncio
import io
import json
import os
import queue
import sys
import threading
import wave
from pathlib import Path

from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(0)

class VoskDecoder:
    def __init__(
        self,
        model_path: str = "vosk-ru-model",
        recognizer_pool_size: int = 4,
        words: bool = True,
        chunk_size: int = 4000,
    ) -> None:
        if recognizer_pool_size <= 0:
            raise ValueError("recognizer_pool_size должен быть > 0")
        if chunk_size <= 0:
            raise ValueError("chunk_size должен быть > 0")

        self.model_path = model_path
        self.words = words
        self.chunk_size = chunk_size
        self._model = Model(self.model_path)
        self._pool_size = recognizer_pool_size
        self._recognizers: dict[int, queue.Queue[KaldiRecognizer]] = {}
        self._pool_init_lock = threading.Lock()

    async def decode_upload(self, uploaded_audio: bytes) -> dict[str, object]:
        return await asyncio.to_thread(self._decode_bytes_sync, uploaded_audio)

    def decode_file(self, wav_file_path: str) -> dict[str, object]:
        with wave.open(wav_file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            return self._decode_wave_reader(wf, sample_rate)

    def _decode_bytes_sync(self, uploaded_audio: bytes) -> dict[str, object]:
        wav_buffer = io.BytesIO(uploaded_audio)
        with wave.open(wav_buffer, "rb") as wf:
            sample_rate = wf.getframerate()
            return self._decode_wave_reader(wf, sample_rate)

    def _decode_wave_reader(self, wf: wave.Wave_read, sample_rate: int) -> dict[str, object]:
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
        wav_path = Path("src/decoder-test.wav")
    if not wav_path.exists():
        print(f"Файл не найден: {wav_path}")
        return 2

    decoder = VoskDecoder(model_path="vosk-ru-model", recognizer_pool_size=2)
    try:
        payload = decoder.decode_file(str(wav_path))
    except ValueError as exc:
        print(str(exc))
        return 1

    print(json.dumps(payload["result"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
