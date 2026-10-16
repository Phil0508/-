"""카드별 음성 만들기. 카드마다 따로 만들어서 길이를 재면 자막 타이밍이 정확히 맞습니다."""

import asyncio
import subprocess


def duration(path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _silent(text: str, path):
    # 한국어 낭독 속도 대략 초당 7~8자
    seconds = max(1.2, len(text.replace(" ", "")) * 0.14)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", f"{seconds:.2f}", "-c:a", "libmp3lame", "-q:a", "4", str(path)],
        check=True,
    )


async def _edge(text: str, path, voice: str, rate: str):
    import edge_tts

    await edge_tts.Communicate(text, voice, rate=rate).save(str(path))


def synthesize(text: str, path, cfg: dict) -> float:
    engine = cfg.get("engine", "edge")
    if engine == "silent":
        _silent(text, path)
    elif engine == "edge":
        asyncio.run(_edge(text, path, cfg["voice"], cfg.get("rate", "+0%")))
    else:
        raise ValueError(f"알 수 없는 TTS 엔진: {engine}")
    return duration(path)
