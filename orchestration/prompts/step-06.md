# step-06 — 검증 + 제출 준비

`../orchestration/prompts/RULES.md`의 공통 규칙을 적용하라. 이 스텝만 수행하고 정지한다.

## 작업

1. **직접 구동 검증**: 심사자 절차 그대로 — 플러그인을 로컬 marketplace에 등록하고 Codex에서 실행한다. **정상 시나리오 1개 + 예외(정보 부족/실패) 시나리오 1개 이상**을 실제로 실행하고, 입력→출력을 `context/verification.md`에 기록한다. (이 실행이 세션 로그에 남아야 문항 5와 정합된다)
2. 발견된 문제를 수정하고 재검증한다.
3. `question.md` 5문항 초안 완성: 자수(800/800/1000/800/800) 준수 — 자수 확인 결과를 기재. 문항 2 출처 URL은 `sources.md` 대장에서. 문항 3은 README와 일치. 문항 5는 verification.md 기반.
4. `../WORKFLOW.md`의 "제출 전 체크리스트" 전 항목을 수행한다 (zip 드라이런 포함: 루트에 `src/`·`README.md`·`logs/`만, ≤100MB).

## 산출물

- `context/verification.md`, `question.md`(완성 초안), 제출 준비된 폴더 상태

## 게이트

- [ ] 제출 전 체크리스트 전 항목 ✅
- [ ] question.md 자수 확인 결과 기재
- [ ] 검증 실행 기록이 세션 로그에 실존

## 종료

`context/JOURNAL.md`에 규격 보고 후 정지. (submission.zip 생성·업로드는 사용자가 수행)
