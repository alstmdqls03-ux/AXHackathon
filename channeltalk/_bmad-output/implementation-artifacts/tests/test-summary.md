# Test Automation Summary — resolution-lift (2026-07-10)

## 프레임워크

stdlib `unittest` + `subprocess` (CLI E2E). 추가 설치 불필요 — `python3 tests/test_pipeline.py`로 실행.

## Generated Tests

### E2E Tests (tests/test_pipeline.py) — 7/7 통과

- [x] test_happy_path_end_to_end — load→simulate 전체 파이프라인, 60건/미해결 27건, 리포트 4종 생성, 해결률 55.0%→85.0% (question.md 문항 5와 정합)
- [x] test_missing_required_column_halts_with_template — 필수 컬럼 누락 시 템플릿 안내 + exit 1, 출력 미생성 (짐작 진행 금지)
- [x] test_non_utf8_csv_halts_with_guidance — CP949 CSV → UTF-8 재저장 안내 후 중단
- [x] test_pii_masking_covers_rrn_card_phone_email — 주민번호·카드번호·전화·이메일이 unresolved.json에 남지 않음
- [x] test_hallucinated_ticket_id_rejected — 시뮬레이션 티켓 ID 변조 → 환각 검출, 리포트 생성 거부
- [x] test_tampered_summary_rejected — summary.json 변조(total=0) → 정합 검증 실패로 중단
- [x] test_pipe_and_newline_in_llm_text_escaped — LLM 텍스트의 `|`·줄바꿈이 마크다운 표를 깨지 않음

### API Tests

해당 없음 (API 엔드포인트 없는 CLI 플러그인).

## Coverage

- CLI 스크립트: 2/2 (load.py, simulate.py)
- question.md 문항 5의 검증 주장(정상 1건 + 예외 2건) 전부 자동 테스트로 고정, ECH 리뷰 가드 4종 추가 커버

## Next Steps

- 제출 zip에는 tests/ 미포함 (규정: src/ + README.md + logs/) — 로컬 회귀용
- 스크립트 수정 시 `python3 tests/test_pipeline.py` 재실행
