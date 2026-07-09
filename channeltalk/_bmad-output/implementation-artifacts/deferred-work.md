# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-review-fixes-v1.md`
  summary: RRN_RE가 13자리 연속 숫자(주문·운송장번호)를 주민번호로 과잉 마스킹할 수 있음.
  evidence: 프라이버시 우선(과잉 마스킹 > 유출)으로 의도한 트레이드오프 — 실데이터에서 오탐 보고 시 체크섬 검증 추가.

- source_spec: `_bmad-output/implementation-artifacts/spec-review-fixes-v1.md`
  summary: faq_count=0(온보딩 모드)일 때 load.py가 경고·플래그를 내지 않아 '보고에 명시'가 SKILL.md 지시에만 의존.
  evidence: resolved_inferred는 플래그+경고 이중 장치가 있는 것과 비대칭 — summary에 onboarding 플래그 추가가 대칭적 개선.

- source_spec: `_bmad-output/implementation-artifacts/spec-review-fixes-v1.md`
  summary: PHONE_RE가 휴대폰(01x)만 마스킹, 유선(02/031)·국제표기(+82)는 미탐.
  evidence: 블라인드 리뷰 지적 — 유선 패턴은 일반 숫자 오탐 위험이 높아 보수적으로 제외한 상태.
