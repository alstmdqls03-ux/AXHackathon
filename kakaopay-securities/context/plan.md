# plan.md — 구현 계획 (step-05)

> 승인 스펙: `solution.md` §5 (후보 1 하이브리드, DECISION.md 승인 2026-07-09). 원칙: 클러치 피처 하나가 확실히 도는 최소 구성 — 표준 라이브러리만, MCP 서버 없음.

## src/ 구조

```
src/                                      # 플러그인 루트 (submission.zip의 src/)
├── .codex-plugin/
│   └── plugin.json                       # name·version·description (게이트 필수 3필드)
└── skills/
    └── trade-decision-report/
        ├── SKILL.md                      # 절차·판단 기준·실패/정보부족 동작
        ├── scripts/
        │   ├── diagnose.py               # 결정론 진단: trades.csv + 현재가·환율 → metrics JSON
        │   ├── render.py                 # 스키마 검증 + 고정 템플릿 조립 → 스탬프된 report.md
        │   └── check_docs.py             # 문서 규율 검사((추정) 표기·납득 프레임)
        └── samples/
            ├── trades.csv                # solution.md 공통 데모 샘플과 동일
            ├── options.sample.json       # 유효한 선택지 JSON (정상 데모)
            └── options_violation.json    # 서열화 어휘+숫자 리터럴 주입 (예외 데모)
```

## 강제 구조 → 코드 매핑 (solution.md §5 그대로)

| 제약 | 구현 위치 |
|---|---|
| 1 서열화 금지 | render.py: `options[].id` enum 4종(hold/partial_sell/dca/sell_all)·정확히 4개·제목은 render.py 하드코딩·가나다순 정렬·denylist 정규식(`RANKING_LANGUAGE_DETECTED`)·텍스트 필드 ≤200자 |
| 2 근거 접지 | render.py: `evidence[]`는 `^metrics\.[a-z_]+$` + 실존 id(`EVIDENCE_NOT_GROUNDED`); 서술 필드 숫자는 `{metrics.xxx}` 플레이스홀더만 — 치환 전 원문에 숫자 리터럴 잔존 시 `UNGROUNDED_NUMBER` |
| 3 고정 템플릿 | render.py가 [진단→선택지→체크리스트] 마크다운 전체를 조립, 경고 문구 하드코딩, `report.md` 파일 + 마지막 줄 report-id(sha256 앞 12자리) 스탬프 |
| 4 (추정)·납득 프레임 | check_docs.py: README/question.md에서 I-1·I-2·공백 표현 줄에 (추정) 필수 + README에 "정답이 아니라 납득 과정" 프레임 존재 확인 |

## 결정론 수치 규칙 (solution.md 데모 샘플과 일치해야 함)

- 원화: half-away-from-zero 정수 반올림 (−34,105.5 → −34,106). 퍼센트: 소수 2자리 half-away-from-zero.
- metric id는 solution.md 표기 유지: nominal_return_usd_pct, true_return_usd_pct(매수 수수료 포함), true_return_krw_pct, fx_effect_pp, unrealized_pnl_krw, realized_loss_if_sell_krw(음수=손실), tax_if_sell_krw(+ 보조 id: ticker, qty, avg_price_usd, avg_cost_usd, avg_buy_fx, price_now_usd, fx_now, invested_usd, invested_krw, value_now_usd, value_now_krw, sell_fee_usd).
- 세금: 해외주식 양도세 단순화 — max(0, 실현이익 − 250만) × 22%, 손실이면 0 (한계는 README 명시).
- 환율 방향 문구: fx_now vs avg_buy_fx 비교로 강세/약세 분기 (render.py).

## 데모 범위 (과잉 설계 차단)

단일 티커·미국 주식·BUY 내역만. SELL 행·복수 티커·기타 자산 → `UNSUPPORTED_SCOPE`. 시세·뉴스 조회 없음(모든 수치는 입력에서 유도).

## 구현 순서

1. plugin.json → 2. diagnose.py → 3. render.py → 4. 샘플 3종 → 5. SKILL.md → 6. 검증 실행 → 7. check_docs.py → 8. README.md → 9. JOURNAL.

## 검증 계획 (이 세션에서 실제 실행 — 로그 소재, 문항 5 정합)

- **정상 1**: `diagnose.py samples/trades.csv --price 160 --fx 1380` → metrics가 solution.md 기대값과 일치(−5.88/−5.95/−4.90/+1.05/−34,106/−34,569/0) → `render.py diagnosis.json options.sample.json` → 스탬프된 report.md 생성.
- **예외 1**: `--price` 누락 → `REQUIRED_INPUT_MISSING` (되묻기 메시지 포함).
- **예외 2**: options_violation.json → `RANKING_LANGUAGE_DETECTED` + `UNGROUNDED_NUMBER` 거부, report.md 미생성.
