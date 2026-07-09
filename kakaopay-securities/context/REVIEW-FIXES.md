# REVIEW-FIXES.md — AI 심사 시뮬레이션 v1 결과 반영 (2026-07-10)

> AI 심사위원 채점: **95/100, 그러나 치명 플래그 2건** — 이걸 지우지 않으면 총점과 무관하게 1등 불가.
> 불변 규칙: logs/ 및 *.jsonl 내용 수정·삭제 절대 금지 (아래 P0-1의 "무편집 이동"만 예외적으로 허용된 처리다). question.md 자수 제한 유지, 수정 후 재측정.

## P0-1 — src/ 안의 로그 스냅샷 처리 (치명 플래그)

`src/skills/trade-decision-report/logs/claude-code/a75e0fe7-*.jsonl`은 정식 로그(logs/claude-code/의 67KB)의 **잘린 prefix 사본**(54KB, 훅 cwd 부작용) — 심사자가 "발췌된 로그"로 오해할 소지.
**무편집 이동으로 처리하라** (이미 검증된 절차): ① `logs/stray/claude-code/`로 cp ② `cmp`로 byte-identical 확인 ③ 확인 후에만 원위치 제거 ④ 빈 디렉터리 정리 ⑤ `logs/stray/README.txt` 생성(훅 cwd 부작용 경위 + 동일 세션 전체 로그 위치 명시). 설치 캐시본(~/.codex/plugins/cache/)에 전파된 사본도 동일 정리.

## P0-2 — 로그 1차 증거 보강 (치명 플래그)

훅은 대화 텍스트만 저장한다 — 현재 logs/에는 검증의 "요약 서술"만 있고 **report-id 8d1a510771e6·명령·출력 원문이 없다** (문항 5의 "실행 기록은 전부 logs/에" 주장이 문자 그대로는 거짓이 됨).
이 세션에서 README 검증 시퀀스(정상 1 + 예외 3 + check_docs)를 **다시 실제 실행**하고, **명령 원문과 핵심 출력(7개 지표 수치, report-id, 거부 코드 3종)을 너의 응답 텍스트에 그대로 인용**하라 — 훅 로그에 1차 증거로 남도록.

## P1 — 출처 정밀도 (Q2 +1.5) & 설치 재현성

1. 문항 2 수치 표현 3건 정정 (인용 페이지 원문 기준):
   - "약 20.4만 명" → **"약 20만 명"** (kcmi 1481 초록 표기)
   - "2배 이상 먼저 파는" → **"약 두 배 먼저 파는"** (41% vs 22% = 1.86배, 원문 "약 두 배 가량")
   - "1,600%를 넘었으며" → **"1,600%에 달했으며"** (원문 "달했던")
2. README 설치 1–2단계를 실제 검증된 명령 원문으로 교체: marketplace 루트 구조 예시(`plugins/trade-decision-report` + `.agents/plugins/marketplace.json` 내용) + `codex plugin marketplace add <root>` + `codex plugin add trade-decision-report@<marketplace명>` — 심사자가 축자 재현 가능하게.

## P2 — 다듬기

3. 문항 4 "받아들이지 않은 AI 제안" → "후보 비교에서 기각한 대안"으로 리워딩 (로그상 AI는 하이브리드를 추천했음 — 과장 인상 제거).
4. README check_docs.py 사용법에 `<폴더>` = zip 루트(README.md 위치)임을 명시.
5. README·문항 5의 수익률 병치에 USD 실질 -5.95%를 포함해 산술이 문장 안에서 닫히게.
6. tests/test_pipeline.py를 src/에 포함하거나 README에 실행법 한 줄 추가.

## 완료 보고

전 항목 반영 후 자수 재측정 결과와 함께 `context/JOURNAL.md`에 `[step-07] 심사 반영 수정` 규격 보고 후 정지.
