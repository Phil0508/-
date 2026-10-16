"""AI 뉴스 후보 모으기 (구글 뉴스 RSS). 제목·링크·언론사만 가져오고 본문은 저장하지 않습니다.

    python -m pipeline.collect            # out/news.json 생성
"""

import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

QUERIES = ["인공지능", "생성형 AI", "OpenAI", "Claude Anthropic", "구글 제미나이", "AI 반도체"]
MAX_AGE_HOURS = 36
HISTORY = Path("data/used_links.txt")


def feed_url(query):
    q = urllib.parse.quote(f"{query} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"


def parse(xml_text, now=None):
    now = now or datetime.now(timezone.utc)
    items = []
    for it in ET.fromstring(xml_text).iter("item"):
        title = (it.findtext("title") or "").strip()
        source = (it.findtext("source") or "").strip()
        # 구글 뉴스 제목은 "기사 제목 - 언론사" 형식
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3]
        try:
            published = parsedate_to_datetime(it.findtext("pubDate"))
        except (TypeError, ValueError):
            continue
        if now - published > timedelta(hours=MAX_AGE_HOURS):
            continue
        items.append({
            "title": title,
            "source": source,
            "link": it.findtext("link"),
            "published": published.isoformat(),
        })
    return items


def collect():
    used = set(HISTORY.read_text().split()) if HISTORY.exists() else set()
    seen, out = set(), []
    for q in QUERIES:
        try:
            with urllib.request.urlopen(feed_url(q), timeout=15) as r:
                items = parse(r.read())
        except Exception as e:  # 한 검색어가 실패해도 나머지는 계속
            print(f"  {q}: 실패 ({e})", file=sys.stderr)
            continue
        for item in items:
            key = item["title"][:30]
            if item["link"] in used or key in seen:
                continue
            seen.add(key)
            item["query"] = q
            out.append(item)
    out.sort(key=lambda x: x["published"], reverse=True)
    return out


def mark_used(links):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a") as f:
        f.writelines(f"{link}\n" for link in links)


if __name__ == "__main__":
    news = collect()
    Path("out").mkdir(exist_ok=True)
    Path("out/news.json").write_text(json.dumps(news, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"후보 {len(news)}개 -> out/news.json")
    if not news:
        sys.exit(1)
