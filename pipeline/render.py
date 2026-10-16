"""카드 이미지 + 카드별 음성을 하나의 세로 영상으로 합칩니다 (ffmpeg)."""

import subprocess
from pathlib import Path


def _run(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _pad_audio(src, dst, seconds):
    # 길이를 정확히 맞춰 둬야 이어 붙였을 때 화면과 소리가 어긋나지 않습니다.
    _run(["-i", str(src), "-af", "apad", "-t", f"{seconds:.3f}",
          "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(dst)])


def build(images, audios, durations, out_path, cfg):
    vid = cfg["video"]
    gap = cfg["tts"].get("gap", 0.12)
    work = Path(out_path).parent / "work"
    work.mkdir(parents=True, exist_ok=True)

    slots = [d + gap for d in durations]
    total = sum(slots)

    padded = []
    for i, (a, s) in enumerate(zip(audios, slots)):
        p = work / f"pad_{i:02d}.wav"
        _pad_audio(a, p, s)
        padded.append(p)

    alist = work / "audio.txt"
    alist.write_text("".join(f"file '{p.resolve()}'\n" for p in padded))
    voice = work / "voice.wav"
    _run(["-f", "concat", "-safe", "0", "-i", str(alist), "-c", "copy", str(voice)])

    vlist = work / "video.txt"
    lines = [f"file '{Path(img).resolve()}'\nduration {s:.3f}\n" for img, s in zip(images, slots)]
    lines.append(f"file '{Path(images[-1]).resolve()}'\n")  # concat 데모서 규칙: 마지막 장 한 번 더
    vlist.write_text("".join(lines))

    color = cfg["style"]["progress"].lstrip("#")
    # 하단 진행 바: 화면 너비만큼의 색 막대를 왼쪽 밖에서 시간에 맞춰 밀어 넣습니다.
    graph = (
        f"[0:v]fps={vid['fps']},format=yuv420p[base];"
        f"color=c=0x{color}:s={vid['width']}x14:r={vid['fps']}[bar];"
        f"[base][bar]overlay=x='-W+W*t/{total:.3f}':y=H-14:shortest=1[v]"
    )

    inputs = ["-f", "concat", "-safe", "0", "-i", str(vlist), "-i", str(voice)]
    audio_map = ["-map", "1:a"]
    bgm = vid.get("bgm")
    if bgm:
        inputs += ["-stream_loop", "-1", "-i", bgm]
        vol = vid.get("bgm_volume", 0.12)
        graph += f";[2:a]volume={vol}[b];[1:a][b]amix=inputs=2:duration=first:normalize=0[a]"
        audio_map = ["-map", "[a]"]

    _run([
        *inputs, "-filter_complex", graph, "-map", "[v]", *audio_map,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart",
        str(out_path),
    ])
    return total
