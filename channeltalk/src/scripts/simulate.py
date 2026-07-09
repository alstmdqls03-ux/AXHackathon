#!/usr/bin/env python3
"""resolution-lift 4단계: LLM 산출물 검증·집계·리포트 렌더 (결정적).

사용법: python3 simulate.py <OUT_DIR>
입력:   OUT_DIR/summary.json·unresolved.json·faq.json (load.py 산출)
        OUT_DIR/gaps.json·faq_draft.json·simulation.json (SKILL.md 2~4단계에서 LLM이 작성)
출력:   OUT_DIR/gap-report.md, faq-draft.md, validation-report.md, report.html
실패:   스키마 위반·환각 티켓 ID·시뮬레이션 미커버 발견 시 리포트를 만들지 않고 exit 1
"""
import json
import sys
from pathlib import Path

GAP_TYPES = {
    "A": "A 지식 부재",
    "B": "B 지식 불명확",
    "C": "C 정책 결정 필요",
    "D": "D 태스크 필요",
    "REVIEW": "사람 검토 필요",
}
DRAFTABLE = {"A", "B"}  # C/D/REVIEW는 FAQ 초안 자동 생성 금지
CONFIDENCES = {"높음", "중간", "낮음"}
VERDICTS = {"해결", "부분", "미해결"}


def fail(msg: str) -> None:
    print(f"[resolution-lift:simulate] 오류: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(out_dir: Path, name: str, produced_by: str):
    p = out_dir / name
    if not p.exists():
        fail(f"{p} 가 없습니다 — {produced_by} 단계를 먼저 수행해 주세요.")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{p} JSON 파싱 실패: {e} — {produced_by} 단계의 출력 형식을 확인해 주세요.")


def validate(summary, unresolved, gaps, drafts, sims):
    ids = {t["ticket_id"] for t in unresolved}
    problems, warnings = [], []

    if not isinstance(gaps, list) or not gaps:
        problems.append("gaps.json은 비어 있지 않은 배열이어야 합니다.")
        gaps = []
    clusters = {}
    for i, g in enumerate(gaps):
        where = f"gaps[{i}]({g.get('cluster', '?')})"
        if not (g.get("cluster") or "").strip():
            problems.append(f"{where}: cluster 이름이 비었습니다.")
        if g.get("gap_type") not in GAP_TYPES:
            problems.append(f"{where}: gap_type '{g.get('gap_type')}' — 허용: {sorted(GAP_TYPES)}")
        if g.get("confidence") not in CONFIDENCES:
            problems.append(f"{where}: confidence '{g.get('confidence')}' — 허용: {sorted(CONFIDENCES)}")
        ev = g.get("evidence_tickets") or []
        if not ev:
            problems.append(f"{where}: evidence_tickets가 비었습니다 — 근거 티켓 없이 갭을 주장할 수 없습니다.")
        bad = [t for t in ev if t not in ids]
        if bad:
            problems.append(f"{where}: 미해결 로그에 없는 티켓 ID(환각 의심): {bad}")
        if not (g.get("rationale") or "").strip():
            problems.append(f"{where}: rationale(판단 근거)이 비었습니다.")
        clusters[g.get("cluster")] = g

    assigned = {t for g in gaps for t in (g.get("evidence_tickets") or [])}
    unassigned = sorted(ids - assigned)
    if unassigned:
        warnings.append(f"어느 클러스터에도 속하지 않은 미해결 티켓 {len(unassigned)}건: {unassigned} — "
                        "REVIEW 클러스터로 분류를 권장합니다.")

    if not isinstance(drafts, list):
        problems.append("faq_draft.json은 배열이어야 합니다.")
        drafts = []
    for i, d in enumerate(drafts):
        where = f"faq_draft[{i}]({d.get('cluster', '?')})"
        g = clusters.get(d.get("cluster"))
        if g is None:
            problems.append(f"{where}: gaps.json에 없는 클러스터를 참조합니다.")
        elif g.get("gap_type") not in DRAFTABLE:
            problems.append(f"{where}: gap_type {g.get('gap_type')} 클러스터에는 FAQ 초안을 자동 생성하지 않습니다 "
                            f"(C=정책 결정, D=태스크, REVIEW=사람 검토).")
        qv = [q for q in (d.get("question_variants") or []) if (q or "").strip()]
        if not qv:
            problems.append(f"{where}: question_variants가 비었습니다.")
        elif len(qv) < 3:
            warnings.append(f"{where}: 질문 변형이 {len(qv)}개 (권장 3개 이상).")
        if not (d.get("answer") or "").strip():
            problems.append(f"{where}: answer가 비었습니다.")
        basis = d.get("basis_tickets") or []
        bad = [t for t in basis if t not in ids]
        if bad:
            problems.append(f"{where}: 미해결 로그에 없는 근거 티켓(환각 의심): {bad}")
        if not basis and not d.get("policy_check"):
            problems.append(f"{where}: 근거 티켓이 없는데 policy_check=true 마커도 없습니다 — "
                            "근거 없는 답변은 [정책 확인 필요]로 표시해야 합니다.")

    if not isinstance(sims, list):
        problems.append("simulation.json은 배열이어야 합니다.")
        sims = []
    sim_ids = set()
    for i, s in enumerate(sims):
        where = f"simulation[{i}]({s.get('ticket_id', '?')})"
        tid = s.get("ticket_id")
        if tid not in ids:
            problems.append(f"{where}: 미해결 로그에 없는 티켓 ID(환각 의심).")
            continue
        if tid in sim_ids:
            problems.append(f"{where}: 중복 판정.")
        sim_ids.add(tid)
        if s.get("verdict") not in VERDICTS:
            problems.append(f"{where}: verdict '{s.get('verdict')}' — 허용: {sorted(VERDICTS)}")
        if not (s.get("reason") or "").strip():
            problems.append(f"{where}: reason(판정 사유)이 비었습니다.")
    missing = sorted(ids - sim_ids)
    if missing:
        problems.append(f"시뮬레이션이 미해결 전건을 커버하지 않습니다 — 누락 {len(missing)}건: {missing}")

    if problems:
        fail("검증 실패 — 리포트를 생성하지 않습니다:\n- " + "\n- ".join(problems))
    return warnings, unassigned


def bar_html(label: str, pct: float, color: str) -> str:
    return (f'<div class="row"><span class="lbl">{label}</span>'
            f'<div class="track"><div class="fill" style="width:{pct:.1f}%;background:{color}">'
            f'{pct:.1f}%</div></div></div>')


def render(out_dir: Path, summary, unresolved, gaps, drafts, sims, warnings, unassigned):
    ids2q = {t["ticket_id"]: t["question"] for t in unresolved}
    verdict_of = {s["ticket_id"]: s for s in sims}
    total, resolved = summary["total"], summary["resolved"]
    base_pct = resolved / total * 100
    lift = sum(1 for s in sims if s["verdict"] == "해결")
    partial = sum(1 for s in sims if s["verdict"] == "부분")
    after = resolved + lift
    after_pct = after / total * 100
    inferred_note = " ※ resolved 값은 agent_answer 존재 여부로 **(추정)** 된 것임" if summary.get("resolved_inferred") else ""
    sim_note = ("※ 본 수치는 입력 로그에 대한 LLM 재시뮬레이션 판정값이며, 실제 해결률은 초안 반영·운영 후 측정해야 한다. "
                "'부분' 판정은 보수적으로 미해결로 집계.")

    def cluster_rows():
        rows = []
        for g in gaps:
            ev = g.get("evidence_tickets") or []
            n_lift = sum(1 for t in ev if verdict_of.get(t, {}).get("verdict") == "해결")
            rows.append((g["cluster"], g["gap_type"], g["confidence"], len(ev), n_lift, g["rationale"]))
        return sorted(rows, key=lambda r: -r[3])

    # ---- gap-report.md
    lines = ["# 갭 리포트 (gap-report)", "",
             f"- 입력: {summary['tickets_file']} (총 {total}건) / 기존 지식 {summary['faq_count']}건",
             f"- 기준 해결률: **{resolved}/{total} ({base_pct:.1f}%)**{inferred_note}",
             f"- 미해결 {summary['unresolved']}건을 {len(gaps)}개 클러스터로 분류", ""]
    if summary.get("masked_pii"):
        lines.append(f"- 개인정보 마스킹: {summary['masked_pii']}건 처리됨")
    if summary.get("skipped_rows"):
        lines.append(f"- 빈 행 등 건너뜀: {summary['skipped_rows']}건")
    lines += ["", "| 클러스터 | 갭 유형 | confidence | 건수 | 시뮬레이션 해결 | 판단 근거 |",
              "|---|---|---|---|---|---|"]
    for c, t, conf, n, nl, rat in cluster_rows():
        lines.append(f"| {c} | {GAP_TYPES[t]} | {conf} | {n} | {nl} | {rat} |")
    if unassigned:
        lines += ["", f"⚠️ 미분류 티켓 {len(unassigned)}건: {', '.join(unassigned)}"]
    for w in warnings:
        lines += ["", f"⚠️ {w}"]
    (out_dir / "gap-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- faq-draft.md
    lines = ["# FAQ·규칙 초안 (faq-draft)", "",
             "> 아래 초안은 상담사 실답변(basis_tickets)을 1차 근거로 생성됨. "
             "**[정책 확인 필요]** 마커가 있는 항목은 담당자 확정 전 등록 금지.", ""]
    for d in drafts:
        marker = " **[정책 확인 필요]**" if d.get("policy_check") else ""
        lines.append(f"## {d['cluster']}{marker}")
        lines.append("")
        for q in d["question_variants"]:
            lines.append(f"- Q. {q}")
        lines.append("")
        lines.append(f"**A.** {d['answer']}")
        basis = d.get("basis_tickets") or []
        if basis:
            lines.append("")
            lines.append(f"근거 티켓: {', '.join(basis)}")
        lines.append("")
    todo = [g for g in gaps if g["gap_type"] not in DRAFTABLE]
    if todo:
        lines += ["---", "", "## 자동 초안 대상이 아닌 갭 (사람 몫)", ""]
        for g in todo:
            lines.append(f"- **{g['cluster']}** ({GAP_TYPES[g['gap_type']]}, {len(g['evidence_tickets'])}건): "
                         f"{g['rationale']}")
    (out_dir / "faq-draft.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- validation-report.md
    lines = ["# 검증 리포트 (validation-report)", "",
             f"| 지표 | 값 |", "|---|---|",
             f"| 기준(현행 지식) 해결 | {resolved}/{total} ({base_pct:.1f}%) |",
             f"| 초안 반영 시뮬레이션 해결 | **{after}/{total} ({after_pct:.1f}%)** |",
             f"| 상승분 | **+{lift}건 (+{after_pct - base_pct:.1f}%p)** |",
             f"| '부분' 판정 (미해결로 집계) | {partial}건 |",
             f"| 시뮬레이션 후에도 미해결 | {total - after}건 |",
             "", sim_note + inferred_note, "", "## 티켓별 판정", "",
             "| 티켓 | 질문 | 판정 | 사유 |", "|---|---|---|---|"]
    for s in sims:
        lines.append(f"| {s['ticket_id']} | {ids2q[s['ticket_id']]} | {s['verdict']} | {s['reason']} |")
    (out_dir / "validation-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- report.html
    cluster_tr = "".join(
        f"<tr><td>{c}</td><td>{GAP_TYPES[t]}</td><td>{conf}</td><td>{n}</td><td>{nl}</td></tr>"
        for c, t, conf, n, nl, _ in cluster_rows())
    policy_items = [d["cluster"] for d in drafts if d.get("policy_check")] + \
                   [f"{g['cluster']} ({GAP_TYPES[g['gap_type']]})" for g in gaps if g["gap_type"] not in DRAFTABLE]
    policy_html = "".join(f"<li>{p}</li>" for p in policy_items) or "<li>없음</li>"
    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>resolution-lift 리포트</title>
<style>
body{{font-family:'Apple SD Gothic Neo',sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#222}}
h1{{font-size:1.4rem}} .row{{display:flex;align-items:center;margin:.5rem 0}}
.lbl{{width:180px;font-size:.9rem}} .track{{flex:1;background:#eee;border-radius:4px}}
.fill{{color:#fff;padding:.35rem .5rem;border-radius:4px;font-size:.85rem;white-space:nowrap}}
table{{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.9rem}}
td,th{{border:1px solid #ddd;padding:.4rem .6rem;text-align:left}} th{{background:#f7f7f7}}
.note{{color:#666;font-size:.85rem}}
</style></head><body>
<h1>resolution-lift — AI 상담 해결률 개선 리포트</h1>
<p>총 {total}건 / 미해결 {summary['unresolved']}건 / 갭 클러스터 {len(gaps)}개 / FAQ 초안 {len(drafts)}건</p>
{bar_html('기준(현행 지식)', base_pct, '#8a8a8a')}
{bar_html('초안 반영 시뮬레이션', after_pct, '#2f7d4f')}
<p><b>상승분 +{lift}건 (+{after_pct - base_pct:.1f}%p)</b> · '부분' {partial}건은 미해결로 집계</p>
<h2>갭 클러스터</h2>
<table><tr><th>클러스터</th><th>갭 유형</th><th>confidence</th><th>건수</th><th>시뮬레이션 해결</th></tr>{cluster_tr}</table>
<h2>사람 확인이 필요한 항목</h2><ul>{policy_html}</ul>
<p class="note">{sim_note}{inferred_note}</p>
</body></html>
"""
    (out_dir / "report.html").write_text(html, encoding="utf-8")

    print(f"[resolution-lift:simulate] 검증 통과 — 리포트 4종 생성: {out_dir}/gap-report.md, faq-draft.md, "
          f"validation-report.md, report.html")
    print(f"[resolution-lift:simulate] 해결률 {base_pct:.1f}% → {after_pct:.1f}% (+{lift}건, 시뮬레이션 기준)")
    for w in warnings:
        print(f"[resolution-lift:simulate] 경고: {w}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("사용법: python3 simulate.py <OUT_DIR>  (OUT_DIR = load.py의 --out 디렉터리)")
    out_dir = Path(sys.argv[1])
    summary = load_json(out_dir, "summary.json", "1(load.py)")
    unresolved = load_json(out_dir, "unresolved.json", "1(load.py)")
    gaps = load_json(out_dir, "gaps.json", "2(갭 분류 — SKILL.md)")
    drafts = load_json(out_dir, "faq_draft.json", "3(초안 생성 — SKILL.md)")
    sims = load_json(out_dir, "simulation.json", "4(재시뮬레이션 채점 — SKILL.md)")
    warnings, unassigned = validate(summary, unresolved, gaps, drafts, sims)
    render(out_dir, summary, unresolved, gaps, drafts, sims, warnings, unassigned)


if __name__ == "__main__":
    main()
