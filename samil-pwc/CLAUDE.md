# CLAUDE.md — 삼일PwC 제출 워크스페이스

이 폴더는 **삼일PwC** 예선 제출물 전용이다. 상위 워크스페이스(`../CLAUDE.md`)의 최우선 원칙을 그대로 상속한다.

## 목표

삼일PwC(그 산업·고객 포함)가 겪는 **실제 문제를 공개 자료로 입증**하고, 이를 해결하는 **Codex 플러그인**(src/ + SKILL.md)을 만들어 제출한다. 사람이 ~2주 걸릴 업무를 대체하는 **클러치 피처 하나**에 집중한다.

## 절대 규칙

- **다른 참가 회사**의 이름·리서치·코드·전략을 이 폴더에서 읽지도 쓰지도 않는다.
- `logs/`는 훅이 자동 생성한다. **절대 편집·발췌·삭제 금지** (실격 사유).
- 근거는 공개 URL만. AI 채팅에 비밀정보(API 키·토큰·비밀번호) 입력 금지.
- 리서치는 플러그인 설계에 필요한 만큼만 — 발견이 플러그인 결정으로 이어지지 않으면 중단.
- 검증(정상/예외 실행)은 이 폴더 세션에서 실제로 수행해 로그에 남긴다 — 문항 5와 정합해야 함.

## 산출물 (이 폴더에서 그대로 zip)

```
submission.zip = src/ (.codex-plugin/plugin.json 필수) + README.md + logs/
```

- `question.md`: 질문 5문항 초안 (zip에 넣지 않음 — 제출 폼에 입력)
- `research/`: problem.md, sources.md (zip에 넣지 않음)
- 제출 폼: https://hack.primer.kr/rounds/10/opportunities/5/submission/new
- 규정 상세: `../submission-spec.md` / 파이프라인: `../WORKFLOW.md` / 리서치 방법: `../RESEARCH_PLAYBOOK.md`

## 완료 기준

- [ ] `src/`가 Codex 플러그인으로 직접 구동됨 (로컬 marketplace 등록 → 실행 확인)
- [ ] `README.md`에 설치·실행법 + 작동 방식 (문항 3과 일치)
- [ ] `question.md` 5문항 자수 제한 내 완성 + 출처 URL 공개 접근 확인
- [ ] `logs/` ↔ 플러그인 ↔ `question.md` 정합
