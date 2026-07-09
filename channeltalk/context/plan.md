# plan.md — resolution-lift 구현 계획 (step-05)

> 승인 솔루션(`DECISION.md`): S2 하이브리드 — 결정적 스크립트 + LLM 판단, Python 표준 라이브러리만, 네트워크·API 키 불요, 합성 데이터 동봉.

## src/ 구조

```
src/
├── .codex-plugin/plugin.json      # 필수: name=resolution-lift, version, description, skills
├── skills/resolution-lift/SKILL.md # 동작 구성 요소: 절차·판단 기준·프롬프트·실패 동작
├── scripts/
│   ├── load.py                    # 1단계: 적재·스키마 검증·PII 마스킹·미해결 분리 (결정적)
│   └── simulate.py                # 4단계: LLM 산출물 스키마 검증·집계·리포트 4종 렌더 (결정적)
└── examples/
    ├── tickets.csv                # 합성 상담 로그 60건 (해결 33 / 미해결 27, 패션 커머스 가정)
    ├── faq.csv                    # 기존 지식 12건
    └── broken/tickets-broken.csv  # 예외 데모용 (question 컬럼 누락)
```

## 파이프라인 계약 (파일 경유)

| 단계 | 담당 | 입력 → 출력 |
|---|---|---|
| 1 적재·검증 | `load.py` | tickets.csv, faq.csv → `out/summary.json`, `out/unresolved.json`, `out/faq.json` |
| 2 갭 분류 | LLM(Codex, SKILL.md 기준) | unresolved.json, faq.json → `out/gaps.json` (클러스터·유형 A/B/C/D/REVIEW·confidence·근거 티켓) |
| 3 초안 생성 | LLM | gaps.json → `out/faq_draft.json` (A/B 갭별 질문 변형 3 + 답변, 근거 없으면 policy_check=true) |
| 4 재시뮬레이션 | LLM 채점 → `simulate.py` 검증·집계 | simulation.json (티켓별 해결/부분/미해결) → `gap-report.md`, `faq-draft.md`, `validation-report.md`, `report.html` |

핵심 불변식(simulate.py가 강제): LLM이 만든 JSON의 티켓 ID는 실제 로그에 존재해야 하고(환각 ID 차단), simulation은 미해결 전건을 커버해야 하며, 스키마·라벨 값이 어긋나면 리포트를 만들지 않고 중단.

## 구현 순서

1. `plugin.json` → 2. 합성 데이터(examples/) → 3. `load.py` → 4. `simulate.py` → 5. `SKILL.md` → 6. 스모크 테스트 → 7. `README.md`(루트)

## 검증 계획 (step-06에서 전체 사이클 실행, 로그에 기록)

- **정상 1**: examples 데이터로 4단계 완주 → 리포트 4종 생성, before/after 해결률 표시 (55% → 개선치, 합성 데이터 기준 명시)
- **예외 1**: `examples/broken/tickets-broken.csv` → load.py가 필수 컬럼 안내 + CSV 템플릿 출력 후 비정상 종료(exit 1), 짐작 진행 없음
- (보조) 예외 2: 근거 없는 갭(C 정책) → faq_draft에 자동 확정 없이 policy_check 마커 확인
- step-05에서는 스크립트 단위 스모크(정상 적재 27건 분리 / broken 중단 / simulate.py 입력 누락 안내)만 수행

## 과잉 설계 금지 체크

- 외부 의존성 0 (csv·json·re·html 표준 모듈만), 설정 파일 없음, 클래스 계층 없음
- 클러스터링 알고리즘·임베딩 없음 — 분류 판단은 전부 SKILL.md의 LLM 기준 (판단 기준이 심사 대상[02:12])
- 리포트는 정적 HTML 1장(인라인 CSS 막대), JS 라이브러리 없음
