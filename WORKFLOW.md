# WORKFLOW.md — 예선 파이프라인

> 원 플랜(Requirements → Research → Solution → Implementation → Scale) 5단계를 유지하되,
> **마감(2026-07-10 23:59:59)** 에 맞춰 타임박스와 게이트를 추가했다.
> 각 회사는 이 파이프라인을 **독립적으로** 통과한다. 회사 작업은 반드시 해당 회사 폴더 세션에서.

## 1. [Requirements] 해커톤 룰 파악 — ✅ 완료

- 산출물: `submission-spec.md` (과제 페이지·제출 폼·FAQ·운영 규정 원문 검증본)
- 핵심: 회사별 독립 zip(src+README+logs) / 5문항(800·800·1000·800·800자) + 출처 URL / 로그 원본 그대로 / 플러그인 직접 구동 / 마감 전 재제출 가능

## 2. [Research] 문제 정의 및 리서치 — 타임박스: 회사당 2~3시간

- 방법·출처 규칙: `RESEARCH_PLAYBOOK.md`
- **첫 작업**: 출제자 힌트 영상 전사·타임스탬프 요약 → `context/hint-video-transcript.md`, `context/hint-video.md` (출제 기업 직접 힌트 = 최상위 가중치)
- 산출물: `<회사>/context/` (hint-video*.md, problem.md, sources.md)
- **게이트**: ① Problem Statement 1개 확정 ② 공개 출처 URL 3개 이상(접근 확인) ③ "누가/어떤 상황에서/어디서 막히는가"가 문항 1·2 초안으로 바로 옮겨질 수 있는 상태

## 3. [Solution] 솔루션 선정 — 타임박스: 회사당 ~1시간

- 후보 2~3개 → 비용 · 내 역량 · 데모 가능성 기준으로 1개 선정 (클러치 피처)
- **아웃풋(데모 시나리오)을 먼저 문장으로 고정**: 입력 → 플러그인 동작 → 출력. 데모 가능 + 비주얼 요소.
- **게이트**: 문항 3(작동 방식: 절차·지식·판단 기준·실패 시 동작) 초안이 써지는 수준의 설계

## 4. [Implementation] 구현 + 검증 + 패키징 — 회사당 반나절

- `src/` 스캐폴드: `.codex-plugin/plugin.json`(name·version·description) + `skills/<이름>/SKILL.md` (+ 필요시 `.mcp.json`·실행 코드)
- 정보 부족·실패 상황의 동작을 반드시 설계에 포함 (문항 3 요구사항)
- **검증은 로그에 남긴다**: 정상 1개 + 예외 1개 이상 실제 실행 — 문항 5에 적을 내용은 logs/에서 재확인 가능해야 함 (정합성 채점)
- **제출 전 체크리스트** (회사별):
  - [ ] zip 드라이런: 심사자 관점에서 압축 해제 → 로컬 marketplace 등록 → Codex에서 실제 구동
  - [ ] `plugin.json` 필수 필드 (name / version / description)
  - [ ] `README.md` = 설치·실행법 + 문항 3 세부 내용과 일치
  - [ ] `question.md` 5문항 자수 확인 (800/800/1000/800/800) + 출처 URL 로그인 없이 열리는지 확인
  - [ ] `logs/` 원본 그대로 (훅 산출물 + 훅 미적용 도구 대화 원본 내보내기 포함)
  - [ ] zip ≤100MB, 루트에 `src/`·`README.md`·`logs/`만
- **일찍 제출하고 개선한다**: 마감 전 재제출 가능하므로, 최소 동작 버전이 나오는 즉시 1차 제출.

## 5. [Scale / Automation] Loop Engineering — 예선에서는 선택 (YAGNI)

- 평가 기준 업데이트 루프(goal setting → 검증 → refinement)는 마감 여유가 있을 때만.
- 본선 대비 자산으로는 유효 — 예선 마감 후 정리.

## 오케스트레이션 로그 관리

- **루트 세션**: 훅이 `logs/claude-code/`에 자동 저장. 루트에서는 회사 내용을 다루지 않는 것이 원칙이므로, 루트 로그는 회사 zip에 넣지 않는다.
- **회사 폴더 세션**: `<회사>/logs/`에 자동 저장 → 그대로 zip에 포함.
- **서브에이전트·워크플로 transcript**: `~/.claude/projects/<프로젝트>/...` 아래에 원본이 남는다. 해당 회사 작업이면 `<회사>/logs/orchestrator/`로 **복사**한다 (복사는 가공이 아님 — 편집·발췌만 금지).
- **훅 미적용 도구**(NotebookLM·ChatGPT 웹 등) 대화는 원본 그대로 텍스트(md/txt/json/jsonl)로 내보내 해당 회사 `logs/`에 넣는다.
- 훅 설치(2026-07-09) 이전 세션은 transcript를 편집 없이 내보내 logs/에 추가한다 (운영진 답변으로 소급 인정).
