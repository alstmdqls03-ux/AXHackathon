# resolution-lift — AI 상담 해결률 개선 파이프라인 (채널톡 과제)

미해결 상담 로그를 넣으면 **지식 갭 진단 → FAQ·규칙 초안 → 재시뮬레이션 검증 리포트**까지, CX 담당자가 수 주에 걸쳐 하던 'AI 상담 해결률 개선 컨설팅 1사이클'을 한 번의 실행으로 완주하는 Codex 플러그인입니다.

**누가, 언제 쓰나**: 채널톡 ALF 같은 AI 상담 에이전트를 도입한 이커머스 CX 담당자(그리고 수천 고객사를 지원하는 AX 컨설턴트)가, AI가 못 푼 상담이 쌓였을 때 씁니다. 공개된 최고 사례(해결률 80%)에서도 최소 20%는 미해결로 남고, AI 상담은 등록된 지식 기반으로만 답하기 때문에 해결률의 레버는 지식 보강뿐인데 — 그 사이클(로그 읽기→갭 찾기→FAQ 쓰기→검증)이 전부 수작업이기 때문입니다.

## 설치 (심사자용)

요구 사항: Codex CLI + Python 3.9+ (macOS 기본 `/usr/bin/python3` 3.9.6에서 컴파일·실행 검증. 외부 패키지·네트워크·API 키 **불필요**)

**방법 A — 로컬 marketplace 등록 (검증 완료 절차, Codex CLI 0.142 기준)**

```bash
# 1) 아무 위치에 마켓플레이스 디렉터리 구성
mkdir -p my-marketplace/resolution-lift my-marketplace/.agents/plugins
cp -R <압축 해제 경로>/src/. my-marketplace/resolution-lift/

# 2) 매니페스트 작성 — 위치가 정확히 .agents/plugins/marketplace.json 이어야 함
cat > my-marketplace/.agents/plugins/marketplace.json <<'EOF'
{ "name": "ax-local",
  "plugins": [ { "name": "resolution-lift", "source": "./resolution-lift",
                 "description": "AI 상담 해결률 개선 파이프라인" } ] }
EOF

# 3) 등록·설치
codex plugin marketplace add "$(pwd)/my-marketplace"
codex plugin add resolution-lift@ax-local
# 이름 충돌(ax-local이 이미 등록됨) 시: codex plugin marketplace remove ax-local 후 재시도
```

(참고: OpenAI 플러그인 문서 https://developers.openai.com/codex/plugins — 루트 `marketplace.json`은 인식되지 않고 `.agents/plugins/marketplace.json`만 지원됨을 실행으로 확인)

**방법 B — 폴백 (marketplace 없이 확인)**
플러그인 등록 환경이 어긋나도 동작 검증이 가능합니다: Codex 세션에서
`src/skills/resolution-lift/SKILL.md 를 읽고, src/examples/tickets.csv 와 src/examples/faq.csv 로 파이프라인을 실행해줘`
라고 요청하면 동일하게 작동합니다 (스킬 본문이 전체 절차를 지시).

## 사용법

Codex에 이렇게 요청합니다:

```
상담 로그로 해결률 개선 사이클 돌려줘.
tickets: src/examples/tickets.csv / faq: src/examples/faq.csv
```

자기 데이터로 쓰려면 같은 형식의 CSV 두 개를 주면 됩니다 (`tickets.csv`: ticket_id, question, [alf_answer, resolved, agent_answer] / `faq.csv`: question, answer).

## 작동 방식

분업 원칙: **세는 일(집계·검증·리포트)은 스크립트가, 생각하는 일(분류·초안·채점)은 LLM이, 정책 결정은 사람이** 합니다. LLM의 판단 기준은 전부 `SKILL.md`에 명문화되어 있습니다.

| 단계 | 담당 | 하는 일 |
|---|---|---|
| 1 적재·검증 | `scripts/load.py` (결정적) | 스키마 검증(불일치 시 템플릿 안내 후 중단), 전화·이메일·주민번호·카드번호 마스킹, 해결/미해결 분리, 기준 해결률 집계 |
| 2 갭 분류 | LLM (SKILL.md 기준) | 미해결 티켓을 클러스터로 묶고 유형 판정: **A 지식 부재 / B 지식 불명확 / C 정책 결정 필요 / D 태스크 필요 / REVIEW 사람 검토** + confidence + 근거 티켓 |
| 3 초안 생성 | LLM | A·B 갭에만 FAQ 초안(질문 변형 3 + 답변). 1차 근거는 상담사 실답변. 근거 없으면 `[정책 확인 필요]` 마커 — 정책을 지어내지 않음 |
| 4 재시뮬레이션 | LLM 채점 → `scripts/simulate.py` (결정적) | "초안이 등록됐다면 해결됐을까"를 전건 채점 → 스크립트가 스키마·환각 ID·전건 커버를 검증하고 리포트 4종 생성 |

**출력물**: `gap-report.md`(갭 클러스터×유형×근거), `faq-draft.md`(등록용 초안 + 정책 확인 목록), `validation-report.md`(before/after 해결률과 티켓별 판정), `report.html`(요약 대시보드).

**판단이 데이터를 넘어서지 못하게 하는 장치**: 갭 주장에는 실제 티켓 근거가 필수(환각 ID는 simulate.py가 차단), 확신 없는 판정은 REVIEW로 강등, 근거 없는 답변은 자동 등록이 보류되며, '부분' 판정은 보수적으로 미해결로 집계합니다.

## 정보가 부족하거나 잘 안 풀리는 상황에서의 동작

| 상황 | 동작 |
|---|---|
| 파일 없음 / 필수 컬럼 누락 | load.py가 필요한 컬럼과 CSV 템플릿을 출력하고 중단 — 짐작으로 진행하지 않음 |
| `resolved` 컬럼 없음 | 상담사 답변 존재 여부로 미해결을 추정하되, 모든 리포트에 (추정) 표기 |
| 기존 FAQ가 비어 있음 | FAQ 파일은 헤더(question,answer) 필수 — 헤더 없으면 템플릿 안내 후 중단. 헤더만 있고 내용 0건이면 온보딩 모드로 전량 '지식 부재' 기준 진행, 보고에 명시 |
| 갭 판정 확신 없음 / 상담사 답변 모순 | REVIEW(사람 검토)로 분류, 초안 생성 안 함 |
| 답변 근거 없음 | `[정책 확인 필요]` 마커로 등록 보류 |
| 시뮬레이션 개선 0 | 그대로 보고 + 갭 유형 분포에서 원인 가설 제시 |
| 미해결 200건 초과 | 50건 배치 분할, 그 사실을 보고에 명시 |
| 로그 내 개인정보 | 적재 단계에서 자동 마스킹(건수 리포트) |

## 검증 (재현 명령)

```bash
# 정상: 합성 로그 60건 적재 → 총 60 / 해결 33 / 미해결 27 (기준 55.0%)
python3 src/scripts/load.py src/examples/tickets.csv src/examples/faq.csv --out out

# 예외: question 컬럼이 없는 로그 → 템플릿 안내 후 exit 1
python3 src/scripts/load.py src/examples/broken/tickets-broken.csv src/examples/faq.csv --out out2
```

전체 사이클(2~4단계 포함)은 위 '사용법'의 프롬프트로 Codex에서 실행합니다. 동봉 데이터는 **합성 데이터**(패션 커머스 가정)이며, 검증 리포트의 해결률 수치는 LLM 재시뮬레이션 판정값입니다(실측은 초안 반영·운영 후 측정).

## 구조

```
src/
├── .codex-plugin/plugin.json        # 플러그인 매니페스트
├── skills/resolution-lift/SKILL.md  # 절차·판단 기준·프롬프트·실패 동작 (핵심)
├── scripts/load.py                  # 1단계 (표준 라이브러리만)
├── scripts/simulate.py              # 4단계 검증·집계·리포트 (표준 라이브러리만)
└── examples/                        # 합성 로그 60건 + FAQ 12건 + 예외용 broken CSV
```
