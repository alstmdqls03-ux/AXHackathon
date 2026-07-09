# AX 인재전쟁 — 예선 제출 워크스페이스

3개 회사(채널톡 · 카카오페이증권 · 삼일PwC)에 각각 **독립적인 Codex 플러그인**을 만들어 제출하는 워크스페이스.

**마감: 2026-07-10 (금) 23:59:59** — 마감 후 제출 불가, 마감 전 재제출 가능.

## 문서 지도

| 문서 | 용도 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | 최우선 원칙 — 모든 세션이 따르는 규칙 |
| [submission-spec.md](submission-spec.md) | 제출 규정 전체 (과제 페이지·FAQ·운영 규정 원문 검증본) |
| [WORKFLOW.md](WORKFLOW.md) | 5단계 파이프라인 + 타임박스 + 제출 체크리스트 |
| [RESEARCH_PLAYBOOK.md](RESEARCH_PLAYBOOK.md) | 리서치 방법, 출처 우선순위·기록 규칙 |

## 회사 폴더 (독립 제출물)

| 폴더 | 회사 | 제출 폼 |
|---|---|---|
| `channeltalk/` | 채널톡 | opportunities/1 |
| `kakaopay-securities/` | 카카오페이증권 | opportunities/4 |
| `samil-pwc/` | 삼일PwC | opportunities/5 |

## 사용 규칙 (중요)

- **회사 작업은 반드시 해당 회사 폴더에서 세션 시작**: `cd channeltalk && claude` — 그래야 로그 훅이 그 회사의 `logs/`에 저장하고, 회사 간 리서치가 섞이지 않는다.
- 루트 세션은 공용 문서·오케스트레이션 전용. 회사별 리서치·구현 금지.
- `logs/` 아래 파일은 어느 폴더든 절대 수정·삭제 금지 (실격 사유).

## 제출물 형태 (회사별, 폴더에서 그대로 zip)

```
submission.zip
├── src/                      # 플러그인 루트 (.codex-plugin/plugin.json 필수)
├── README.md                 # 설치·실행 + 작동 방식 (문항 3과 일치)
└── logs/                     # AI 대화 로그 원본 (훅 자동 생성)
```

질문 5문항은 각 회사 폴더의 `question.md`에서 초안 관리 후 제출 폼에 입력 (zip에는 미포함).
