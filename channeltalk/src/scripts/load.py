#!/usr/bin/env python3
"""resolution-lift 1단계: 상담 로그 적재·검증·PII 마스킹·미해결 분리 (결정적).

사용법: python3 load.py <tickets.csv> <faq.csv> [--out OUT_DIR]
출력:   OUT_DIR/summary.json, OUT_DIR/unresolved.json, OUT_DIR/faq.json
실패:   스키마 불일치 시 필수 컬럼 안내 + CSV 템플릿을 출력하고 exit 1 (짐작 진행 금지)
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

REQUIRED_TICKET_COLS = ["ticket_id", "question"]
OPTIONAL_TICKET_COLS = ["created_at", "alf_answer", "resolved", "agent_answer"]
REQUIRED_FAQ_COLS = ["question", "answer"]

TICKETS_TEMPLATE = """ticket_id,created_at,question,alf_answer,resolved,agent_answer
T-0001,2026-06-01,"고객 질문 원문","ALF가 답한 내용(있다면)",true,
T-0002,2026-06-01,"고객 질문 원문","ALF 답변",false,"상담사가 실제로 답한 내용(있다면)"
"""

FAQ_TEMPLATE = """question,answer
"자주 묻는 질문","등록된 답변"
"""

PHONE_RE = re.compile(r"01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

TRUE_VALUES = {"true", "1", "y", "yes", "해결"}
FALSE_VALUES = {"false", "0", "n", "no", "미해결"}


def fail(msg: str) -> None:
    print(f"[resolution-lift:load] 오류: {msg}", file=sys.stderr)
    sys.exit(1)


def mask_pii(text: str, counter: dict) -> str:
    text, n_phone = PHONE_RE.subn("[전화번호 마스킹]", text)
    text, n_email = EMAIL_RE.subn("[이메일 마스킹]", text)
    counter["masked"] += n_phone + n_email
    return text


def read_csv_checked(path: Path, required: list, template: str, label: str) -> list:
    if not path.exists():
        fail(f"{label} 파일이 없습니다: {path}\n필요한 형식:\n{template}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        missing = [c for c in required if c not in cols]
        if missing:
            fail(
                f"{label}에 필수 컬럼이 없습니다: {', '.join(missing)}\n"
                f"발견된 컬럼: {', '.join(cols)}\n"
                f"필요한 형식(템플릿):\n{template}"
            )
        return list(reader)


def parse_resolved(row: dict, has_resolved_col: bool) -> tuple:
    """(resolved: bool, inferred: bool)를 반환. resolved 컬럼이 없으면
    agent_answer 존재 여부로 추정한다(상담사 답변이 있다 = ALF가 못 풀었다)."""
    if has_resolved_col and (row.get("resolved") or "").strip():
        v = row["resolved"].strip().lower()
        if v in TRUE_VALUES:
            return True, False
        if v in FALSE_VALUES:
            return False, False
        fail(
            f"resolved 값을 해석할 수 없습니다: '{row['resolved']}' (ticket_id={row.get('ticket_id')})\n"
            f"허용 값: {sorted(TRUE_VALUES)} / {sorted(FALSE_VALUES)}"
        )
    return (not (row.get("agent_answer") or "").strip()), True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="resolution-lift 1단계: 상담 로그 적재·검증",
        epilog=f"tickets.csv 형식:\n{TICKETS_TEMPLATE}\nfaq.csv 형식:\n{FAQ_TEMPLATE}",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tickets", help="상담 로그 CSV")
    parser.add_argument("faq", help="기존 지식 CSV")
    parser.add_argument("--out", default="out", help="출력 디렉터리 (기본: out)")
    ns = parser.parse_args()
    out_dir = Path(ns.out)

    tickets_path, faq_path = Path(ns.tickets), Path(ns.faq)
    rows = read_csv_checked(tickets_path, REQUIRED_TICKET_COLS, TICKETS_TEMPLATE, "상담 로그(tickets)")
    faq_rows = read_csv_checked(faq_path, REQUIRED_FAQ_COLS, FAQ_TEMPLATE, "기존 지식(faq)")

    has_resolved_col = False
    with tickets_path.open(newline="", encoding="utf-8-sig") as f:
        has_resolved_col = "resolved" in (csv.DictReader(f).fieldnames or [])

    counter = {"masked": 0}
    skipped = 0
    seen_ids = set()
    resolved_n = 0
    inferred_any = False
    unresolved = []

    for row in rows:
        tid = (row.get("ticket_id") or "").strip()
        q = (row.get("question") or "").strip()
        if not tid or not q:
            skipped += 1
            continue
        if tid in seen_ids:
            fail(f"ticket_id 중복: {tid} — 로그를 확인해 주세요.")
        seen_ids.add(tid)

        is_resolved, inferred = parse_resolved(row, has_resolved_col)
        inferred_any = inferred_any or inferred
        if is_resolved:
            resolved_n += 1
            continue
        unresolved.append({
            "ticket_id": tid,
            "question": mask_pii(q, counter),
            "alf_answer": mask_pii((row.get("alf_answer") or "").strip(), counter),
            "agent_answer": mask_pii((row.get("agent_answer") or "").strip(), counter),
        })

    total = len(seen_ids)
    if total == 0:
        fail(f"유효한 티켓이 0건입니다 (건너뜀 {skipped}건). tickets.csv 내용을 확인해 주세요.\n필요한 형식:\n{TICKETS_TEMPLATE}")

    faq = [{"question": r["question"].strip(), "answer": r["answer"].strip()}
           for r in faq_rows if (r.get("question") or "").strip()]

    summary = {
        "total": total,
        "resolved": resolved_n,
        "unresolved": len(unresolved),
        "baseline_resolution_rate": round(resolved_n / total, 4),
        "resolved_inferred": inferred_any,  # true면 리포트에 (추정) 표기 의무
        "masked_pii": counter["masked"],
        "skipped_rows": skipped,
        "faq_count": len(faq),
        "tickets_file": str(tickets_path),
        "faq_file": str(faq_path),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "unresolved.json").write_text(json.dumps(unresolved, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "faq.json").write_text(json.dumps(faq, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[resolution-lift:load] 적재 완료 — 총 {total}건 / 해결 {resolved_n}건 / 미해결 {len(unresolved)}건 "
          f"(기준 해결률 {summary['baseline_resolution_rate']*100:.1f}%"
          f"{', resolved 추정' if inferred_any else ''}"
          f"{f', PII 마스킹 {counter['masked']}건' if counter['masked'] else ''}"
          f"{f', 건너뜀 {skipped}건' if skipped else ''})")
    print(f"[resolution-lift:load] 출력: {out_dir}/summary.json, {out_dir}/unresolved.json, {out_dir}/faq.json")
    if inferred_any:
        print("[resolution-lift:load] 주의: resolved 컬럼이 없거나 비어 있어 agent_answer 존재 여부로 미해결을 추정했습니다."
              " 모든 리포트에 (추정) 표기가 붙습니다.")


if __name__ == "__main__":
    main()
