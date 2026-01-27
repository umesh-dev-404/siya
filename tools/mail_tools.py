"""
Mail integration tools (initial, offline-first).

Design:
- Offline-first: reads mail data from a local JSON file.
- Network-based mail fetching (IMAP/Gmail API) will be added later with LAW 16 enforcement.

This provides an end-to-end example ("summarize mails") without requiring network setup.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from ai.ai_interface import AIInterface


def _load_mail_store(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    if not p.is_file():
        raise RuntimeError("MAIL_STORE_INVALID: mail store path is not a file")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"MAIL_STORE_INVALID_JSON: {e}") from e
    if not isinstance(data, list):
        raise RuntimeError("MAIL_STORE_INVALID: expected a JSON array")
    # each element is a mail object (best-effort)
    return [x for x in data if isinstance(x, dict)]


def make_fetch_mails_tool(default_store_path: str):
    def fetch_mails(args: Dict[str, Any]) -> Dict[str, Any]:
        store_path = args.get("store_path", default_store_path)
        if not isinstance(store_path, str) or not store_path.strip():
            store_path = default_store_path
        limit = args.get("limit", 10)
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            limit = 10

        mails = _load_mail_store(store_path)
        mails = mails[:limit]
        return {"status": "ok", "count": len(mails), "mails": mails}

    return fetch_mails


def make_summarize_mails_tool(ai: AIInterface, default_store_path: str):
    fetch = make_fetch_mails_tool(default_store_path)

    def summarize_mails(args: Dict[str, Any]) -> Dict[str, Any]:
        fetched = fetch(args)
        mails = fetched.get("mails", [])
        if not mails:
            return {"status": "ok", "summary": "No mails found in local store.", "count": 0}

        # Selective output controls
        max_items = args.get("max_items", 5)
        if not isinstance(max_items, int) or max_items < 1 or max_items > 20:
            max_items = 5
        fields = args.get("fields", ["from", "subject", "date", "snippet"])
        if not isinstance(fields, list) or not all(isinstance(x, str) for x in fields):
            fields = ["from", "subject", "date", "snippet"]

        selected = []
        for m in mails[:max_items]:
            selected.append({k: m.get(k) for k in fields})

        prompt = (
            "You are Siya's local content processor. Summarize the following emails for the user.\n"
            "Return a concise summary and highlight any urgent items.\n\n"
            f"EMAILS(JSON):\n{json.dumps(selected, ensure_ascii=False)}\n"
        )
        summary = ai.generate_text(prompt=prompt, max_tokens=256, temperature=0.2).strip()
        return {"status": "ok", "count": len(selected), "summary": summary, "items": selected}

    return summarize_mails

