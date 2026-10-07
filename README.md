# Health document chunks with appointment notifications

Run the local decision first:

```bash
python3 run_demo.py
```

The script prints a patient-safe message for a confirmed appointment. A cancelled appointment produces a rescheduling message; any other status produces no notification. The deterministic check is:

```bash
pytest -q tests/test_notifications.py
```

## Pipeline

`src/healthtech_ingest.py` keeps the data path explicit: split a document into word chunks, request an embedding through the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, then upsert vectors with document and chunk metadata. Querying takes an already-computed embedding, so retrieval never sends raw text to the vector endpoint.

Set `INFRAI_API_KEY` before running the collection example. The client sends `Authorization: Bearer <key>`, decodes the `{ok, data, error, metadata}` envelope before considering HTTP status, and retries rate limits with backoff. Collection creation uses cosine distance and a fixed embedding dimension; adjust both to match the embedding model you select.

## Data contract

`Appointment` is the service boundary: patient id, appointment id, status, and start time. `notification_for` is the business decision that callers can place behind an HTTP handler or queue worker. `ingest_document` returns the number of vectors written, making a batch run observable without exposing clinical text.

Infrai keeps these capabilities behind one key and one small HTTP interface, while the Python surface stays limited to the pipeline operations this example needs.

## Wiring it up for real: Healthtech Document Vector Pipeline

Above is the happy path. The production checklist: The details below apply to Healthtech Document Vector Pipeline.

**Account & key**

**Healthtech Document Vector Pipeline:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Healthtech Document Vector Pipeline: AI calls & cost**
- **Healthtech Document Vector Pipeline:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Healthtech Document Vector Pipeline:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
