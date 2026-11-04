"""Incident explainer: a small, tool-less model explains a tripwire from the audit record ONLY,
never from the misbehaving model's own words. Its text is labelled as possibly wrong."""
import json

EXPLAINER_MODEL = "qwen3:4b-instruct-2507-q4_K_M"   # already installed for JARVIS
FIELDS = ("event", "t", "data")


def prompt(record):
    facts = {k: record.get(k) for k in FIELDS}
    return [
        {"role": "system", "content": "You explain safety stops to a non-expert in 3-5 short sentences. Use only the "
                                      "facts given. Do not guess intent. Do not suggest how to get around the stop."},
        {"role": "user", "content": "GOD mode stopped itself. Audit record (facts):\n" +
                                    json.dumps(facts, indent=1, ensure_ascii=False)[:4000]},
    ]


def explain(record, client):
    """client: OllamaClient for the explainer model. Returns labelled text; never raises."""
    try:
        r = client.chat(prompt(record), tools=None)
        text = (r.get("content") or "").strip() or "(no explanation)"
    except Exception as e:   # the raw record is always shown anyway
        text = f"(explainer unavailable: {type(e).__name__})"
    return "AI explanation, may be wrong:\n" + text
