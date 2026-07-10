# 제출 런북 — 채널톡 (마감 2026-07-10 23:59:59)

폼: https://hack.primer.kr/rounds/10/opportunities/1/submission/new
재제출 가능(마감 전) — 일찍 제출하고 필요 시 갱신.

## 0. 현재 상태

- `submission.zip` 생성됨 (2026-07-10, 121,661 bytes ≤100MB, 루트 = src/·README.md·logs/만).
- 드라이런 통과: 압축 해제 → marketplace 등록 → plugin add → /usr/bin/python3(3.9.6) 구동 확인.
- **주의**: 이 zip 생성 이후 채널톡 폴더에서 Claude/Codex 세션을 더 돌렸다면 1번부터 다시.

## 1. (세션 추가 작업했을 때만) zip 재생성

```bash
cd ~/code/ax-hackathon && orchestration/make_zip.sh channeltalk
```
- 마지막 세션 로그까지 포함되도록 **제출 직전** 실행이 원칙.
- 스크립트가 100MB 제한·루트 구성 자동 확인.

## 2. 폼 입력 — question.md에서 복사

`channeltalk/question.md`의 문항 1~5 본문을 붙여넣기 (제목·출처 블록·자수표는 제외).

| 문항 | 로컬 자수 | 제한 | 주의 |
|---|---|---|---|
| 1 | 672 | 800 | |
| 2 | 677 | 800 | |
| 3 | 996 | 1000 | ⚠️ 여유 4자 — 폼 카운터 필수 확인 |
| 4 | 731 | 800 | |
| 5 | 796 | 800 | ⚠️ 여유 4자 — 폼 카운터 필수 확인 |

- 로컬 측정은 개행 포함 len() 기준 — **폼 카운터가 다르면 폼 기준이 정답**.
- 초과 시 줄일 곳: 문항 3 "판정마다 confidence와 근거 티켓을 남기고" → "판정마다 confidence·근거 티켓을 남기고" / 문항 5 "(로그 동봉)" 삭제.

## 3. 출처 URL 입력 (문항 2 관련, 폼의 출처 필드)

7건 전부 2026-07-10 200 OK 확인됨. question.md의 "출처 URL" 블록에서 복사.
특히 4번째(안다르, 퍼센트 인코딩 긴 URL)는 붙여넣기 후 잘리지 않았는지 확인.

## 4. zip 업로드 & 제출

- `channeltalk/submission.zip` 업로드 (다른 회사 zip과 혼동 금지).
- 제출 완료 화면/메일 캡처 보관.

## 5. 제출 후

- 재작업 시: 수정 → 세션 종료 → `make_zip.sh channeltalk` → 재제출 (한 세트).
- logs/ 아래 파일은 어떤 경우에도 편집·삭제 금지 (실격 사유).
