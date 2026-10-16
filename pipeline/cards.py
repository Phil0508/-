"""카드 이미지(1080x1920) 그리기.

쇼츠는 하단(제목·채널명)과 오른쪽(좋아요 버튼)이 UI에 가려지므로
본문은 화면 위쪽 중앙(약 y 520~1250)에만 둡니다.
"""

import re

from PIL import Image, ImageDraw, ImageFont

TEXT_LEFT = 90
TEXT_WIDTH = 860
TEXT_CENTER_Y = 860
LINE_GAP = 1.28


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _background(w, h, top, bottom):
    t, b = _hex(top), _hex(bottom)
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / (h - 1)
        grad.putpixel((0, y), tuple(round(t[i] + (b[i] - t[i]) * k) for i in range(3)))
    return grad.resize((w, h))


def _tokens(show: str):
    """'[GPT-6]이 공개' -> [[('GPT-6', True), ('이', False)], [('공개', False)]]

    단어 하나는 (글자, 강조여부) 조각들의 목록이라 '[사람]이'처럼 단어 중간에서 색만 바뀝니다.
    줄바꿈은 None.
    """
    words, word = [], []
    accent = False
    for ch in show:
        if ch == "[":
            accent = True
        elif ch == "]":
            accent = False
        elif ch in " \n":
            if word:
                words.append(word)
                word = []
            if ch == "\n":
                words.append(None)
        elif word and word[-1][1] == accent:
            word[-1] = (word[-1][0] + ch, accent)
        else:
            word.append((ch, accent))
    if word:
        words.append(word)
    return words


def _wlen(font, word):
    return sum(font.getlength(t) for t, _ in word)


def _wrap(tokens, font, max_w):
    space = font.getlength(" ")
    lines, line, width = [], [], 0.0
    for word in tokens:
        if word is None:
            lines.append(line)
            line, width = [], 0.0
            continue
        w = _wlen(font, word)
        if line and width + space + w > max_w:
            lines.append(line)
            line, width = [], 0.0
        line.append(word)
        width += (space if len(line) > 1 else 0) + w
    if line:
        lines.append(line)
    return lines


def _fit(tokens, path, size, max_w, max_lines=4):
    while size > 48:
        font = ImageFont.truetype(path, size)
        lines = _wrap(tokens, font, max_w)
        if len(lines) <= max_lines and all(
            sum(_wlen(font, w) for w in ln) + font.getlength(" ") * (len(ln) - 1) <= max_w
            for ln in lines
        ):
            return font, lines
        size -= 6
    font = ImageFont.truetype(path, size)
    return font, _wrap(tokens, font, max_w)


def render(card, index, total, date, sources, cfg, path):
    st, vid = cfg["style"], cfg["video"]
    w, h = vid["width"], vid["height"]
    img = _background(w, h, st["bg_top"], st["bg_bottom"])
    d = ImageDraw.Draw(img)

    small = ImageFont.truetype(st["font_regular"], 40)
    brand = ImageFont.truetype(st["font_bold"], 46)
    label_font = ImageFont.truetype(st["font_bold"], 52)

    # 상단 브랜드 배지 + 날짜
    name = cfg["channel"]["name"]
    bw = brand.getlength(name) + 56
    d.rounded_rectangle((TEXT_LEFT, 250, TEXT_LEFT + bw, 334), radius=42, fill=_hex(st["brand_bg"]))
    d.text((TEXT_LEFT + 28, 292), name, font=brand, fill=_hex(st["brand_text"]), anchor="lm")
    d.text((TEXT_LEFT + bw + 28, 292), date, font=small, fill=_hex(st["sub"]), anchor="lm")

    # 본문
    font, lines = _fit(_tokens(card.show), st["font_bold"], st["main_size"], TEXT_WIDTH)
    line_h = font.size * LINE_GAP
    top = TEXT_CENTER_Y - line_h * len(lines) / 2
    space = font.getlength(" ")

    if card.label:
        d.text((TEXT_LEFT, top - 70), card.label, font=label_font, fill=_hex(st["accent"]), anchor="ls")

    for i, ln in enumerate(lines):
        x, y = TEXT_LEFT, top + line_h * i + font.size
        for word in ln:
            for text, accent in word:
                d.text((x, y), text, font=font, fill=_hex(st["accent"] if accent else st["text"]), anchor="ls")
                x += font.getlength(text)
            x += space

    # 카드 번호 / 출처
    d.text((TEXT_LEFT, 1330), f"{index + 1} / {total}", font=small, fill=_hex(st["sub"]), anchor="ls")
    names = ", ".join(s["name"] for s in sources)
    d.text((TEXT_LEFT, 1390), f"출처: {names}"[:40], font=small, fill=_hex(st["sub"]), anchor="ls")

    img.save(path)
