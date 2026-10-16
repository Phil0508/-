"""대본 JSON 하나로 쇼츠 영상 + 업로드 정보를 만듭니다.

사용법:
    python make_short.py samples/example_script.json
    python make_short.py samples/example_script.json --tts silent   # 네트워크 없이 화면만 확인
"""

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

from pipeline import cards, render, script, tts

ROOT = Path(__file__).parent


def slugify(text):
    return re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-")[:40]


def upload_info(sc, cfg, seconds):
    src = "\n".join(f"- {s['name']}: {s['url']}" for s in sc.sources)
    desc = f"{sc.description}\n\n[출처]\n{src}\n\n{cfg['channel']['footer']}".strip()
    return {
        "title": sc.title,
        "description": desc,
        "tags": sc.tags,
        "seconds": round(seconds, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--tts", help="config.toml의 TTS 엔진 대신 사용 (edge | silent)")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cfg = tomllib.loads((ROOT / "config.toml").read_text(encoding="utf-8"))
    for key in ("font_bold", "font_regular"):
        cfg["style"][key] = str(ROOT / cfg["style"][key])
    if cfg["video"].get("bgm"):
        cfg["video"]["bgm"] = str(ROOT / cfg["video"]["bgm"])
    if args.tts:
        cfg["tts"]["engine"] = args.tts

    try:
        sc = script.load(args.script)
    except ValueError as e:
        sys.exit(f"대본 오류:\n{e}")

    out_dir = Path(args.out) / f"{sc.date}-{slugify(sc.title)}"
    (out_dir / "cards").mkdir(parents=True, exist_ok=True)
    (out_dir / "audio").mkdir(parents=True, exist_ok=True)

    images, audios, durations = [], [], []
    total = len(sc.cards)
    for i, card in enumerate(sc.cards):
        img = out_dir / "cards" / f"{i:02d}.png"
        cards.render(card, i, total, sc.date, sc.sources, cfg, img)
        aud = out_dir / "audio" / f"{i:02d}.mp3"
        try:
            durations.append(tts.synthesize(card.say, aud, cfg["tts"]))
        except Exception as e:
            sys.exit(f"음성 생성 실패 ({cfg['tts']['engine']}): {e}\n"
                     "인터넷 연결을 확인하거나, 화면만 볼 때는 --tts silent 로 실행하세요.")
        images.append(img)
        audios.append(aud)
        print(f"  [{i + 1}/{total}] {durations[-1]:.1f}s  {card.say}")

    video = out_dir / "short.mp4"
    seconds = render.build(images, audios, durations, video, cfg)

    info = upload_info(sc, cfg, seconds)
    (out_dir / "upload.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n완료: {video}  ({seconds:.1f}초)")
    if seconds > script.MAX_TOTAL_SECONDS_HINT:
        print(f"주의: {seconds:.0f}초입니다. 쇼츠는 60초 이하로 맞추세요(대본을 줄이거나 rate를 올리세요).")


if __name__ == "__main__":
    main()
