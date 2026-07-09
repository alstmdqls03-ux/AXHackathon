# verification.md — 직접 구동 검증 기록 (step-06)

> 실행 일시: 2026-07-09 23:33~23:45 KST. 모든 실행은 이 폴더 세션(Claude Code, logs/claude-code/에 훅 자동 기록) 및 Codex CLI(로그 원본을 logs/codex/에 복사)에서 실제 수행됨 — 문항 5와 정합.

## A. 심사자 절차 재현 (로컬 marketplace 등록 → Codex 실행)

환경: Codex CLI 0.142.5 (macOS), Python 3.x (표준 라이브러리만 사용)

1. **marketplace 구성**: 임시 디렉터리에 `resolution-lift/`(= `src/` 복사) + 매니페스트 생성.
   - 실증 발견: 매니페스트 위치는 **`<마켓플레이스 루트>/.agents/plugins/marketplace.json`** 이어야 함 (루트 `marketplace.json`·`.codex-plugin/marketplace.json`은 "marketplace root does not contain a supported manifest" 오류 — README 설치 절차에 반영).
2. **등록·설치**:
   ```
   codex plugin marketplace add <마켓플레이스 경로>   → Added marketplace `ax-local`
   codex plugin add resolution-lift@ax-local          → Installed plugin root: ~/.codex/plugins/cache/ax-local/resolution-lift/1.0.0
   ```
3. **실행**: `codex exec -C <이 폴더> -s workspace-write --dangerously-bypass-hook-trust "resolution-lift 스킬을 사용해 상담 로그 해결률 개선 사이클을 완주해줘. 입력: src/examples/tickets.csv 와 src/examples/faq.csv, 작업 디렉터리: out/. …"`

## B. 정상 시나리오 (합성 로그 60건, Codex가 스킬로 실행)

**입력**: `src/examples/tickets.csv`(60건), `src/examples/faq.csv`(12건)

**Codex 실행 경과** (세션 로그: `logs/codex/rollout-2026-07-09T23-36-03-….jsonl`):
- 1단계: `load.py` 실행 → 총 60 / 해결 33 / 미해결 27 (기준 해결률 55.0%)
- 2단계: Codex(LLM)가 미해결 27건 전건을 7개 클러스터로 분류 (`out/gaps.json`) — 상품 케어 A(9) / 쿠폰 조건 B(7) / 해외 배송 B(4) / 환불계좌 안내 A(2) / 환불계좌 처리 D(2) / 제휴 할인 C(2) / 감정 표현 REVIEW(1). 유형·confidence·근거 티켓·판단 사유 전부 기재.
- 3단계: A·B 클러스터 4개에만 FAQ 초안 생성 (`out/faq_draft.json`) — **C(정책)·D(태스크)·REVIEW에는 초안을 만들지 않음 (가드레일 작동 확인)**
- 4단계: 27건 전건 재시뮬레이션 채점 (`out/simulation.json`) — 판정 사유에 근거 지식 명시, '부분' 5건(예: 본인 인증이 남는 환불계좌 건)을 관대하게 '해결'로 치지 않음
- **Codex 사용량 한도 도달**: simulation.json 작성 직후 "You've hit your usage limit" (계정 무료 한도) — 마지막 결정적 단계만 남긴 시점. 잔여 단계인 `python3 src/scripts/simulate.py out`(스크립트, LLM 불필요)을 이 세션에서 직접 실행해 완결.

**출력** (`out/`):

| 지표 | 값 |
|---|---|
| 기준(현행 지식) 해결 | 33/60 (55.0%) |
| 초안 반영 시뮬레이션 해결 | 51/60 (85.0%) |
| 상승분 | **+18건 (+30.0%p)** — 시뮬레이션 판정값 |
| '부분' 판정 (보수적으로 미해결 집계) | 5건 |
| 사람 몫으로 분리된 갭 | C 2건, D 2건, REVIEW 1건 (faq-draft.md "사람 몫" 목록) |

생성물: `gap-report.md`, `faq-draft.md`, `validation-report.md`, `report.html` (before/after 막대 대시보드)

**검증 게이트 통과 확인**: simulate.py가 스키마·환각 티켓 ID·전건 커버를 검사 후 "검증 통과" 출력 (환각 ID 거부 동작은 step-05 스모크에서 별도 확인 — ID 1건 변조 시 리포트 생성 거부).

## C. 예외 시나리오 (정보 부족 — 필수 컬럼 누락)

**입력**: `src/examples/broken/tickets-broken.csv` (question 컬럼 대신 content)

**결과**: exit 1 — "필수 컬럼이 없습니다: question / 발견된 컬럼: ticket_id, created_at, content, resolved" + CSV 템플릿 출력. **out-broken/ 미생성 — 짐작으로 진행하지 않음 확인.**

## D. 추가 확인된 가드레일 (정상 실행 안에서)

- C 클러스터(임직원·제휴 할인): 상담사 답변 부재 → 초안 미생성, "사람이 방침을 결정해야" 목록으로 분리 — **정책을 지어내지 않음**
- REVIEW(감정 표현): 지식 갭으로 확정하지 않고 사람 검토 큐로
- validation-report에 "시뮬레이션 판정값, 실측 아님" 고지 자동 포함

## E. 이슈·수정 기록

1. **(step-05에서 수정)** load.py `--out` 값이 위치 인자로 집계되는 파싱 버그 → argparse 교체 후 재검증.
2. **marketplace 매니페스트 위치** — 공개 문서 표현과 달리 로컬 마켓플레이스는 `.agents/plugins/marketplace.json`만 인식됨을 실증, README에 정확 절차 반영 필요(→ 반영함).
3. **Codex 사용량 한도** — LLM 단계는 전부 완료된 뒤 도달. 잔여는 결정적 스크립트라 파이프라인 신뢰성에 영향 없음. 단 재실행 데모가 필요하면 유료 계정 또는 타 Codex 계정 필요.
4. **로그 반입 사고 원상복구 (투명성 기록)**: Codex 세션 원본을 logs/codex/로 복사하는 과정에서, 같은 시간대에 병렬 실행 중이던 **다른 회사 폴더(cwd 상이)의 세션 파일 1개를 실수로 함께 복사**했다가 cwd 확인 즉시 그 복사본만 제거함(23:40, 원본은 ~/.codex/sessions에 그대로). 채널톡 자체 세션 로그는 일절 편집·삭제하지 않음 — 회사 간 분리 원칙 준수를 위한 조치이며 전 과정이 이 세션 로그에 남아 있음.

## F. 한계 (정직 고지)

- 동봉 데이터는 합성 데이터(패션 커머스 가정) — 실제 채널톡 수출 로그 형식과 컬럼명이 다를 수 있어 load.py가 스키마 안내로 흡수하도록 설계했으나 실로그 검증은 미수행.
- +30.0%p는 LLM 재시뮬레이션 판정값이며 실측 아님(리포트에 자동 고지).
