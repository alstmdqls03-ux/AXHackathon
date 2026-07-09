#!/bin/bash
# 스텝 디스패치: pane에 "step-NN을 읽고 수행하라" 한 줄을 보낸다
# 사용: orchestration/dispatch.sh step-01                    — 3개 세션 전부
#       orchestration/dispatch.sh step-01 channeltalk        — 특정 세션만
# 세션 이름 == 회사 폴더 이름 전제. pane cwd가 틀어져도 안전하도록 절대 경로 사용.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STEP="$1"; shift
SESSIONS=${@:-channeltalk kakaopay-securities samil-pwc}
[ -z "$STEP" ] && { echo "사용법: dispatch.sh step-NN [세션...]"; exit 1; }
[ -f "$ROOT/orchestration/prompts/$STEP.md" ] || { echo "없는 스텝: $STEP"; exit 1; }

for s in $SESSIONS; do
  tmux has-session -t "$s" 2>/dev/null || { echo "✗ $s : tmux 세션 없음 — 디스패치 실패"; continue; }
  tmux send-keys -t "$s" -l "작업 디렉토리를 $ROOT/$s 로 되돌린 뒤(bash cd), $ROOT/orchestration/prompts/$STEP.md 를 읽고 그대로 수행하라. 공통 규칙은 $ROOT/orchestration/prompts/RULES.md 를 따른다. 모든 산출물 경로(context/ 등)는 $ROOT/$s 기준이다."
  sleep 0.3
  tmux send-keys -t "$s" Enter
  echo "→ $s : $STEP 디스패치 완료"
done
