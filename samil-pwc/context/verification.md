# verification.md — 직접 구동 검증 기록 (step-06)

> 실행 일시: 2026-07-09 23:14~23:40 (이 폴더 세션 — 실행 기록은 `logs/claude-code/3dd43331-….jsonl` 및 `logs/codex/rollout-2026-07-09T23-38-49-….jsonl`에 원본 그대로 존재)

## A. 심사자 절차 재현 (README 그대로)

| 단계 | 명령 | 결과 |
|---|---|---|
| 1. marketplace 구성 | `mkdir …/haenggan-marketplace/{plugins,.agents/plugins}` + `cp -r src → plugins/haenggan-audit` + marketplace.json 작성 | ✅ |
| 2. 등록 | `codex plugin marketplace add ./haenggan-marketplace` | ✅ "Added marketplace `samil-local-plugins`" |
| 3. 설치 | `codex plugin add haenggan-audit@samil-local-plugins` | ✅ "Added plugin `haenggan-audit`" — `codex plugin list`: **installed, enabled 1.0.0** |
| 4. 실행 | `codex exec -s workspace-write "haenggan-audit 스킬을 사용해서 src/skills/haenggan-audit/data/demo 의 결산 데이터를 행간 감사하고, 보고서를 context/demo-report-normal.md 로 저장해줘."` | ⚠️ 부분 성공 (아래) |

- 발견·수정 1: 최초 README의 설치 명령이 `codex plugin add haenggan-audit`이었음 → CLI가 `<plugin>@<marketplace>` 형식 요구 → **README를 검증된 명령으로 교정**.
- 4단계 상세: Codex가 **스킬을 정상 인식·트리거**하고 SKILL.md 절차를 그대로 추적함 — 계획 로그: "① 데이터 파일·헤더 인벤토리 확인 ✓ → ② 체커와 가설 모듈 기준 로드 → ③ 후보 산출 및 원본 대조 → ④ 보고서 작성 및 수치 검산" (SKILL.md 실행 절차 1~7단계와 일치). 이후 **OpenAI 계정 사용 한도 초과**("You've hit your usage limit… try again at Aug 4th")로 보고서 생성 전 중단 (22,212 tokens 사용). — **플러그인 결함이 아니라 실행 환경(계정 쿼터) 제약**. 세션 원본: `logs/codex/rollout-…jsonl`.

**검증된 것**: 플러그인 규격(매니페스트·marketplace 등록·설치·활성화) + 스킬 트리거 + 절차 준수 개시.
**검증 못 한 것(잔여 리스크)**: Codex가 끝까지 생성한 report.md의 품질 — 계정 쿼터 확보 후 동일 명령 재실행 필요 (프롬프트·절차는 위와 동일).

## B. 결정론 체커 검증 (스킬의 계산 계층 — 동일 세션 로그에 실존)

### B-1. 정상 시나리오

- 입력: `python3 scripts/checks.py data/demo --out findings_normal.json`
- 출력: **이상 후보 19건**, 심은 신호 3종 전부 검출 —
  - H1: `H1-CAP-4712`(수선성 적요의 자산 계상, high) + `H1-PE-4712/4713`(기말 대형) + `H1-SA-4712/4713`(작성자=승인자) + `H1-YOY-505`(수선비 -78%) → 전표 #4712 사건으로 수렴
  - H2: `H2-DIV`(흑자 속 영업CF 음수 3개월 연속) + `H2-DSO`(49→87일, 1.8배) + `H2-SPK-2025-12`(분기말 스파이크 1.84배) + `H2-CONC`(대한상사 편중 46%, 61일+ 연체 42%)
  - H3: `H3-ALLOC-B`(마진 +12.0% → 기계시간 재배부 시 -3.0%, **부호 반전**, high) — 제품 A는 임계값 미달로 미발화(설계 의도)
- 오탐 후보(정기 감가상각 분개 #4850/4851, 12월 매출 인식 #4800/4801, 매입채무·미지급금 YoY 등)도 후보에 포함됨 — **에이전트 기각 단계의 입력으로 의도된 동작** (가설 모듈의 기각 조건 대상).

### B-2. 예외 시나리오 (정보 부족)

- 입력: `monthly_series.csv`를 제거한 사본 폴더로 동일 실행
- 출력: `[checks] H2(현금흐름 이상) 건너뜀 — 필수 파일 부재: monthly_series.csv` + H1 후보 14건·H3 후보 1건 정상 산출 + **exit 0** → 가설군 모듈 독립성·부분 실패 동작 확인.

### B-3. 빌드 무결성

- `plugin.json` JSON 파싱 + 필수 필드(name/version/description) 확인 ✅
- `checks.py` 문법 검사(py_compile) ✅, 외부 의존성 0 (표준 라이브러리만) ✅
- 데모 데이터 시트 간 정합(차대 균형 77,340 / 간접비 합 4,200 / 월매출 합 48,000 / 채권연령 합 13,500) — 설계 단계에서 수기 검산, 체커 `tb_arithmetic`·`tb_balance` 무발화로 교차 확인 ✅

## C. 로그 정합 (문항 5 대응)

- 위 A·B의 모든 명령·출력은 이 세션 로그(`logs/claude-code/3dd43331-….jsonl`)에 훅으로 자동 기록됨.
- Codex 구동 세션은 에러 중단으로 Stop 훅 미발화 → **원본 rollout 파일을 무편집 복사**로 `logs/codex/`에 포함 (byte-identical 확인 `cmp` 통과). 규정상 "훅 미적용 대화는 원본 그대로 텍스트로 logs/에" 요건 준수.

## D. zip 드라이런 + 체크리스트 (2026-07-09 23:44)

- `zip -r submission-dryrun.zip src README.md logs` (스크래치에 생성) → 루트 구성 `src/`·`README.md`·`logs/`만 ✅, 30개 파일, **82KB ≤ 100MB** ✅, `__pycache__`·`.DS_Store` 0개 ✅.
- WORKFLOW 체크리스트: plugin.json 필수 필드 ✅ / README=설치·실행+문항3 일치 ✅ / question.md 자수(544·619·940·717·766) ✅ / 문항 2 출처 URL 6건 접근성(2026-07-09 curl 전건 200, step-02 대장 검증분) ✅ / logs/ 원본 그대로(훅 산출물 무수정 + rollout 무편집 복사) ✅.
- **발견·보고 2 (드라이런이 잡음)**: 훅(save_log.py)이 **셸 cwd 기준** `logs/`에 저장하는 구조라, step-05~06 사이 셸 cwd가 스킬 폴더였던 턴에 `src/skills/haenggan-audit/logs/claude-code/<세션id>.jsonl` **스테일 스냅샷이 생성됨**. 로그 불가침 규칙(위치 무관 수정·삭제 금지)에 따라 **본 세션에서는 건드리지 않음**. 완전한 최종 로그는 세션 종료 시 루트 `logs/claude-code/`에 저장됨(훅이 매 턴 전체 전사를 다시 씀 — save_log.py 코드로 확인). → **zip 생성 전 처리(이동/포함 여부)는 사용자 결정 사항**으로 이관. 재발 방지: 이후 셸 cwd를 회사 폴더 루트로 고정.
