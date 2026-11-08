"""Conversation memory with per-conversation locking and optional JSON persistence."""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .settings import DATA_DIR

MAX_CONVERSATIONS = 50
STORE_FILE = DATA_DIR / "genesis_conversations.json"


@dataclass
class Conversation:
    id: str
    messages: List[Dict[str, str]] = field(default_factory=list)  # user/assistant only
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def public(self) -> dict:
        return {"id": self.id, "created": self.created, "updated": self.updated,
                "messages": list(self.messages)}


class ConversationStore:
    def __init__(self, persist: bool = True) -> None:
        self._convs: Dict[str, Conversation] = {}
        self._persist = persist
        self._io_lock = threading.Lock()
        if persist:
            self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(STORE_FILE.read_text(encoding="utf-8"))
            for c in raw.get("conversations", []):
                self._convs[c["id"]] = Conversation(c["id"], c.get("messages", []),
                                                    c.get("created", time.time()),
                                                    c.get("updated", time.time()))
        except (FileNotFoundError, ValueError, KeyError):
            pass

    def _save(self) -> None:
        if not self._persist:
            return
        with self._io_lock:
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                payload = {"conversations": [c.public() for c in self._convs.values()]}
                fd, tmp = tempfile.mkstemp(dir=str(DATA_DIR), suffix=".tmp")
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f)
                os.replace(tmp, STORE_FILE)  # atomic
            except OSError:
                pass  # persistence is best-effort; never break chat

    def create(self) -> Conversation:
        conv = Conversation(uuid.uuid4().hex[:12])
        self._convs[conv.id] = conv
        if len(self._convs) > MAX_CONVERSATIONS:
            oldest = sorted(self._convs.values(), key=lambda c: c.updated)[0]
            self._convs.pop(oldest.id, None)
        self._save()
        return conv

    def get(self, cid: Optional[str]) -> Optional[Conversation]:
        return self._convs.get(cid) if cid else None

    def get_or_create(self, cid: Optional[str]) -> Conversation:
        return self.get(cid) or self.create()

    def append_turn(self, conv: Conversation, user: str, assistant: str, keep: int) -> None:
        conv.messages.append({"role": "user", "content": user})
        conv.messages.append({"role": "assistant", "content": assistant})
        limit = max(2, keep * 2)
        if len(conv.messages) > limit:
            conv.messages = conv.messages[-limit:]
        conv.updated = time.time()
        self._save()

    def clear(self, cid: str) -> bool:
        conv = self._convs.get(cid)
        if not conv:
            return False
        conv.messages = []
        conv.updated = time.time()
        self._save()
        return True

    def delete(self, cid: str) -> bool:
        existed = self._convs.pop(cid, None) is not None
        if existed:
            self._save()
        return existed

    def list(self) -> List[dict]:
        return [{"id": c.id, "updated": c.updated, "turns": len(c.messages) // 2}
                for c in sorted(self._convs.values(), key=lambda c: -c.updated)]
