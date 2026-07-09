#!/usr/bin/env python3
"""회사별 검토 리포트 렌더러: 요약 워크플로 JSON → reports/<회사>.html

사용: python3 orchestration/render_report.py <data.json>
data.json은 {"result": {<key>: <company data>, ...}} 또는 {<key>: <company data>} 형식.
"""
import html
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTMAP = {
    "channeltalk": ("channeltalk.html", "채널톡"),
    "samil": ("samil-pwc.html", "삼일PwC"),
    "samil-pwc": ("samil-pwc.html", "삼일PwC"),
    "kakao": ("kakaopay-securities.html", "카카오페이증권"),
    "kakaopay-securities": ("kakaopay-securities.html", "카카오페이증권"),
}
AXES = ["의도 적합성", "공개 근거 강도", "비즈니스 임팩트", "플러그인 적합성", "데모 가능성"]
WEIGHTS = {"의도 적합성": 30, "공개 근거 강도": 25, "비즈니스 임팩트": 20, "플러그인 적합성": 15, "데모 가능성": 10}

CSS = """
body{font-family:'Apple SD Gothic Neo','Noto Sans KR',sans-serif;max-width:900px;margin:2rem auto;padding:0 1.5rem;color:#1a1a2e;line-height:1.65}
h1{font-size:1.5rem;border-bottom:3px solid #16324f;padding-bottom:.5rem}
h2{font-size:1.15rem;margin-top:2.2rem;color:#16324f;border-left:4px solid #16324f;padding-left:.6rem}
h3{font-size:1rem;margin-top:1.4rem}
.meta{color:#555;font-size:.85rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.9rem}
th,td{border:1px solid #cdd5df;padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:#eef2f7}
td.num,th.num{text-align:right;white-space:nowrap}
tr.rec{background:#eafaf0;font-weight:600}
.badge{display:inline-block;background:#16324f;color:#fff;border-radius:4px;padding:.1rem .5rem;font-size:.78rem;margin-left:.4rem;font-weight:600}
.card{border:1px solid #cdd5df;border-radius:8px;padding:1rem 1.2rem;margin:1rem 0}
.card.rec{border-color:#2e9e5b;box-shadow:0 0 0 2px #eafaf0}
ul{padding-left:1.2rem}
li{margin:.3rem 0}
.small{font-size:.85rem;color:#444}
.warn{background:#fff8e6;border:1px solid #e6c96b;border-radius:8px;padding:.9rem 1.2rem}
.footer{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #cdd5df;font-size:.85rem;color:#555}
code{background:#f0f2f5;padding:0 .3rem;border-radius:3px;font-size:.88em}
"""


def esc(s):
    return html.escape(str(s))


def lis(items):
    return "\n".join(f"<li>{esc(i)}</li>" for i in items)


def render(key, d):
    fname, disp = OUTMAP.get(key, (f"{key}.html", key))
    cands = d["candidates"]
    rec_id = d["recommendation"]["id"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    head_cols = "".join(
        f'<th class="num">{esc(a)}<br><span class="small">/{WEIGHTS[a]}</span></th>' for a in AXES
    )
    score_rows = []
    for c in sorted(cands, key=lambda x: -x["total"]):
        cls = ' class="rec"' if c["id"] == rec_id else ""
        cells = "".join(f'<td class="num">{c["scores"].get(a, "—")}</td>' for a in AXES)
        mark = ' <span class="badge">추천</span>' if c["id"] == rec_id else ""
        score_rows.append(
            f'<tr{cls}><td>{esc(c["id"])}. {esc(c["name"])}{mark}</td>{cells}'
            f'<td class="num"><b>{c["total"]}</b></td></tr>'
        )

    cards = []
    for c in cands:
        cls = "card rec" if c["id"] == rec_id else "card"
        mark = ' <span class="badge">추천</span>' if c["id"] == rec_id else ""
        cards.append(f"""
<div class="{cls}">
<h3>후보 {esc(c["id"])} — {esc(c["name"])}{mark} <span class="small">(총점 {c["total"]}/100)</span></h3>
<p>{esc(c["definition"])}</p>
<b class="small">핵심 근거</b><ul class="small">{lis(c["evidence"])}</ul>
<b class="small">Opportunity Sizing</b><p class="small">{esc(c["sizing"])}</p>
<b class="small">점수 사유</b><ul class="small">{lis(c["score_rationale"])}</ul>
</div>""")

    body = f"""<title>{esc(disp)} 문제 선정 검토 리포트</title>
<style>{CSS}</style>
<h1>{esc(disp)} — 문제 선정 검토 리포트</h1>
<p class="meta">생성: {now} · 목적: step-03 문제 선정 승인 전 사용자 검토 · 원문: <code>{esc(key if key in ('channeltalk','samil-pwc','kakaopay-securities') else fname.replace('.html',''))}/context/problem.md</code></p>
<p class="meta">근거 대장: {esc(d["ledger_stats"])}</p>

<h2>1. 리서치 요약</h2>
<ul>{lis(d["research_summary"])}</ul>

<h2>2. 후보 점수표 <span class="small">(의도 30 / 근거 25 / 임팩트 20 / 플러그인 15 / 데모 10)</span></h2>
<table>
<tr><th>후보</th>{head_cols}<th class="num">총점<br><span class="small">/100</span></th></tr>
{"".join(score_rows)}
</table>

<h2>3. 후보 상세</h2>
{"".join(cards)}

<h2>4. 추천</h2>
<div class="card rec"><b>후보 {esc(rec_id)}</b><p>{esc(d["recommendation"]["why"])}</p></div>

<h2>5. 승인 전 검증 포인트 (사용자 확인 필요)</h2>
<div class="warn"><ul>{lis(d["verification_points"])}</ul></div>

<div class="footer">피드백 방법: 오케스트레이터 채팅에 "{esc(disp)} {esc(rec_id)} 승인" / "후보 X로 변경" / 구체 피드백을 남기면 해당 pane에 반영됩니다.
모든 점수·요약은 해당 회사 폴더의 context/ 산출물(intent·company·sources·problem)만을 근거로 산정됨.</div>
"""
    outdir = os.path.join(ROOT, "reports")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    data = data.get("result", data)
    for key, d in data.items():
        print("wrote", render(key, d))


if __name__ == "__main__":
    main()
