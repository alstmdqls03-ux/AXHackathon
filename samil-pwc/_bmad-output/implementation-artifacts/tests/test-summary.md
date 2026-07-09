# 테스트 자동화 요약 — haenggan-audit 체커 계층

- 일자: 2026-07-10
- 프레임워크: Python stdlib `unittest` (프로젝트가 순수 stdlib이므로 외부 의존성 미추가)
- 실행: `python3 -m unittest tests.test_checks -v` (프로젝트 루트)
- 결과: **5/5 통과**

## 생성된 테스트

### E2E (checks.py — 데모 데이터 기준)

- [x] `tests/test_checks.py::test_happy_path_demo_data` — 정상: 후보 19건, 심은 문제 3건(H1-CAP-4712·H2-DSO·H3-ALLOC-B) 신호 포착, skip 없음, exit 0
- [x] `tests/test_checks.py::test_missing_file_skips_only_that_hypothesis` — monthly_series.csv 부재 → H2만 skip("필수 파일 부재"), H1·H3 정상, exit 0
- [x] `tests/test_checks.py::test_broken_file_skips_with_reason` — 파싱 불가 파일 → 해당 가설군만 "파싱 실패" 사유로 skip, exit 0
- [x] `tests/test_checks.py::test_all_files_missing_reports_all_skipped` — 전 파일 부재 → 3종 전부 skip 보고, 후보 0건, exit 0
- [x] `tests/test_checks.py::test_missing_data_dir_exits_2` — data_dir 부재 → exit 2 + 안내 메시지

API/UI 테스트: 해당 없음 (API·UI 없는 CLI 체커 + 마크다운 스킬).

## 테스트가 발견해 수정한 버그

- `checks.py` skip 사유 오표기: 파일이 존재하지만 파싱 불가일 때 "필수 파일 부재"로 보고 → `missing` 계산에서 `load_errors` 제외(1줄 수정)로 "파싱 실패: <사유>" 정확 보고. 후보 수·심은 문제 검출에는 영향 없음(happy path 19건 그대로 통과 = question.md 문항 5 정합 유지).

## 커버리지

- checks.py 실행 경로: 정상 1 + 예외 4 (파일 부재/파손/전체 부재/폴더 부재) — SKILL.md "정보 부족·실패 시 동작" ①②와 대응
- 미커버: 에이전트 계층(가설 모듈 판단·보고서 생성) — Codex 실행이 필요해 자동화 범위 밖

## 다음 단계

- 제출 zip 재생성 시 이 수정(checks.py 1줄)이 포함된 상태로 생성
- tests/는 zip 구성요소(src/·README·logs) 밖이므로 제출물 오염 없음
