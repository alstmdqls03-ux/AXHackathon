# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-trading-flow-context.md`
  summary: read_trades()도 read_flows()와 같은 강화 필요 — utf-8-sig(BOM), 헤더 list 비교(중복 열), OSError/UnicodeDecodeError/csv.Error 광역 catch.
  evidence: 리뷰에서 flows 경로에 대해 재현·수정된 동일 결함 3종이 read_trades에 그대로 존재(기존 코드, 이번 스토리가 만든 것 아님). trades.csv는 스킬이 대신 만들어 주는 경로라 실사용 빈도는 낮음.

- source_spec: `_bmad-output/implementation-artifacts/spec-trading-flow-context.md`
  summary: 기존 테스트 2건(test_sell_row_rejected, test_invalid_rows_reported_per_line)의 NamedTemporaryFile(delete=False) 임시 파일 미정리.
  evidence: 리뷰 지적 — 실행마다 temp CSV가 누적. 신규 flows 테스트는 TemporaryDirectory로 수정 완료, 기존 2건은 이번 diff 범위 밖.
