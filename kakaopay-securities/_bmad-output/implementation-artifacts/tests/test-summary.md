# Test Automation Summary — trade-decision-report (2026-07-10)

## Generated Tests

### E2E Tests (CLI 블랙박스, 표준 라이브러리 unittest)

- [x] `tests/test_pipeline.py` — diagnose.py + render.py 파이프라인 7건, 전체 통과

| 테스트 | 검증 내용 | question.md 정합 |
|---|---|---|
| test_happy_path_matches_expected_metrics | samples/trades.csv + 현재가 160·환율 1380 → metrics가 samples/diagnosis.json과 전항 일치 (결정론) | 문항 5 정상 경로 |
| test_missing_price_asks_instead_of_guessing | 현재가 누락 → REQUIRED_INPUT_MISSING + 필요한 필드·이유 반환, 추정값 대입 없음 | 문항 5 예외 ① |
| test_sell_row_rejected_as_out_of_scope | SELL 행 → UNSUPPORTED_SCOPE 거부 | 문항 5 예외 ③ |
| test_invalid_rows_reported_per_line | 비정상 행(qty=0, 숫자 아님) → CSV_INVALID + 행 번호별 보고 | 문항 3 CSV 오류 처리 |
| test_happy_path_reproduces_stamped_report | 리포트 생성 + report-id 8d1a510771e6 재현(verification.md와 동일) + 4종 제목·무추천 고지 존재 | 문항 5 결정론 재현 |
| test_violating_options_rejected_and_no_report_written | 추천 어휘·근거 없는 숫자 → RANKING_LANGUAGE_DETECTED·UNGROUNDED_NUMBER, 리포트 파일 미생성 | 문항 5 예외 ② |
| test_ranking_field_in_schema_rejected | 순위 필드(rank) 주입 → SCHEMA_INVALID | 문항 3 "스키마에 순위 필드 없음" |

## 실행 방법

```bash
python3 -m unittest discover tests -v   # 의존성 설치 불요
```

## Coverage

- diagnose.py: 정상 1 + 예외 3 (REQUIRED_INPUT_MISSING / UNSUPPORTED_SCOPE / CSV_INVALID)
- render.py: 정상 1 + 예외 2 (denylist·접지 위반 / 스키마 순위 필드)
- 미커버: 이익 구간 세금(tax > 0) 케이스, 복수 종목 거부 — 필요 시 동일 패턴으로 추가

## Next Steps

- tests/는 submission.zip 범위(src/ + README.md + logs/) 밖 — 제출물 오염 없음
- 이익 구간(양도세 발생) 기대값 케이스 추가 시 세금 분기 커버 완성
