"""대본(script.json) 읽기와 검증.

카드 하나 = 화면 한 장 = 음성 한 조각.
카드는 문자열이거나 {"show": 화면 글자, "say": 읽을 글자} 입니다.
화면 글자에서 [대괄호]로 감싼 부분은 강조색으로 칠해집니다.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

MAX_CARD_CHARS = 40
MAX_TOTAL_SECONDS_HINT = 58


@dataclass
class Card:
    label: str
    show: str
    say: str


@dataclass
class Script:
    date: str
    title: str
    description: str
    tags: list
    sources: list
    cards: list


def strip_marks(text: str) -> str:
    return re.sub(r"[\[\]]", "", text).replace("\n", " ").strip()


def load(path) -> Script:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    for key in ("date", "title", "segments", "sources"):
        if key not in data:
            errors.append(f"'{key}' 항목이 없습니다")
    if errors:
        raise ValueError("; ".join(errors))

    cards = []
    for seg in data["segments"]:
        label = seg.get("label", "")
        for raw in seg["cards"]:
            if isinstance(raw, str):
                show, say = raw, strip_marks(raw)
            else:
                show = raw["show"]
                say = raw.get("say") or strip_marks(show)
            if len(strip_marks(show)) > MAX_CARD_CHARS:
                errors.append(f"카드가 너무 깁니다({len(strip_marks(show))}자): {show}")
            if show.count("[") != show.count("]"):
                errors.append(f"대괄호 짝이 안 맞습니다: {show}")
            cards.append(Card(label, show, say))

    if not data["sources"]:
        errors.append("출처(sources)가 비어 있습니다")
    if errors:
        raise ValueError("\n".join(errors))

    return Script(
        date=data["date"],
        title=data["title"],
        description=data.get("description", ""),
        tags=data.get("tags", []),
        sources=data["sources"],
        cards=cards,
    )
