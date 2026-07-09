# verification.md — 직접 구동 검증 기록 (step-06)

> 실행 일시: 2026-07-09 (전 명령은 이 폴더의 Claude Code 세션에서 실행 — `logs/claude-code/a75e0fe7-….jsonl`에 기록됨). 문항 5는 이 문서 기반.

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

## 4. Codex 모델 턴(대화형 스킬 구동) — ⚠️ 외부 요인으로 차단

```
codex exec --skip-git-repo-check --sandbox workspace-write "trade-decision-report 스킬을 사용해줘. …"
→ ERROR: You've hit your usage limit. … or try again at Aug 4th, 2026 5:50 PM.
```

- 원인: 이 계정의 ChatGPT 플랜 사용량 한도(2026-08-04 리셋) — **플러그인 결함이 아니라 실행 환경의 쿼터 문제.** API 키 인증 없음, ollama 로컬 모델 미보유(대용량 다운로드는 보류).
- 커버된 것: 등록→설치→활성화(§1) + 스킬의 전체 실행 경로(진단→검증→렌더)를 설치본에서 정상·예외 모두 완주(§2·§3). SKILL.md는 이 스크립트 호출 절차의 지시문이므로, 모델 턴에서 추가되는 것은 자연어 파싱과 options.json 작문뿐이며 그 산출물이 규칙을 어기면 §3-E2가 보여주듯 렌더러가 거부한다.
- 남은 리스크와 계획: 심사 환경(쿼터 정상)에서는 재현되지 않을 문제로 판단(추정). 마감 전 쿼터 복구·대체 계정·로컬 모델 확보 시 모델 턴 검증을 추가하고 이 문서를 갱신한다.

## 5. 수정 이력 (발견 → 수정 → 재검증)

1. 스펙 데모 수치의 환율 효과 방향 서술 반대("달러 약세"→**강세**, 평균 매수 환율 1,364.7 대비 현재 1,380) — step-04 산술 적대 검증에서 발견, 스펙·코드 모두 방향 분기 로직으로 반영.
2. 체크리스트 헤더 조사 오류("보유 지속를"→"보유 지속 선택 시") — step-05 정상 실행 출력 검토에서 발견, 수정 후 재렌더 확인.
3. LLM 서술 필드의 숫자 리터럴·추천 어휘 구멍 — step-04 강제력 적대 검증에서 발견, 플레이스홀더 치환·denylist로 봉합(§3-E2로 실증).
