# step-05 — 구현 Plan + 구현

`../orchestration/prompts/RULES.md`의 공통 규칙을 적용하라. 이 스텝만 수행하고 정지한다.
**승인된 솔루션(step-04에서 사용자가 확정)만 구현한다.**

## 작업

1. **Plan**: `context/plan.md`에 작성 — src/ 구조(`.codex-plugin/plugin.json` 필수 필드, `skills/<이름>/SKILL.md`, 필요시 `.mcp.json`·실행 코드), 구현 순서, 검증 계획(정상 1 + 예외 1)
2. **구현**: `src/`를 실제로 구축한다. SKILL.md에는 절차·지식·판단 기준·**실패/정보부족 시 동작**을 담는다
3. **README.md**(폴더 루트) 작성: 개요 / 설치·실행(심사자용) / 작동 방식 / 검증 — 질문 문항 3과 일치해야 함
4. 과잉 설계 금지: 클러치 피처 하나가 확실히 도는 **최소 구성**

## 산출물

- `context/plan.md`, `src/` 전체, `README.md`

## 게이트

- [ ] plugin.json에 name · version · description
- [ ] SKILL.md에 실패·정보부족 동작 포함
- [ ] README ↔ 문항 3에 쓸 내용 일치

## 종료

`context/JOURNAL.md`에 규격 보고 후 정지.
