---
title: '투자자 매매동향 맥락 섹션 (flows 입력)'
type: 'feature'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 0
baseline_commit: '49e920c'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** 리포트가 "나"의 손익만 진단하고, 사용자가 궁금해하는 "다른 투자자들은 이 종목을 언제·얼마나 사고팔았나"라는 맥락(기관·매매동향류 질문)을 담지 못한다. 데모 범위가 미국 주식이므로 KRX 기관/외인 데이터는 부정합하고, 예탁결제원 SEIBro가 공개하는 **외화증권 종목별 매수·매도 결제금액**(국내 투자자 집계, USD)이 정합하는 공개 데이터다.

**Approach:** 선택 입력 `--flows flows.csv`(공개 데이터를 사용자가 내려받아 제공)를 diagnose.py가 결정론 집계해 `flow_*` metrics로 추가하고, render.py가 ① 진단 안에 **렌더러 하드코딩 서브섹션** "국내 투자자 매매동향"을 표+비신호 고지로 조립한다. LLM 작문 구간·외부 조회·신규 의존성 없음.

## Boundaries & Constraints

**Always:**
- 표준 라이브러리만, Python 3.9 호환(f-string 안 따옴표 중첩 금지 — 과거 P0).
- flows 미제공 시 기존 산출물과 **byte-identical** (sample report-id `8d1a510771e6` 불변, 기존 테스트 7건 무수정 통과).
- 모든 수치는 입력에서 결정론 유도(hafz 반올림), 새 섹션은 render.py 고정 템플릿만 — LLM은 새 섹션에 한 글자도 쓰지 않는다.
- 서브섹션에 하드코딩 고지: 과거 집계 사실이며 매수·매도 신호가 아니라는 문장.
- 3단 구조(①진단 ②선택지 ③체크리스트) 유지 — 새 내용은 ① 내부 서브섹션.
- README의 SEIBro 출처 URL은 로그인 없이 접근됨을 실제 확인 후 기재.

**Ask First:**
- 새 최상위 리포트 섹션 추가, 기존 metric id·report-id 산출 방식 변경, 의존성 추가.

**Never:**
- 외부 네트워크 조회, OpenAI 등 제2 LLM 연동, 추천·순위·신호 표현, flows 필수화, KR 종목용 기관/외인 분해(데모는 미국 주식).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| flows 정상 | `--flows samples/flows.csv` (헤더 `date,buy_usd,sell_usd`) | diagnosis.json metrics에 `flow_days, flow_from_date, flow_to_date, flow_buy_usd, flow_sell_usd, flow_net_buy_usd` 추가; report ① 안에 매매동향 표+고지 | N/A |
| flows 미제공 | `--flows` 없음 | metrics·report 기존과 byte-identical, 서브섹션 없음 | N/A |
| flows 행 오류 | 숫자 아님·음수 금액·날짜 형식(YYYY-MM-DD) 위반·중복 날짜 | 리포트 미생성 | `CSV_INVALID` + 행 번호별 오류 목록 (파일명 명시) |
| flows 빈 파일/헤더 불일치 | 행 0건 또는 다른 헤더 | 리포트 미생성 | `CSV_INVALID` |
| LLM이 flow metric 인용 | `evidence: ["metrics.flow_net_buy_usd"]` 또는 `{metrics.flow_net_buy_usd}` | 기존 검증 그대로 통과(실존 id), 숫자 리터럴은 기존대로 거부 | 기존 코드 재사용 |

</frozen-after-approval>

## Code Map

(경로는 `src/skills/trade-decision-report/` 기준)
- `scripts/diagnose.py` — CLI·CSV 검증·metrics 산출. `fail()`/행 검증 패턴 재사용해 `--flows` 추가.
- `scripts/render.py` — `build_report()`가 ① 진단 표 조립. `fmt()`의 `_usd` 접미사 자동 포맷 덕에 명명만 맞추면 포맷 코드 무수정.
- `SKILL.md`, `samples/`, `../../tests/test_pipeline.py`(블랙박스 CLI unittest), 루트 `README.md`.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/diagnose.py` — `--flows` 옵션 + `read_flows()`: 헤더 `date,buy_usd,sell_usd`, 행별 오류 수집(숫자·≥0·ISO 날짜·중복 날짜), 집계 metrics 6종(`flow_days`, `flow_from_date`, `flow_to_date`, `flow_buy_usd`, `flow_sell_usd`, `flow_net_buy_usd` — 금액 hafz 2자리)을 기존 dict 뒤에 추가. 미제공 시 무변경.
- [x] `scripts/render.py` — `flow_days` 존재 시 ① 말미에 `### 국내 투자자 매매동향 (입력 데이터 기준)` 표(기간·매수·매도·순매수)+고지 블록쿼트. 부재 시 출력 무변경.
- [x] `samples/flows.csv` — 합성 5행 신규(형식 예시).
- [x] `SKILL.md` — 입력 (d) 선택 항목, 실패 표 flows 행, 한계 1줄.
- [x] `README.md` — `--flows` 사용 예, SEIBro 출처 URL(접근 확인 후), 검증 시퀀스에 flows 정상·예외 1건씩.
- [x] `src/tests/test_pipeline.py` — 3건: ①flows 정상(손계산 기대값 전항 일치+서브섹션·고지 존재) ②미제공 시 report-id 불변 ③오류 행 `CSV_INVALID`+행 번호.

**Acceptance Criteria:**
- Given flows 미제공, when 기존 README 검증 시퀀스 전체 실행, then 기존 테스트 7건+신규 3건 통과하고 sample report-id `8d1a510771e6` 불변.
- Given `samples/flows.csv` 제공, when diagnose→render 완주, then 리포트는 3단 구조를 유지한 채 ① 안에 매매동향 표와 비신호 고지를 포함하고 모든 수치가 metrics 산출물이다.
- Given 추천 어휘·숫자 리터럴이 포함된 options, when render, then 기존과 동일하게 거부되고 리포트 미생성(회귀 없음).
- Given `/usr/bin/python3`(3.9.6), when 전체 테스트 실행, then 전부 통과.

## Spec Change Log

## Verification

**Commands:**
- `python3 -m unittest discover src/tests -v` — expected: 10건 전부 OK (`/usr/bin/python3` 3.9.6에서도 동일)
- `diagnose.py samples/trades.csv --price 160 --fx 1380` 출력 — expected: `samples/diagnosis.json`과 byte-identical
- 같은 명령 + `--flows samples/flows.csv` → render — expected: `flow_*` 6종 포함 JSON, 리포트에 매매동향 서브섹션+고지+report-id 스탬프

## Suggested Review Order

**진입점 — 리포트에 실제로 나가는 것**

- 조건부 서브섹션: LLM이 한 글자도 안 쓰는 고정 템플릿 + 비신호 고지 하드코딩
  [`render.py:154`](../../src/skills/trade-decision-report/scripts/render.py#L154)

**flows 입력 검증 (diagnose.py)**

- 검증 본체: BOM 허용, list 헤더 비교(중복 열 거부), 실존 날짜, isfinite, 필드별 오류 수집
  [`diagnose.py:86`](../../src/skills/trade-decision-report/scripts/diagnose.py#L86)

- 하위 호환의 스위치: 미제공 시 metrics 무변경, 빈 문자열은 조용히 무시하지 않음
  [`diagnose.py:216`](../../src/skills/trade-decision-report/scripts/diagnose.py#L216)

**렌더 방어·표기**

- 손편집 진단 JSON의 불완전 flow 세트 → JSON 오류 계약 유지
  [`render.py:205`](../../src/skills/trade-decision-report/scripts/render.py#L205)

- 최초의 음수 가능 _usd: "-$X" 표기 (기존 양수 출력엔 영향 없음)
  [`render.py:123`](../../src/skills/trade-decision-report/scripts/render.py#L123)

**신호 누출 이중 방어 (리뷰에서 나온 핵심 리스크)**

- denylist가 못 잡는 동조 프레임을 LLM 지침으로 차단
  [`SKILL.md:54`](../../src/skills/trade-decision-report/SKILL.md#L54)

- 한계 정직 고지: 어휘 필터+지침+렌더러 고지의 이중 방어 명시
  [`README.md:74`](../../README.md#L74)

**주변부 — 출처·샘플·테스트**

- SEIBro 딥링크 포함 공개 출처 (오늘 HTTP 200 확인)
  [`README.md:49`](../../README.md#L49)

- 3건 추가: 골든 byte 대조로 하위 호환 실증, 행 오류 3종 개별 보고 검증
  [`test_pipeline.py:58`](../../src/tests/test_pipeline.py#L58)
