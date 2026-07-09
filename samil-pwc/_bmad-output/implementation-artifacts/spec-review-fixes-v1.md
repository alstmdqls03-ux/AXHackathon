---
title: 'AI 심사 시뮬레이션 v1 수정 반영 (REVIEW-FIXES.md P0~P2)'
type: 'chore'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'ef1c22f40b7fb369636c572e04f668a74af3c44d'
context: ['{project-root}/context/REVIEW-FIXES.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** AI 심사 시뮬레이션(93/100)이 제출물의 감점 요인 9건(P0 3·P1 3·P2 3)을 지적했다 — 문항 간 모순, 단위 미선언, 로그 1차 증거 부재 등 심사자가 바로 잡는 급소 포함.

**Approach:** REVIEW-FIXES.md의 P0→P1→P2 순으로 전부 반영한다. 텍스트 수정(question.md·README·SKILL.md), 코드 정리(checks.py SYNONYMS), 로그 무편집 이동(P1-2), 체커 재실행으로 훅 로그에 1차 증거 남기기(P0-3)로 구성된다.

## Boundaries & Constraints

**Always:** logs/ 및 모든 *.jsonl 내용 수정·삭제 금지 — P1-2의 무편집 이동 절차(cp → cmp byte-identical → 원위치 제거)만 허용. question.md 수정 후 자수 재측정(문항 1·2·4·5 ≤800, 문항 3 ≤1000). 회사 간 분리 유지(samil-pwc 폴더 밖 수정 금지). 수치 주장(19건 등)은 실행으로 재확인 후 기재.

**Ask First:** 자수 제한을 넘겨야만 반영 가능한 문구가 생기는 경우(무엇을 줄일지). question.md 답변의 사실 주장 자체를 바꿔야 하는 경우(P0-1의 경위 서술 외).

**Never:** 로그 파일 열어서 고치기, checks.py 판정 로직 변경(P1-3은 dead code 제거만), 데모 CSV 수치 변경, 다른 회사 폴더 접근.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| P0-3 정상 재실행 | data/demo 전체 | 후보 19건, H1-CAP-4712·H2-DSO·H3-ALLOC-B 포함, exit 0 — 출력 원문을 응답 텍스트에 인용 | 19건 불일치 시 HALT(명세 수치 재협상) |
| P0-3 예외 재실행 | monthly_series.csv 제외 사본 | H2만 skip(필수 파일 부재), exit 0 — 출력 원문 인용 | 동일 |
| P1-2 로그 이동 | context/logs/claude-code/3dd43331….jsonl | cp → cmp 통과 → 원위치 제거, logs/stray/README.txt에 항목 추가 | cmp 불일치 시 원본 유지·HALT |
| P1-3 SYNONYMS 제거 후 | 전체 테스트 | tests/test_checks.py 5/5 통과 | 실패 시 원복 |

</frozen-after-approval>

## Code Map

- `question.md` — P0-1(문항4 (a) 최종 경위), P2-6(문항1 통계 연결); 헤더 자수 표기
- `README.md` — P0-2(단위 1줄), P1-1(간접원가 4계정 합), P2-4(사용자 순서 — README 기준인 CFO 우선으로 문항1을 정렬하는 게 아니라, 문항1과 README 중 한쪽 통일: README를 문항1 순서(삼일 실무자 우선)로 맞추면 자수 무관이므로 README 쪽 수정), P2-5(출력 예 코드블록)
- `src/skills/haenggan-audit/SKILL.md` — P0-2(입력 계약에 데모 단위 1줄), P1-3(동의어 매핑 주체 명확화는 이미 서술돼 있어 확인만)
- `src/skills/haenggan-audit/scripts/checks.py` — P1-3(미사용 SYNONYMS dict 삭제)
- `context/logs/claude-code/3dd43331….jsonl` — P1-2 이동 대상 (내용 불가침)
- `logs/stray/README.txt` — P1-2 항목 추가 (로그 아님·직접 작성 파일이라 편집 가능)
- `context/JOURNAL.md` — 완료 후 [step-07] 보고

## Tasks & Acceptance

**Execution:**
- [x] `question.md` — 문항4 (a)를 "403 → KDI 미러 1차 교체 → 재확인 시 불안정 → 동일 통계 보도 원문(세정신문) 최종 교체"로 수정 — P0-1 모순 해소
- [x] `src/skills/haenggan-audit/SKILL.md` — 입력 계약 데모 행에 "데모 금액 단위: 백만원" 명시 — P0-2
- [x] `README.md` — 데모 설명에 단위 1줄(8.4억=840백만원 대응), 검증 절 "제조간접비 4,200"→"간접원가 4계정 합 4,200", 사용자 순서 문항1과 통일, 실행 출력 예 코드블록 추가 — P0-2·P1-1·P2-4·P2-5
- [x] `question.md` — 문항1에 사후 적발(정정 공시·감리) 연결 구절이 이미 있는지 확인, 없으면 자수 내 추가 — P2-6
- [x] `src/skills/haenggan-audit/scripts/checks.py` — SYNONYMS dict 삭제(참조 0건 확인 후) — P1-3
- [x] 체커 정상+예외 재실행, 명령·출력 원문을 응답에 인용 — P0-3 (훅 로그 1차 증거)
- [x] `context/logs/claude-code/` 스냅샷을 무편집 이동 → `logs/stray/claude-code-context-snapshot/`, README.txt 항목 추가, 빈 디렉터리 정리 — P1-2
- [x] 자수 재측정 + `tests/test_checks.py` 재실행 — 회귀 확인
- [x] `context/JOURNAL.md` — [step-07] 심사 반영 수정 보고 (기존 규격: 한 일/핵심 발견과 결정/게이트 체크/오케스트레이터에게 요청)

**Acceptance Criteria:**
- Given 수정 완료 상태, when question.md 자수를 python len으로 재측정, then 전 문항 제한 내이고 헤더 표기와 일치
- Given 수정 완료 상태, when `python3 -m unittest tests.test_checks`, then 5/5 통과
- Given 이동 완료 상태, when `find src context -name "*.jsonl"`, then context/logs 잔존 0건이며 logs/stray에 byte-identical 사본 존재
- Given 전체 diff, when 검사, then logs/ 내 기존 파일·*.jsonl 내용 변경 0건

## Design Notes

- P2-4 방향: 문항 1(544자, 여유 256자)을 건드리기보다 README 7행의 순서를 문항 1 순서(삼일 회계사·컨설턴트 → 고객 CFO·재무팀)로 맞춘다 — 자수 리스크 0, 힌트 영상(삼일 관점) 정합도 상승.
- P1-3: SYNONYMS는 read_csv 어디서도 참조되지 않는 dead code(grep으로 확인 필요). 문항 3의 "동의어 매핑"은 SKILL.md 29행이 에이전트 절차로 이미 서술 — 체커 주석에서 매핑 암시만 제거하면 정합.

## Verification

**Commands:**
- `python3 src/skills/haenggan-audit/scripts/checks.py src/skills/haenggan-audit/data/demo --out /tmp/scratch/out.json` — expected: 후보 19건, exit 0
- `python3 -m unittest tests.test_checks -v` — expected: 5/5 OK
- `cmp <원본> <사본>` — expected: 출력 없음(byte-identical)
- `python3 자수 재측정 스크립트` — expected: 전 문항 제한 내

**Manual checks (if no CLI):**
- git diff에서 logs/·*.jsonl 콘텐츠 변경이 이동(rename/추가) 외 없는지 육안 확인
