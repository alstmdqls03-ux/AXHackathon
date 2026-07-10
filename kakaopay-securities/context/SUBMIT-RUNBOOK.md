# SUBMIT-RUNBOOK.md — 카카오페이증권 제출 런북

제출 폼: https://hack.primer.kr/rounds/10/opportunities/4/submission/new
마감: **2026-07-10 (금) 23:59:59** — 마감 후 제출 불가, 마감 전에는 재제출 가능.

## 0. 제출 직전 준비

1. 이 폴더에서 미커밋 변경 확인: `git status --short .`
2. **submission.zip 재생성** (세션 로그가 계속 쌓이므로 업로드 직전에 반드시 재생성):
   ```bash
   cd ~/code/ax-hackathon/kakaopay-securities
   rm -f submission.zip
   zip -r submission.zip src README.md logs -x "*__pycache__*" -x "*.DS_Store"
   ```
3. 확인: `unzip -l submission.zip | tail -3` — 루트에 src/·README.md·logs/만, ≤100MB (현재 ~1.2MB).
   `unzip -l submission.zip | grep plugin.json` — `src/.codex-plugin/plugin.json` 존재.

## 1. 문항 1~5 복붙 (question.md 기준)

`question.md`의 각 `## 문항 N` 절 본문을 그대로 복사한다.
**주의**: 문항 2의 `### 출처 URL` 절과 문서 하단 `## 자수 확인 결과` 절은 본문에 포함하지 않는다 (자수 측정 제외 구간).

| 순서 | 문항 | 자수 (2026-07-10 측정) | 제한 |
|---|---|---|---|
| 1 | 무엇을, 누가, 어떤 상황에서 쓰나요? | 694자 | 800자 |
| 2 | 왜 이 문제를 선택했나요? | 716자 | 800자 |
| 3 | 플러그인은 어떻게 작동하나요? | 988자 | 1000자 |
| 4 | AI를 어떻게 썼나요? | 684자 | 800자 |
| 5 | 어떻게 검증했나요? | 731자 | 800자 |

붙여넣은 뒤 폼의 자수 카운터가 위 표와 대략 일치하는지 확인 (폼 측정 방식이 다를 수 있음 — 초과 시 question.md를 고치지 말고 폼 기준으로 재확인).

## 2. 문항 2 출처 URL 개별 입력 (7건, 전부 로그인 불요 — 2026-07-10 접근 확인)

1. https://www.youtube.com/watch?v=aBuoojGjyf4 — 출제자 힌트 영상 (01:03~01:19)
2. https://www.kcmi.re.kr/report/report_view?report_no=1243 — 신규투자자 60% 손실, -1.2%
3. https://www.kcmi.re.kr/report/report_view?report_no=1481 — 거래회전율 1,600%, 처분효과 41% vs 22%
4. https://www.a-ha.io/questions/48f180ac9f623139a1d681a47150492e — 유저 원문: 물타기 질문
5. https://www.industrynews.co.kr/news/articleView.html?idxno=73167 — 회사 관계자 발언
6. https://www.newsis.com/view/NISX20251119_0003408486 — 주식 모으기 160만 명
7. https://www.kakaopaysec.com/company/news_page/dynamicNewsDetail.do?id=12 — 계좌 700만·2040 70%대

## 3. submission.zip 업로드

- 0단계에서 재생성한 `submission.zip`을 업로드.
- 업로드 후 폼이 파일명·용량을 표시하면 캡처(스크린샷) 보관.
- 제출 버튼 클릭 → 완료 화면/확인 메일 캡처 보관.

## 4. 마감 전 재제출 절차

마감(2026-07-10 23:59:59) 전에는 재제출 가능 — 최소 버전을 일찍 제출하고 개선한다.

1. 수정 사항 반영 후 커밋 (`logs/`는 편집 금지 — git add만).
2. 0단계대로 submission.zip **재생성** (이전 zip 재사용 금지 — 로그 최신화).
3. 제출 폼에서 재제출: 문항 텍스트를 바꿨다면 1단계 자수 재확인 후 전체 재입력, 아니면 zip만 교체.
4. 재제출 완료 화면 캡처. **마감 임박 시 미완 개선보다 제출 상태 유지가 우선** — 23:30 이후에는 새 변경을 넣지 않는다.
