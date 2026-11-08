"""Device feed: the single 'what should the TFT show right now' view, polled by the ESP32.

The ESP32 only makes OUTBOUND requests to the backend, so it works even when the phone's hotspot
blocks client-to-client traffic. Both the phone web UI and the device itself update this view."""
from __future__ import annotations

import time
from typing import Optional

from .formatting import device_text, paginate

# States shown on the TFT. READY = idle and able to take a question.
READY, THINKING, SEARCHING, TOOL, ANSWERED, ERROR = (
    "READY", "THINKING", "SEARCHING", "EXECUTING TOOL", "ANSWERED", "ERROR")


class DeviceFeed:
    def __init__(self) -> None:
        self.seq = 1
        self.state = READY
        self.question = ""
        self.answer_ascii = ""
        self.error = ""
        self.conversation_id = ""
        self.request_id = ""
        self.provider = ""
        self.model = ""
        self.brain = "CLOUD"      # "CLOUD" or "LOCAL"
        self.mode = "ONLINE"      # "ONLINE" or "OFFLINE"
        self.source = ""          # "phone" or "device"
        self.updated = time.time()

    def _bump(self) -> None:
        self.seq += 1
        self.updated = time.time()

    def begin(self, question: str, conversation_id: Optional[str], source: str,
              brain: str = "CLOUD", mode: str = "ONLINE") -> None:
        self.state, self.question, self.answer_ascii, self.error = THINKING, device_text(question), "", ""
        self.conversation_id = conversation_id or ""
        self.request_id, self.provider, self.model, self.source = "", "", "", source
        self.brain = brain
        self.mode = mode
        self._bump()

    def set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            self._bump()

    def finish(self, result: dict) -> None:
        self.state = ANSWERED
        self.answer_ascii = device_text(result.get("text", ""))
        self.conversation_id = result.get("conversation_id", self.conversation_id)
        self.request_id = result.get("request_id", "")
        self.provider, self.model = result.get("provider", ""), result.get("model", "")
        self.brain = result.get("brain", "LOCAL" if self.provider == "ollama" else "CLOUD")
        self.mode = result.get("mode", "OFFLINE" if self.brain == "LOCAL" else "ONLINE")
        self._bump()

    def fail(self, message: str, request_id: str = "") -> None:
        self.state, self.error, self.request_id = ERROR, device_text(message), request_id
        self.answer_ascii = ""
        self._bump()

    def reset(self) -> None:
        self.state, self.question, self.answer_ascii, self.error = READY, "", "", ""
        self.conversation_id = self.request_id = self.provider = self.model = ""
        self._bump()

    def view(self, client_seq: int, cols: int, rows: int, page: int = 0) -> dict:
        out = {"seq": self.seq, "state": self.state, "changed": client_seq != self.seq,
               "age_s": int(time.time() - self.updated), "brain": self.brain, "mode": self.mode}
        if client_seq == self.seq:
            return out
        body = self.answer_ascii if self.state == ANSWERED else self.error
        pages = paginate(body, cols, rows) if body else [""]
        page = max(0, min(page, len(pages) - 1))
        out.update({"question": self.question, "conversation_id": self.conversation_id,
                    "request_id": self.request_id, "provider": self.provider, "model": self.model,
                    "brain": self.brain, "mode": self.mode,
                    "source": self.source, "page": page, "total_pages": len(pages),
                    "text": pages[page]})
        return out

    def page(self, cols: int, rows: int, page: int) -> dict:
        body = self.answer_ascii if self.state == ANSWERED else self.error
        pages = paginate(body, cols, rows) if body else [""]
        page = max(0, min(page, len(pages) - 1))
        return {"seq": self.seq, "page": page, "total_pages": len(pages), "text": pages[page]}


feed = DeviceFeed()
