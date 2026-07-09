logs/stray/ — 훅 cwd 부작용으로 잘못된 위치에 생성됐던 로그 사본 (무편집 이동)

경위:
- 로깅 훅은 세션 cwd 기준으로 logs/claude-code/에 jsonl을 기록한다.
- 2026-07-09 세션 중 훅이 일시적으로 src/skills/trade-decision-report/를 cwd로 잡아,
  동일 세션 로그의 "잘린 prefix 사본"(53,941 bytes)이
  src/skills/trade-decision-report/logs/claude-code/ 아래에 생성되었다.
- 이 사본은 편집·발췌된 것이 아니라 기록 시점 차이로 인한 byte-exact prefix다.

처리 (2026-07-10, 무편집 이동):
1. 사본을 이 폴더(logs/stray/claude-code/)로 cp
2. cmp로 byte-identical 확인 후에만 원위치(src/ 및 설치 캐시본)에서 제거
3. 내용 수정·삭제는 일절 없음

동일 세션의 전체(정본) 로그:
- logs/claude-code/a75e0fe7-b332-4f20-865a-ab2aa085b5db.jsonl (67,053 bytes)
- 이 폴더의 a75e0fe7-*.jsonl(53,941 bytes)은 위 정본의 앞 53,941 bytes와 정확히 일치한다.
  확인 명령: cmp logs/stray/claude-code/a75e0fe7-*.jsonl <(head -c 53941 logs/claude-code/a75e0fe7-*.jsonl)
