이 폴더의 파일은 로그 훅(save_log.py)이 셸 작업 디렉토리 기준으로 저장하는 동작 때문에
플러그인 폴더(src/skills/haenggan-audit/logs/claude-code/) 안에 생성됐던 세션 로그의
중간 스냅샷을, 내용 무편집(byte-identical 확인)으로 이곳에 옮겨 보존한 것입니다.

- 파일: claude-code/3dd43331-f4c7-495a-9cab-3420d6ba2fa4.jsonl (2026-07-09 23:36 시점 스냅샷)
- 동일 세션의 전체(최종) 로그: logs/claude-code/3dd43331-f4c7-495a-9cab-3420d6ba2fa4.jsonl
  (훅이 매 턴 전체 전사를 다시 쓰므로 최종본이 완전한 기록입니다)
- 로그 내용에는 일절 손대지 않았습니다 — 위치 이동만 수행 (2026-07-10).

[추가 2026-07-10] 두 번째 스트레이 스냅샷 이관:
- 파일: claude-code-context-snapshot/3dd43331-f4c7-495a-9cab-3420d6ba2fa4.jsonl
  (context/logs/claude-code/ 에 훅의 cwd 기준 저장 동작으로 생성됐던 동일 세션의 또 다른 중간 스냅샷)
- 절차: cp → cmp byte-identical 확인 → 원위치 제거 (내용 무편집, 위치 이동만)
- 동일 세션의 전체(최종) 로그: logs/claude-code/3dd43331-f4c7-495a-9cab-3420d6ba2fa4.jsonl
