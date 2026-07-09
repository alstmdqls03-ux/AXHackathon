# plan.md — 구현 계획 (step-05)

> 승인된 솔루션: 후보 2 하이브리드 (DECISION.md 2026-07-09). 스코프: 클러치 피처 하나의 최소 구성.

## src/ 구조

```
src/
├── .codex-plugin/plugin.json        # 필수 3필드: name·version·description (+skills 경로)
└── skills/
    └── haenggan-audit/              # 스킬 = 유일한 동작 구성 요소 (자기완결)
        ├── SKILL.md                 # 절차·지식·판단 기준·실패/정보부족 동작
        ├── hypotheses/
        │   ├── H1-accounting.md     # 가설군 1: 회계처리 오류 (독립 모듈)
        │   ├── H2-cashflow.md       # 가설군 2: 현금흐름 이상 (독립 모듈)
        │   └── H3-costing.md        # 가설군 3: 원가배분 왜곡 (독립 모듈)
        ├── scripts/
        │   └── checks.py            # 결정론 체커 — python3 표준 라이브러리만
        ├── templates/
        │   └── report-template.md   # SOP형 경영진 보고서 골격
        └── data/
            └── demo/                # 합성 데모: (주)한빛산업 FY2025 (시트 간 수치 정합)
                ├── trial_balance.csv
                ├── gl_entries.csv       # 주요 전표 발췌 샘플
                ├── monthly_series.csv
                ├── ar_aging.csv
                └── cost_allocation.csv
```

- MCP 서버·기타 실행 코드 없음 (step-04에서 기각). 축소 경로: `hypotheses/H2·H3.md` + checks.py 해당 함수 + `monthly_series/ar_aging/cost_allocation.csv` 삭제 → 후보 A (재설계 없음).

## 구현 순서 (DECISION 일정 게이트 정합)

1. **오늘 밤**: plugin.json → 데모 데이터 5종(수치 상호 정합 설계) → checks.py(H1·H2·H3 함수 모두 — 모듈러) → 스모크 실행 → SKILL.md·hypotheses·템플릿 → README.md
2. **내일 오전**: H2·H3 시나리오 검증(정상+예외 실행, 로그 확보) → 게이트 판단 → (불가 시) 축소 실행

## 검증 계획 (문항 5 대비 — 로그에 남김)

- **정상 1**: `python3 checks.py data/demo` → H1(#4712 자본화 3중 신호 + 수선비 -78%) / H2(이익-CF 괴리 3개월·DSO 상승·12월 스파이크·대한상사 편중) / H3(제품 B 마진 +12%→-3% 반전) 후보가 전부 잡히는지 + JSON 스키마 확인.
- **예외 1**: `monthly_series.csv` 제거 후 재실행 → H2 "skipped(사유 명시)" + H1·H3 정상 → 모듈 독립성 입증.
- (스킬 전체의 Codex 실행 검증은 심사 환경 기준 README 절차로 — 이 세션에서는 체커·데이터 레벨 검증을 로그로 남긴다.)

## 게이트 대응

- plugin.json name·version·description ✓ / SKILL.md 실패·정보부족 동작 §명시 ✓ / README ↔ 문항 3 동일 구조·내용 ✓
