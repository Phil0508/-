# AI 1분 뉴스 쇼츠 파이프라인

대본 JSON 하나로 1080×1920 쇼츠 영상과 업로드 정보(제목·설명·태그)를 만듭니다.

```bash
pip install -r requirements.txt
python make_short.py samples/example_script.json            # 음성 포함 (인터넷 필요)
python make_short.py samples/example_script.json --tts silent  # 무음으로 화면만 확인
```

결과물은 `out/<날짜>-<제목>/`에 생깁니다.

- `short.mp4`: 업로드할 영상
- `upload.json`: 제목, 설명(출처 포함), 태그
- `cards/`: 카드 이미지

매일 돌리는 순서와 대본 작성 규칙은 [CLAUDE.md](CLAUDE.md)에 있습니다.

## 필요한 것

- Python 3.11+, ffmpeg
- 인터넷: `news.google.com`(뉴스 수집), `speech.platform.bing.com`(음성)

## 진행 상황

- [x] 대본 → 카드 → 음성 → 영상 렌더
- [x] 뉴스 RSS 수집
- [ ] 매일 자동 실행 (Claude Code 예약 작업)
- [ ] 텔레그램 검토·승인
- [ ] 유튜브 업로드 API
- [ ] 배경 스톡 영상 (Pexels)

폰트: [Pretendard](https://github.com/orioncactus/pretendard) (SIL OFL 1.1, `assets/fonts/OFL.txt`)
