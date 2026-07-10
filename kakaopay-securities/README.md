# trade-decision-report — 매매 의사결정 설득 리포트 (카카오페이증권 예선 제출물)

초보 투자자가 보유 종목을 두고 "나 손해 본 거야? 지금 어떡해?"라고 물을 때, **결정론 계산으로 실질 손익을 진단하고, 순위 없는 선택지 비교와 실행 체크리스트를 고정 템플릿 리포트로 제공**하는 Codex 플러그인. 이 플러그인이 주는 것은 **정답이 아니라 납득 과정**이다 — 추천·예측을 하지 않으며 결정은 항상 사용자의 몫으로 남긴다.

## 개요

- **누가·언제**: 초보 투자자가 평가손실(또는 수익) 상태의 보유 종목 앞에서 다음 행동을 정하지 못할 때.
- **무엇을**: 거래 내역 CSV + 현재가·환율 → [① 진단(실질 손익의 실체) → ② 선택지 4종 병렬 비교(보유/부분 매도/분할 추가 매수/전량 매도) → ③ 선택한 행동의 실행 체크리스트]를 담은 `report.md`.
- **설계 원칙**: 리포트의 모든 숫자는 결정론 스크립트의 산출물이고, 리포트는 순위를 매길 수 없는 구조로 강제된다(아래 "작동 방식"). 이는 금융 AI의 보조수단 원칙(최종 판단은 사람)과 정합한다.

## 설치·실행 (심사자용)

플러그인 등록 없이 스크립트만으로도 전체 검증이 가능하다(아래 3). Codex에서 스킬로 쓰려면 1–2.

1. marketplace 루트 폴더를 만들고 이 zip의 `src/` 내용을 복사 (아래 구조·내용 그대로 — Codex CLI 0.142.5에서 검증):
   ```
   <marketplace-root>/
   ├── plugins/trade-decision-report/     ← src/ 내용 복사 (.codex-plugin/plugin.json 포함)
   └── .agents/plugins/marketplace.json   ← 아래 내용
   ```
   ```json
   {
     "name": "kakaopay-local",
     "plugins": [
       { "name": "trade-decision-report", "source": "./plugins/trade-decision-report" }
     ]
   }
   ```
2. 등록·설치·확인 (검증된 명령 원문):
   ```bash
   codex plugin marketplace add <marketplace-root>        # → Added marketplace `kakaopay-local`
   codex plugin add trade-decision-report@kakaopay-local  # → Added plugin (Installed plugin root: ~/.codex/plugins/cache/…)
   codex plugin list                                      # → trade-decision-report@kakaopay-local  installed, enabled  0.1.0
   ```
   프롬프트 예: *"테슬라 3주 들고 있는데 파란불이야. samples/trades.csv가 내 거래 내역이고 지금 160달러, 환율 1380원. 나 손해 본 거야? 지금 어떡해?"*
3. **스크립트 직접 실행** (Python 3 표준 라이브러리만, 외부 의존성 0):
   ```bash
   cd src/skills/trade-decision-report
   python3 scripts/diagnose.py samples/trades.csv --price 160 --fx 1380 --out samples/diagnosis.json
   python3 scripts/render.py samples/diagnosis.json samples/options.sample.json --out samples/report.md
   cat samples/report.md
   ```
4. **(선택) 국내 투자자 매매동향 맥락 추가** — `--flows`로 매매동향 CSV(헤더 `date,buy_usd,sell_usd`)를 주면 metrics에 `flow_*` 6종이 추가되고, 리포트 ① 진단 안에 렌더러 하드코딩 서브섹션(기간·매수·매도·순매수 표 + 비신호 고지)이 들어간다. LLM은 이 섹션에 한 글자도 쓰지 않는다:
   ```bash
   python3 scripts/diagnose.py samples/trades.csv --price 160 --fx 1380 --flows samples/flows.csv --out samples/diagnosis_flows.json
   python3 scripts/render.py samples/diagnosis_flows.json samples/options.sample.json --out samples/report_flows.md
   ```
   (출력은 `samples/`의 동봉 골든 파일을 재생성한다 — 결정론이라 byte-identical, zip 루트에 새 파일이 생기지 않는다.)
   데이터 출처: **한국예탁결제원 증권정보포털 SEIBro** (https://seibro.or.kr — 종목별내역(주식TOP50) 화면 딥링크: https://seibro.or.kr/websquare/control.jsp?w2xPath=%2FIPORTAL%2Fuser%2FovsSec%2FBIP_CNTS10013V.xml&menuNo=921, 둘 다 로그인 없이 접근 가능·2026-07-10 HTTP 200 확인) — 경로: 국제거래 > 외화증권예탁결제 > 종목별내역(주식 TOP50), 종목별 매수·매도 결제금액(USD) 공개. `samples/flows.csv`는 형식 예시용 **합성 데이터**이며, 실제 데이터는 위 경로에서 내려받아 같은 헤더로 저장해 쓴다(UTF-8, 엑셀 BOM 허용).

## 작동 방식 (문항 3과 동일)

**절차** — 3단계 파이프라인, LLM의 작문 구간은 2단계 하나뿐:

1. **진단** `scripts/diagnose.py`: 거래 내역 CSV(+현재가·환율)에서 실질 손익을 결정론 계산 — 명목 vs 실질 수익률(매수 수수료·환율 반영), 환율 효과 분해, 전량 매도 시 확정 손익·양도세(단순화). 원화는 half-away-from-zero 반올림. 시세·뉴스 조회 없음(모든 수치는 입력에서 유도).
2. **선택지 작성** (LLM): 진단 metrics를 보고 4개 선택지의 [일어나는 일/근거/확정되는 것/알 수 없는 것]를 JSON으로 작성.
3. **검증·조립** `scripts/render.py`: 스키마 검증 후 고정 템플릿 마크다운을 조립, `report.md`로 저장(마지막 줄에 입력 해시 기반 report-id 스탬프 — 유효 산출물의 정의).

**판단 기준을 코드로 강제** (프롬프트 권고가 아님):

| 제약 | 강제 구조 |
|---|---|
| 순위·추천 불가 | 선택지 id는 enum 4종 고정(제목은 렌더러 하드코딩), 순위·점수 필드 자체가 스키마에 없음, 가나다순 강제 정렬, 추천·비교·예측 어휘 denylist(`RANKING_LANGUAGE_DETECTED`), 필드당 200자 제한 |
| 모든 숫자 = 계산 산출물 | 근거 필드는 실존 `metrics.<id>` 참조만(`EVIDENCE_NOT_GROUNDED`), 서술 속 숫자는 `{metrics.<id>}` 플레이스홀더만 — 숫자 리터럴은 `UNGROUNDED_NUMBER`로 거부 |
| 고정 3단 템플릿 | 최종 마크다운은 render.py만 생성, 경고 문구("순위·추천을 제시하지 않는다" 등) 하드코딩, report-id 스탬프 |

**정보가 부족하거나 잘 안 풀리는 상황**:

- 현재가·환율 미제공 → `REQUIRED_INPUT_MISSING`: 어떤 값이 왜 필요한지 출력하고 되묻는다. **임의 추정값 대입 금지.**
- CSV 오류 → `CSV_INVALID`: 행 번호별 오류 목록.
- SELL 내역·복수 종목·주식 외 자산 → `UNSUPPORTED_SCOPE`: 데모 범위(단일 종목·미국 주식·BUY 내역)를 안내.
- LLM 산출물이 규칙 위반 → 3종 거부 코드와 함께 리포트 미생성, 수정 후 재시도(위반은 사용자에게도 공개).
- 의도 모호 → 질문 1개로 구체화. 추천 요구 → 순위를 제시하지 않는 이유를 설명하고 판단 재료를 안내.

**한계(정직 고지)**: 세금은 단순화 계산(연 250만 원 기본공제 초과분 22%, 손익통산·환차익 미반영). denylist는 완전하지 않으나 거부→재작성 루프로 동작 — 특히 매매동향(`flow_*`) 수치를 선택지 서술에 동조 프레임("함께 사는" 등)으로 끌어오는 표현은 어휘 필터만으로 다 막지 못하므로, SKILL.md가 LLM에 사실 서술 전용을 지시하고 렌더러 고지가 신호 해석을 차단하는 이중 방어를 쓴다. 이 플러그인은 투자 자문이 아니다.

## 검증 (이 폴더 세션에서 실제 실행 — 로그와 정합)

- **정상**: 위 "설치·실행 3" 명령 → `report.md` 생성, 진단 수치 예: 명목 -5.88% → USD 실질 -5.95%(매수 수수료 반영) → 원화 실질 -4.90%(환율 효과 +1.05%p), 전량 매도 시 -34,569원 확정, report-id 스탬프 포함.
- **예외 1 (입력 누락)**: `python3 scripts/diagnose.py samples/trades.csv --fx 1380` → `REQUIRED_INPUT_MISSING` (price가 왜 필요한지 포함), exit 1.
- **예외 2 (규칙 위반 주입)**: `python3 scripts/render.py samples/diagnosis.json samples/options_violation.json` → `RANKING_LANGUAGE_DETECTED`("가장") + `UNGROUNDED_NUMBER`(-40,000원) 검출, 리포트 미생성, exit 1.
- **예외 3 (범위 외)**: SELL 행 포함 CSV → `UNSUPPORTED_SCOPE`, exit 1.
- **정상 (매매동향)**: 위 "설치·실행 4" 명령(`--flows samples/flows.csv`) → metrics에 `flow_*` 6종 추가(매수 $500,000,000.00 / 매도 $460,000,000.00 / 순매수 $40,000,000.00, 2026-06-30 ~ 2026-07-06 자료 5일치), 리포트 ① 안에 "국내 투자자 매매동향" 표 + 비신호 고지 — 동봉 골든 `samples/report_flows.md`와 byte-identical. `--flows` 미제공 시 산출물은 기존과 byte-identical(report-id `8d1a510771e6` 불변, 테스트가 골든 대조로 실증).
- **예외 4 (매매동향 행 오류)**: 날짜 형식 위반·음수 금액·숫자 아님 행 포함 flows CSV → `CSV_INVALID` + 행 번호별 오류 목록(메시지에 flows 파일 명시), 리포트 미생성, exit 1.
- 문서 규율 자가 검사: `python3 scripts/check_docs.py <폴더>` — 공백 주장 (추정) 표기·납득 프레임 문구 확인. `<폴더>`는 zip 루트(이 README.md가 있는 위치).
- 자동 테스트(E2E 11건, 표준 라이브러리만): zip 루트에서 `python3 -m unittest discover src/tests -v` — 정상 1 + 예외 3 + 스키마·denylist·비객체 JSON 거부 경로 + 매매동향(flows) 정상·하위호환·예외 3건.
