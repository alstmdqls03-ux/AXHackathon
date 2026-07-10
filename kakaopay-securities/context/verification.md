# verification.md — 직접 구동 검증 기록 (step-06, step-09 갱신)

> 실행 일시: 2026-07-09, 2026-07-10 (step-09 모델 턴은 `logs/codex/019f49a3-8c3c-7973-a155-f3800b0ca0a9.jsonl`에 저장됨). 문항 5는 이 문서 기반.

## 1. 심사자 절차 — 로컬 marketplace 등록·설치 ✅

```
codex plugin marketplace add <marketplace 루트>       # marketplace.json에 trade-decision-report 등록
→ Added marketplace `kakaopay-local`
codex plugin add trade-decision-report@kakaopay-local
→ Added plugin. Installed plugin root: ~/.codex/plugins/cache/kakaopay-local/trade-decision-report/0.1.0
codex plugin list
→ trade-decision-report@kakaopay-local  installed, enabled  0.1.0
```

- Codex CLI 0.142.5. marketplace 루트 구조: `.agents/plugins/marketplace.json` + `plugins/trade-decision-report/`(= `src/` 복사본).
- step-09 재확인(Codex CLI 0.144.1): README 구조 그대로 `/tmp/kp-step09-marketplace.slEwMw`를 만들고 `codex plugin marketplace add /tmp/kp-step09-marketplace.slEwMw` 실행 → 기존 `kakaopay-local`이 다른 경로로 이미 등록되어 `Error: marketplace 'kakaopay-local' is already added from a different source; remove it before adding this source` 반환. 이어서 `codex plugin add trade-decision-report@kakaopay-local` → `Added plugin ... Installed plugin root: /Users/seungbinmin/.codex/plugins/cache/kakaopay-local/trade-decision-report/0.1.0`, `codex plugin list` → `trade-decision-report@kakaopay-local  installed, enabled  0.1.0`.

## 2. 정상 시나리오 ✅ (설치 캐시본 = 심사자가 받게 되는 경로에서 실행)

입력: `samples/trades.csv`(TSLA BUY 2주 @$180 fee $0.25 fx 1350 / BUY 1주 @$150 fee $0.12 fx 1400) + `--price 160 --fx 1380`

```
cd ~/.codex/plugins/cache/kakaopay-local/trade-decision-report/0.1.0/skills/trade-decision-report
python3 scripts/diagnose.py samples/trades.csv --price 160 --fx 1380 --out /tmp/kp_diag.json   → 진단 완료
python3 scripts/render.py /tmp/kp_diag.json samples/options.sample.json --out /tmp/kp_report.md → 리포트 생성 (report-id: 8d1a510771e6)
```

출력 검증: 진단 7개 지표가 solution.md 기대값과 **전항 일치** — 명목 -5.88% / 실질(USD) -5.95% / 실질(KRW) -4.90% / 환율 효과 +1.05%p(달러 강세 방향 문구 포함) / 평가손익 -34,106원 / 전량 매도 시 -34,569원 / 세금 0원. **소스 트리 실행(step-05)과 설치 캐시본 실행의 report-id가 동일(8d1a510771e6) = 결정론 재현 확인.**

## 3. 예외 시나리오 ✅ (3종)

| # | 입력 | 결과 | 확인 |
|---|---|---|---|
| E1 | `--price` 누락 | `REQUIRED_INPUT_MISSING` + "현재 주가 없이는 손익을 계산할 수 없습니다"(되묻기 사유), exit 1 | 임의 추정값 미대입 |
| E2 | `samples/options_violation.json`(추천 어휘 "가장" + 숫자 리터럴 -40,000원 주입) | `RANKING_LANGUAGE_DETECTED` + `UNGROUNDED_NUMBER` 동시 검출, exit 1, **report 파일 미생성 확인** | 서열화 금지·근거 접지가 코드로 강제됨 |
| E3 | SELL 행 포함 CSV | `UNSUPPORTED_SCOPE`(데모 범위 안내), exit 1 | 범위 밖 정직 거부 |

(E1·E2는 step-05와 step-06 양쪽에서 실행 — E2·E3 상세 출력은 step-05 세션 기록 참조. 추가: `check_docs.py` 통과, `--chosen sell_all` 렌더 통과.)

## 4. Codex 모델 턴(대화형 스킬 구동) — ✅ step-09 완주

```
codex exec --skip-git-repo-check --sandbox workspace-write "trade-decision-report 스킬을 사용해줘. 테슬라 3주 들고 있는데 파란불이야. samples/trades.csv가 내 거래 내역이고 지금 160달러, 환율 1380원. 나 손해 본 거야? 지금 어떡해? 스킬 절차 그대로 diagnose → 선택지 JSON 작성 → render 파이프라인을 실행해 report.md 생성까지 완료하고, 최종 report.md 내용을 그대로 보여줘."
→ session id: 019f49a3-8c3c-7973-a155-f3800b0ca0a9
→ 진단 완료 → diagnosis.json
→ 리포트 생성 완료 → report.md (report-id: a33718a54909)
→ 생성 완료: report.md
```

- 실제 모델 턴은 설치 캐시의 `SKILL.md`를 읽고, 저장소의 `src/skills/trade-decision-report/samples/trades.csv`를 스킬 디렉터리 기준 입력으로 해석했다.
- 모델이 직접 실행한 파이프라인: `python3 scripts/diagnose.py samples/trades.csv --price 160 --fx 1380 --out diagnosis.json` → 진단 metrics 확인 → 모델 작성 `options.json` → `python3 scripts/render.py diagnosis.json options.json --out report.md`.
- 산출물 검증: `report.md`는 ①진단 ②선택지 비교 ③실행 체크리스트 3단 구조, 마지막 줄 `report-id: a33718a54909`, 진단 수치 명목 -5.88% / USD 실질 -5.95% / 원화 실질 -4.90% / 환율 효과 +1.05%p / 평가손익 -34,106원 / 전량 매도 시 -34,569원 / 세금 0원. 선택지 JSON은 숫자를 `{metrics.<id>}` 플레이스홀더로만 쓰고, `render.py`가 실존 metric evidence만 통과시켰다.
- 로그: Stop 훅이 발화해 `logs/codex/019f49a3-8c3c-7973-a155-f3800b0ca0a9.jsonl`(7,885 bytes)에 사용자 프롬프트, 중간 진행, 최종 report.md 출력이 저장됨. 훅 미발화 대체 복사는 수행하지 않음.

## 5. 수정 이력 (발견 → 수정 → 재검증)

1. 스펙 데모 수치의 환율 효과 방향 서술 반대("달러 약세"→**강세**, 평균 매수 환율 1,364.7 대비 현재 1,380) — step-04 산술 적대 검증에서 발견, 스펙·코드 모두 방향 분기 로직으로 반영.
2. 체크리스트 헤더 조사 오류("보유 지속를"→"보유 지속 선택 시") — step-05 정상 실행 출력 검토에서 발견, 수정 후 재렌더 확인.
3. LLM 서술 필드의 숫자 리터럴·추천 어휘 구멍 — step-04 강제력 적대 검증에서 발견, 플레이스홀더 치환·denylist로 봉합(§3-E2로 실증).
4. Codex 모델 턴 미검증 고지 — step-09에서 계정 재로그인 후 `codex exec` 실제 실행으로 해소, §4와 `logs/codex/`에 결과 기록.
