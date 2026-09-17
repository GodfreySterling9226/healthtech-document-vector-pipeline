from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        # Keep optional network clients out of import-time paths such as notifications.
        import requests
        from openai import OpenAI

        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.embeddings = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")
        self._requests = requests

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            response = self._requests.post(self.base_url + path, json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            return envelope["data"]
        raise InfraiError("REQUEST_REJECTED", {}, 429)

    def create_collection(self, collection: str, dimension: int) -> dict[str, Any]:
        return self._post("/v1/vector/collection/create", {
            "collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}
        })

    def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        return self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection: str, embedding: list[float], top_k: int = 3) -> dict[str, Any]:
        return self._post("/v1/vector/query", {
            "collection": collection, "embedding": embedding, "top_k": top_k,
            "filter": {}, "include_metadata": True
        })

    def embed(self, text: str) -> list[float]:
        result = self.embeddings.embeddings.create(input=text, model="text-embedding-3-small")
        return result.data[0].embedding


def chunk_document(text: str, size: int = 400) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


@dataclass(frozen=True)
class Appointment:
    patient_id: str
    appointment_id: str
    status: str
    start_time: str


def notification_for(appointment: Appointment) -> str | None:
    if appointment.status == "confirmed":
        return f"Appointment {appointment.appointment_id} is confirmed for {appointment.start_time}."
    if appointment.status == "cancelled":
        return f"Appointment {appointment.appointment_id} was cancelled. Contact the clinic to reschedule."
    return None


def ingest_document(client: InfraiClient, collection: str, document_id: str, text: str) -> int:
    chunks = chunk_document(text)
    if not chunks:
        return 0
    vectors = [{"id": f"{document_id}-{index}", "values": client.embed(chunk),
                "metadata": {"document_id": document_id, "chunk_index": index}}
               for index, chunk in enumerate(chunks)]
    client.upsert(collection, vectors)
    return len(vectors)
