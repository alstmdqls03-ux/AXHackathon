---
title: '심사 시뮬레이션 반영 수정 (REVIEW-FIXES P0~P2)'
type: 'chore'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'ef1c22f40b7fb369636c572e04f668a74af3c44d'
context: ['{project-root}/context/REVIEW-FIXES.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** AI 심사 시뮬레이션(95/100)이 치명 플래그 2건을 지목 — ① src/ 안의 잘린 로그 prefix 사본(발췌 오해 소지), ② logs/에 검증 1차 증거(명령·출력 원문·report-id) 부재로 문항 5 주장이 문자 그대로 거짓. P1(출처 정밀도·설치 재현성)·P2(다듬기 4건)도 감점 요인.

**Approach:** REVIEW-FIXES.md의 9개 항목을 P0→P1→P2 순으로 전부 반영. 로그는 무편집 이동만, 문서는 자수 재측정 동반.

## Boundaries & Constraints

**Always:** logs/·*.jsonl 내용 수정·삭제 금지 — P0-1의 cp→cmp(byte-identical 확인)→원본 제거 절차만 허용. question.md 수정 후 전 문항 자수 재측정(≤800/1000). 완료 후 context/JOURNAL.md에 [step-07] 규격 보고(기존 항목 형식: 한 일/핵심 발견과 결정/게이트 체크/오케스트레이터에게 요청).

**Ask First:** cmp 불일치 등 무편집 이동의 전제가 깨지는 경우. 자수 조정이 사실 주장 변경을 요구하는 경우.

**Never:** 다른 회사 폴더 접근. 로그 내용 편집·발췌. 검증 결과 과장(모델 턴 미검증 사실 유지).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| P0-1 이동 | src/…/logs/ 사본(53,941B, 정식 로그의 exact prefix — 검증 완료) | logs/stray/claude-code/로 이동 + README.txt(경위·전체 로그 위치), src/·캐시에서 제거 | cmp 불일치 시 HALT |
| P0-2 재실행 | README 검증 시퀀스(정상1+예외3+check_docs) | 명령 원문+핵심 출력(7개 지표·report-id 8d1a510771e6·거부 코드 3종)을 응답 텍스트에 그대로 인용 → 훅 로그에 1차 증거 | 출력이 기대값과 다르면 HALT |
| 자수 초과 | 문항 5에 -5.95% 추가 시 787→800 초과 | 같은 문항 내 압축으로 상쇄, 사실 주장 불변 | 재측정 후 초과면 재압축 |

</frozen-after-approval>

## Code Map

- `src/skills/trade-decision-report/logs/claude-code/a75e0fe7-*.jsonl` — P0-1 이동 대상 (67KB 정식본의 prefix)
- `~/.codex/plugins/cache/kakaopay-local/trade-decision-report/0.1.0/skills/trade-decision-report/logs/` — P0-1 캐시 전파본
- `question.md` — P1-1(문항2 표현 3건), P2-3(문항4 리워딩), P2-5(문항5 -5.95% 병치)
- `README.md` — P1-2(설치 1–2단계 실측 명령), P2-4(check_docs 폴더 설명), P2-5, P2-6(tests 실행법)
- `context/verification.md` — P1-2의 검증된 명령 원문 소스 (codex plugin marketplace add / plugin add / list)
- `tests/test_pipeline.py` — P2-6 참조 대상 (7건 통과 확인됨)
- `context/JOURNAL.md` — [step-07] 보고 대상

## Tasks & Acceptance

**Execution:**
- [x] `logs/stray/` — P0-1: cp → cmp → 원위치 제거 → 빈 디렉터리 정리 → README.txt 생성 → 캐시본 동일 처리 -- 발췌 오해 제거, 로그 불가침 유지
- [x] (세션 응답 텍스트) — P0-2: 검증 시퀀스 재실행 + 명령·출력 원문 인용 -- logs/에 1차 증거 적재
- [x] `question.md` — P1-1: "약 20.4만 명"→"약 20만 명", "2배 이상 먼저 파는"→"약 두 배 먼저 파는", "1,600%를 넘었으며"→"1,600%에 달했으며" -- 인용 원문 정합
- [x] `README.md` — P1-2: 설치 1–2단계를 marketplace 루트 구조 예시+실측 명령으로 교체 -- 축자 재현성
- [x] `question.md` — P2-3: 문항 4 "받아들이지 않은 AI 제안"→"후보 비교에서 기각한 대안" -- 과장 인상 제거
- [x] `README.md` — P2-4: check_docs `<폴더>`=zip 루트(README.md 위치) 명시; P2-6: tests 실행법 한 줄(`python3 -m unittest discover tests -v`) -- src/ 포함 대신 README 안내(더 단순)
- [x] `README.md`+`question.md` — P2-5: 수익률 병치에 USD 실질 -5.95% 포함 -- 산술이 문장 안에서 닫힘
- [x] `question.md` 하단 자수 표 — 전 문항 재측정·갱신
- [x] `context/JOURNAL.md` — [step-07] 심사 반영 수정 보고 append

**Acceptance Criteria:**
- Given 이동 완료 상태, when `find src -name "*.jsonl"` 실행, then 결과 0건이고 logs/stray/에 byte-identical 사본+README.txt 존재
- Given 수정된 question.md, when 자수 재측정, then 전 문항 제한 내
- Given 재실행된 검증, when 세션 응답 확인, then report-id 8d1a510771e6과 거부 코드 3종 원문이 응답 텍스트에 존재

## Verification

**Commands:**
- `find src ~/.codex/plugins/cache/kakaopay-local -name "*.jsonl" | wc -l` -- expected: 0
- `cmp logs/stray/claude-code/a75e0fe7-*.jsonl <이동 전 사본>` -- expected: 실행 순서상 이동 전 cmp 통과가 전제
- `python3 -m unittest discover tests -v` -- expected: 7건 OK (회귀 없음)
- 자수 측정 스크립트 -- expected: 전 문항 통과
