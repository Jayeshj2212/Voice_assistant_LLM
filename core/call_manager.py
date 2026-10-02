from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class CallSession:
    lead_name: str
    phone: str
    language: str
    campaign: str
    status: str = "initiated"
    transcript: List[str] = field(default_factory=list)
    summary: str = ""
    recording_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_transcript_line(self, text: str):
        self.transcript.append(text)

    def save_summary(self, text: str):
        self.summary = text
        self.status = "completed"


class CallManager:
    def __init__(self, base_dir: str = "./recordings"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: List[CallSession] = []
        self.sessions_by_lead: dict[str, list[str]] = {}

    def new_session(self, lead_name: str, phone: str, language: str, campaign: str) -> CallSession:
        session = CallSession(lead_name=lead_name, phone=phone, language=language, campaign=campaign)
        self.sessions.append(session)
        return session

    def persist_recording(self, session: CallSession, audio_path: str) -> str:
        target_dir = self.base_dir / session.lead_name.replace(" ", "_") / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "call.wav"
        os.replace(audio_path, target_file)
        session.recording_path = str(target_file)
        return str(target_file)

    def export_summary(self, session: CallSession, summary_text: str) -> str:
        summary_path = self.base_dir / session.lead_name.replace(" ", "_") / "summary.txt"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary_text, encoding="utf-8")
        session.save_summary(summary_text)
        return str(summary_path)
