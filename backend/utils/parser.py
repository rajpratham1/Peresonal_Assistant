from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from difflib import get_close_matches

from backend.config import APP_ALIASES, FUZZY_TARGETS, WEBSITE_ALIASES


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def fuzzy_normalize_target(text: str) -> str:
    normalized = normalize_text(text)
    if normalized in FUZZY_TARGETS:
        return FUZZY_TARGETS[normalized]

    candidates = list(APP_ALIASES) + list(WEBSITE_ALIASES) + list(FUZZY_TARGETS)
    matches = get_close_matches(normalized, candidates, n=1, cutoff=0.72)
    if matches:
        best = matches[0]
        return FUZZY_TARGETS.get(best, best)
    return normalized


def extract_email_fields(text: str) -> tuple[str | None, str, str]:
    recipient_match = EMAIL_PATTERN.search(text)
    recipient = recipient_match.group(0) if recipient_match else None
    subject = "Assistant Message"
    body = text
    if "subject" in text and "body" in text:
        subject_part = text.split("subject", 1)[1].split("body", 1)[0]
        body_part = text.split("body", 1)[1]
        subject = subject_part.strip(" :,-") or subject
        body = body_part.strip(" :,-") or body
    return recipient, subject, body


def extract_open_target(text: str) -> str:
    prefixes = ("open ", "launch ", "start ")
    for prefix in prefixes:
        if text.startswith(prefix):
            return fuzzy_normalize_target(text[len(prefix) :].strip())
    return fuzzy_normalize_target(text.strip())


def extract_message_fields(text: str) -> tuple[str | None, str]:
    match = re.search(r"message\s+(.+?)\s+saying\s+(.+)", text)
    if match:
        return normalize_text(match.group(1).strip()), match.group(2).strip()
    return None, text


def extract_note_content(text: str) -> str:
    prefixes = ("create a note", "save this note", "note")
    for prefix in prefixes:
        if text.startswith(prefix):
            content = text[len(prefix) :].strip(" :,.-")
            if content:
                return content
    return text


def split_compound_commands(text: str) -> list[str]:
    separators = (" and then ", " then ", " and ")
    commands = [text.strip()]
    for separator in separators:
        next_commands: list[str] = []
        for command in commands:
            parts = [part.strip() for part in command.split(separator) if part.strip()]
            next_commands.extend(parts if parts else [command])
        commands = next_commands
    return commands


def extract_youtube_query(text: str) -> str | None:
    patterns = (
        r"open youtube and play (?P<query>.+)",
        r"play (?P<query>.+) on youtube",
        r"play (?P<query>.+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group("query").strip()
    return None


def extract_call_target(text: str) -> str | None:
    match = re.search(r"call\s+(.+)", text)
    if match:
        return normalize_text(match.group(1).strip())
    return None


def parse_time_expression(text: str) -> datetime | None:
    match = re.search(r"(?:at|on|for)\s+(\d{1,2}:\d{2})", text)
    if not match:
        return None

    time_text = match.group(1)
    now = datetime.now()
    candidate = datetime.strptime(time_text, "%H:%M").replace(
        year=now.year,
        month=now.month,
        day=now.day,
    )
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def extract_alarm_message(text: str) -> str:
    cleaned = re.sub(r"^(set\s+)?alarm\s+for\s+\d{1,2}:\d{2}", "", text).strip(" :,-")
    return cleaned or "Alarm reminder"


def extract_scheduled_message(text: str) -> tuple[datetime | None, str | None, str | None]:
    trigger_at = parse_time_expression(text)
    match = re.search(r"(?:at|on)\s+\d{1,2}:\d{2}\s+message\s+(.+?)\s+saying\s+(.+)", text)
    if not match:
        return trigger_at, None, None
    return trigger_at, normalize_text(match.group(1).strip()), match.group(2).strip()


def extract_contact_fields(text: str) -> tuple[str | None, str | None, str | None, str | None]:
    match = re.search(
        r"save contact\s+(?P<name>.+?)(?:\s+phone\s+(?P<phone>[\d+ -]+))?(?:\s+email\s+(?P<email>[\w.+-]+@[\w-]+\.[\w.-]+))?(?:\s+whatsapp\s+(?P<whatsapp>.+))?$",
        text,
    )
    if not match:
        return None, None, None, None
    return (
        normalize_text(match.group("name").strip()),
        match.group("phone").strip() if match.group("phone") else None,
        match.group("email").strip() if match.group("email") else None,
        match.group("whatsapp").strip() if match.group("whatsapp") else None,
    )


def find_file(root: Path, query: str) -> str | None:
    lowered = query.lower()
    for path in root.rglob("*"):
        if path.is_file() and lowered in path.name.lower():
            return str(path)
    return None
