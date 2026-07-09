# WORKFLOW.md — 예선 오케스트레이션 파이프라인

> **마감: 2026-07-10 (금) 23:59:59.** 세 회사는 같은 스텝 시퀀스를 독립적으로 통과한다.
> 오케스트레이터(루트 세션)가 스텝을 디스패치하고, 각 회사 pane은 **한 번에 한 스텝**만 수행 후 `context/JOURNAL.md`에 보고하고 정지한다.

## 스텝 파이프라인 (step-00 ~ step-06)

프롬프트 원문: `orchestration/prompts/step-NN.md` (공통 규칙: `orchestration/prompts/RULES.md`)

| 스텝 | 이름 | 산출물 | 게이트 |
|---|---|---|---|
| 00 | 출제자 의도 정리 | `context/intent.md` | 타임스탬프 근거, 사실/추정 구분, 최상위 가중치 명시 |
| 01 | 회사 컨텍스트 | `context/company.md` | 전 주장 URL+수집일, `[의도연결]` ≥3 |
| 02 | 공개 근거 대장 | `context/sources.md` | 모든 숫자·주장 대장 추적 가능, URL 접근성 확인 |
| 03 | 문제 후보 비교 + Opportunity Sizing | `context/problem.md` | 후보별 힌트영상 근거 ≥1, sizing 출처 — **⛔ 사용자 승인 게이트** |
| 04 | 솔루션 후보 + 확정 피치 | `context/solution.md` | 데모 시나리오 구체성, 실패 동작 포함 — **⛔ 사용자 승인 게이트** |
| 05 | 구현 Plan + 구현 | `context/plan.md`, `src/`, `README.md` | plugin.json 필수 필드, 실패 동작, README↔문항3 일치 |
| 06 | 검증 + 제출 준비 | `context/verification.md`, `question.md` | 제출 전 체크리스트 전 항목, 자수 확인, 검증이 로그에 실존 |

**원칙**: 문제는 출제자 힌트(영상 정리 파일 = 최상위 가중치)와 리서치 근거에서만 나온다. 모든 주장에 출처 URL + 수집일, 사실/추정 구분, 출처 없는 숫자 금지. 대화는 원본 그대로 제출 로그가 되므로 비밀정보 입력 금지.

## 오케스트레이션 운영

- **디스패치**: `orchestration/dispatch.sh step-NN [세션]` — pane에 "step-NN.md를 읽고 그대로 수행하라" 한 줄을 보낸다. 긴 지침은 항상 git 관리되는 프롬프트 파일로.
- **상태 확인**: `orchestration/status.sh [세션]` — pane 상태 / JOURNAL 완료 스텝·최근 요청 / 산출물 존재 / 로그 훅 동작을 한눈에.
- **진행 규칙**: 각 pane은 자기 속도로 진행하되(비동기), JOURNAL 게이트 체크가 ✅여야 다음 스텝을 디스패치한다. ❌면 보완 지시 후 재확인.
- **승인 게이트(⛔)**: step-03 완료 → 3사 problem.md 요약을 사용자에게 보고, 사용자가 문제를 선정해야 step-04 디스패치. step-04 완료 → 동일하게 솔루션 승인 후 step-05.
- 오케스트레이터(루트 세션)는 회사별 리서치·구현을 직접 하지 않는다 — 디스패치·검수·보고만.

## 제출 전 체크리스트 (step-06에서 회사별 수행)

- [ ] zip 드라이런: 심사자 관점에서 압축 해제 → 로컬 marketplace 등록 → Codex에서 실제 구동
- [ ] `plugin.json` 필수 필드 (name / version / description)
- [ ] `README.md` = 설치·실행법 + 문항 3 세부 내용과 일치
- [ ] `question.md` 5문항 자수 확인 (800/800/1000/800/800) + 출처 URL 로그인 없이 열리는지 확인
- [ ] `logs/` 원본 그대로 (훅 산출물 + 훅 미적용 도구 대화 원본 내보내기 포함)
- [ ] zip ≤100MB, 루트에 `src/`·`README.md`·`logs/`만
- **일찍 제출하고 개선한다**: 마감 전 재제출 가능하므로, 최소 동작 버전이 나오는 즉시 1차 제출.

## 로그 관리

- **회사 pane 세션**: 훅이 `<회사>/logs/claude-code/`에 자동 저장 → 그대로 zip에 포함.
- **루트(오케스트레이터) 세션**: 훅이 루트 `logs/`에 저장. 루트에서는 회사 내용을 다루지 않는 것이 원칙이므로 회사 zip에는 넣지 않는다.
- **서브에이전트·워크플로 transcript**: 해당 회사 작업이면 `<회사>/logs/orchestrator/`로 **복사** (복사는 가공이 아님 — 편집·발췌·삭제만 금지).
- **훅 미적용 도구**(NotebookLM·ChatGPT 웹 등) 대화는 원본 그대로 텍스트(md/txt/json/jsonl)로 내보내 해당 회사 `logs/`에 넣는다.
- 훅 설치(2026-07-09) 이전 세션은 transcript를 편집 없이 내보내 logs/에 추가 (운영진 답변으로 소급 인정).

## 참고

- 규정 전체: `submission-spec.md` / 리서치 방법: `RESEARCH_PLAYBOOK.md` / 최우선 원칙: `CLAUDE.md`
- Loop engineering(평가 기준 자동 업데이트)은 예선 범위에서 제외 — 마감 여유 시에만.
