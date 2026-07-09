---
title: 'AI 심사 시뮬레이션 v1 수정 반영 (REVIEW-FIXES P0~P2)'
type: 'chore'
created: '2026-07-10'
status: 'done'
route: 'one-shot'
---

# AI 심사 시뮬레이션 v1 수정 반영 (REVIEW-FIXES P0~P2)

## Intent

**Problem:** AI 심사 시뮬레이션(95/100)이 남긴 수정 명세 `context/REVIEW-FIXES.md`의 P0~P2 — 로그 1차 증거 부재, 출처 없는 수치, 로그 미추적 일화, 코드-문서 불일치, 자수 여유 부족 — 가 미반영 상태였다.

**Approach:** P0(검증 재실행 + 명령·출력 원문을 대화 텍스트로 인용해 훅 로그에 남김), P1(문항 1 수치 완화, 문항 4 일화를 로그 실재 사례로 교체), P2(문항 5 정밀화, FAQ 빈 파일 문서 정정, 문항 3 자수 여유 확보)를 순서대로 적용하고 자수 재측정 + 회귀 테스트 7종으로 검증. 블라인드 리뷰 발견 5건 추가 패치(문항 3 정합 2건, 문항 4 Codex 병기, CARD_RE 무구분자, SKILL 마커 표기).

## Suggested Review Order

1. [question.md](../../question.md) — 문항 1·3·4·5 수정 + 자수표(674/677/996/731/796)
2. [README.md](../../README.md) — FAQ 빈 파일 처리 정정, 마스킹 4종 반영
3. [src/skills/resolution-lift/SKILL.md](../../src/skills/resolution-lift/SKILL.md) — 실패표 2행 정정
4. [src/scripts/load.py](../../src/scripts/load.py) — CARD_RE 무구분자 카드번호 커버
5. [tests/test_pipeline.py](../../tests/test_pipeline.py) — PII 테스트에 무구분자 카드 추가 (7/7 통과)
6. [deferred-work.md](deferred-work.md) — 이월 3건 (RRN 과잉 마스킹, 온보딩 플래그, 유선번호)
