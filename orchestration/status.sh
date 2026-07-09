#!/bin/bash
# 오케스트레이션 상태 대시보드
# 사용: orchestration/status.sh          — 3개 세션 전체
#       orchestration/status.sh <세션>   — 특정 세션만
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSIONS=${1:-"channeltalk kakaopay-securities samil-pwc"}

for s in $SESSIONS; do
  echo "═════ $s ═════"

  # tmux pane 마지막 상태 (작업 중 스피너/대기 프롬프트 확인)
  if tmux has-session -t "$s" 2>/dev/null; then
    tmux capture-pane -t "$s" -p | grep -v '^$' | tail -3 | sed 's/^/  pane│ /'
  else
    echo "  pane│ (tmux 세션 없음)"
  fi

  # JOURNAL: 완료된 스텝 목록 + 마지막 보고의 '오케스트레이터에게 요청'
  j="$ROOT/$s/context/JOURNAL.md"
  if [ -f "$j" ]; then
    echo "  journal│ 완료 스텝: $(grep -o '^\#\# \[step-[0-9]*\]' "$j" | grep -o 'step-[0-9]*' | tr '\n' ' ')"
    last_req=$(awk '/^## \[step-/{buf=""} {buf=buf $0 ORS} END{printf "%s", buf}' "$j" \
      | awk '/^### 오케스트레이터에게 요청/{f=1;next} /^###|^## /{f=0} f&&NF' | tr '\n' ' ')
    [ -n "$last_req" ] && echo "  journal│ 최근 요청: $last_req"
  else
    echo "  journal│ (JOURNAL.md 없음 — step-00 미완료)"
  fi

  # 산출물 존재 여부
  echo -n "  context│"
  for f in intent.md company.md sources.md problem.md solution.md plan.md verification.md; do
    [ -f "$ROOT/$s/context/$f" ] && echo -n " ✅$f" || echo -n " ▫$f"
  done
  echo
  [ -d "$ROOT/$s/src" ] && echo "  src│ 존재 ($(find "$ROOT/$s/src" -type f | wc -l | tr -d ' ')개 파일)" || echo "  src│ 없음"

  # 로그 훅 동작 확인 (개수만 — 내용은 절대 건드리지 않음)
  n=$(find "$ROOT/$s/logs" -name '*.jsonl' 2>/dev/null | wc -l | tr -d ' ')
  echo "  logs│ ${n}개 로그 파일"
  echo
done
