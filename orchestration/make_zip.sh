#!/bin/bash
# submission.zip 생성 — 제출 직전에 실행해야 마지막 세션 로그까지 포함됨
# 사용: orchestration/make_zip.sh <회사폴더>   (예: make_zip.sh channeltalk)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
C="$1"
[ -n "$C" ] && [ -d "$ROOT/$C/src" ] || { echo "사용법: make_zip.sh <회사폴더> (src/ 필요)"; exit 1; }
cd "$ROOT/$C" || exit 1

# 규정 트리: zip 루트에 src/ + README.md + logs/ 만
rm -f submission.zip
zip -r submission.zip src README.md logs -x "*__pycache__*" -x "*.DS_Store" >/dev/null || exit 1

size_bytes=$(stat -f%z submission.zip 2>/dev/null || stat -c%s submission.zip)
echo "생성: $C/submission.zip — $(du -h submission.zip | cut -f1) ($size_bytes bytes, 제한 100MB)"
[ "$size_bytes" -gt 104857600 ] && { echo "⚠️ 100MB 초과!"; exit 1; }
echo "--- 루트 구성 확인:"
unzip -l submission.zip | awk '{print $4}' | grep -v '^$' | cut -d/ -f1 | sort -u
