#!/usr/bin/env python3
"""스키마 검증 + 고정 템플릿 조립: diagnosis.json + options.json → 스탬프된 report.md.

solution.md §5의 강제 구조가 전부 여기 있다:
- 제약 1(서열화 금지): id enum 4종 고정·제목 하드코딩·가나다순 정렬·denylist·길이 제한
- 제약 2(근거 접지): evidence는 실존 metric id만, 서술 숫자는 {metrics.xxx} 플레이스홀더만
- 제약 3(고정 템플릿): 최종 마크다운은 이 스크립트만 생성, report-id 스탬프
LLM은 options.json의 필드 값만 쓸 수 있고, 검증 실패 시 리포트는 생성되지 않는다.
"""
import argparse
import hashlib
import json
import re
import sys

OPTION_TITLES = {  # 제목은 하드코딩 — LLM은 id만 고른다 (제약 1a)
    "hold": "보유 지속",
    "partial_sell": "부분 매도",
    "dca": "분할 추가 매수",
    "sell_all": "전량 매도",
}
TEXT_FIELDS = ["what_happens", "locked_in", "unknown"]
OPTION_KEYS = {"id", "what_happens", "evidence", "locked_in", "unknown"}
MAX_TEXT = 200  # 분량 비대칭 억제 (제약 1d)

# 추천·비교·예측 어휘 denylist (제약 1c) — 완전하지 않으나 거부→재작성 루프로 실용적 충분 (solution.md §5 한계)
DENYLIST = re.compile(
    "추천|권장|가장|최선|최악|제일|유리|불리|낫다|나은|더 좋|하는 게 좋|해야 한|해야만|"
    "반드시|무조건|확실|베스트|반등|폭등|폭락|전망|오를|내릴"
)
PLACEHOLDER = re.compile(r"\{metrics\.([a-z_]+)\}")
EVIDENCE_PATTERN = re.compile(r"^metrics\.[a-z_]+$")

CHECKLISTS = {  # ③ 실행 체크리스트 — 고정 템플릿 (제약 3)
    "hold": ["보유 사유를 한 줄로 메모해 두기 (다음 점검 때 스스로 납득하기 위한 기록)",
             "다음 점검 시점 정하기 (예: 실적 발표일)",
             "이 리포트를 다시 만들 조건 정하기 (가격·환율이 크게 움직였을 때)"],
    "partial_sell": ["몇 주를 팔지 결정하고 주문 전 수량 확인",
                     "지정가/시장가의 의미 확인 후 주문 유형 선택",
                     "체결 후 체결가·수수료 확인",
                     "남긴 수량의 다음 점검 시점 정하기"],
    "dca": ["추가 투입 금액이 감당 가능한 돈인지 확인 (생활비·비상금 제외)",
            "분할 횟수와 간격 정하기",
            "매수 후 바뀐 평균 단가 확인",
            "추가 하락 시 어떻게 할지 미리 메모"],
    "sell_all": ["주문 전 최종 확인: 보유 수량 전체",
                 "지정가/시장가의 의미 확인 후 주문 유형 선택",
                 "체결 후 체결가·수수료 확인",
                 "올해 다른 해외주식 손익과의 통산 여부 메모 (세금 신고 시 활용)"],
}


def fail(code, violations):
    print(json.dumps({"error": code, "violations": violations}, ensure_ascii=False, indent=2))
    sys.exit(1)


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), open(path, "rb").read()
    except FileNotFoundError:
        fail("INPUT_NOT_FOUND", [f"{what} 파일을 찾을 수 없습니다: {path}"])
    except json.JSONDecodeError as e:
        fail("INPUT_NOT_JSON", [f"{what}가 유효한 JSON이 아닙니다: {e}"])


def validate_options(options, metrics):
    v = []  # 위반은 전부 모아서 한 번에 보고
    if not isinstance(options, list) or len(options) != 4:
        fail("SCHEMA_INVALID", ["options는 정확히 4개여야 합니다 (hold/partial_sell/dca/sell_all 각 1개)"])
    ids = [o.get("id") for o in options]
    if sorted(ids) != sorted(OPTION_TITLES):
        fail("SCHEMA_INVALID", [f"options[].id는 {sorted(OPTION_TITLES)} 각 1개여야 합니다 (입력: {ids})"])

    for o in options:
        oid = o["id"]
        extra = set(o.keys()) - OPTION_KEYS
        missing = OPTION_KEYS - set(o.keys())
        if extra:
            v.append({"code": "SCHEMA_INVALID", "option": oid, "detail": f"허용되지 않은 필드: {sorted(extra)} (순위·점수 필드 금지)"})
        if missing:
            v.append({"code": "SCHEMA_INVALID", "option": oid, "detail": f"누락 필드: {sorted(missing)}"})
            continue
        ev = o["evidence"]
        if not isinstance(ev, list) or not ev:
            v.append({"code": "EVIDENCE_NOT_GROUNDED", "option": oid, "detail": "evidence는 비어 있지 않은 배열이어야 합니다"})
        else:
            for e in ev:
                if not isinstance(e, str) or not EVIDENCE_PATTERN.match(e):
                    v.append({"code": "EVIDENCE_NOT_GROUNDED", "option": oid, "detail": f"근거는 metrics.<id> 참조만 허용: {e!r}"})
                elif e.split(".", 1)[1] not in metrics:
                    v.append({"code": "EVIDENCE_NOT_GROUNDED", "option": oid, "detail": f"진단 산출물에 없는 metric: {e}"})
        for field in TEXT_FIELDS:
            text = o[field]
            if not isinstance(text, str) or not text.strip():
                v.append({"code": "SCHEMA_INVALID", "option": oid, "detail": f"{field}는 비어 있지 않은 문자열이어야 합니다"})
                continue
            if len(text) > MAX_TEXT:
                v.append({"code": "SCHEMA_INVALID", "option": oid, "detail": f"{field}가 {MAX_TEXT}자를 초과 ({len(text)}자)"})
            m = DENYLIST.search(text)
            if m:
                v.append({"code": "RANKING_LANGUAGE_DETECTED", "option": oid,
                          "detail": f"{field}에 추천·비교·예측 어휘 {m.group(0)!r} — 이 리포트는 순위를 매기지 않습니다"})
            for ref in PLACEHOLDER.findall(text):
                if ref not in metrics:
                    v.append({"code": "EVIDENCE_NOT_GROUNDED", "option": oid, "detail": f"{field}의 플레이스홀더가 진단에 없음: metrics.{ref}"})
            if re.search(r"\d", PLACEHOLDER.sub("", text)):
                v.append({"code": "UNGROUNDED_NUMBER", "option": oid,
                          "detail": f"{field}에 숫자 리터럴 — 숫자는 {{metrics.xxx}} 플레이스홀더로만 (모든 숫자는 결정론 계산 산출물이어야 함)"})
    if v:
        fail(v[0]["code"], v)


def fmt(metrics, key):
    val = metrics[key]
    if key.endswith("_krw"):
        return f"{val:,.0f}원"
    if key.endswith("_pct") or key.endswith("_pp"):
        return f"{val:+.2f}%p" if key.endswith("_pp") else f"{val:.2f}%"
    if key.endswith("_usd"):
        return f"${val:,.2f}"
    if key == "fx_now" or key == "avg_buy_fx":
        return f"{val:,.1f}원"
    return str(val)


def substitute(text, metrics):
    return PLACEHOLDER.sub(lambda m: fmt(metrics, m.group(1)), text)


def build_report(metrics, options, chosen):
    m = metrics
    fx_dir = "강세" if m["fx_now"] > m["avg_buy_fx"] else ("약세" if m["fx_now"] < m["avg_buy_fx"] else "변동 없음")
    fx_note = (f"매수 시점 평균 환율 {m['avg_buy_fx']:,.1f}원 → 현재 {m['fx_now']:,.1f}원, "
               f"달러 {fx_dir}가 원화 환산 수익률에 {m['fx_effect_pp']:+.2f}%p 기여")
    lines = [
        f"# 매매 의사결정 리포트 — {m['ticker']} {m['qty']:g}주",
        "",
        "## ① 진단 — \"손해 봤나?\"의 실체",
        "",
        "| 지표 | 값 |",
        "|---|---|",
        f"| 명목 수익률(가격만, USD) | {m['nominal_return_usd_pct']:.2f}% |",
        f"| 실질 수익률(매수 수수료 포함, USD) | {m['true_return_usd_pct']:.2f}% |",
        f"| **실질 수익률(원화 환산)** | **{m['true_return_krw_pct']:.2f}%** |",
        f"| 환율 효과 | {fx_note} |",
        f"| 평가손익(원화) | {m['unrealized_pnl_krw']:,.0f}원 |",
        f"| 지금 전량 매도 시 확정 손익(제비용 반영) | {m['realized_loss_if_sell_krw']:,.0f}원 |",
        f"| 매도 시 양도소득세(단순화 계산) | {m['tax_if_sell_krw']:,.0f}원 |",
        "",
        "## ② 선택지 비교 (가나다순)",
        "",
        "> 이 리포트는 순위·추천을 제시하지 않으며, 결정은 사용자의 몫입니다. 미래 주가는 이 리포트가 알 수 없습니다.",
        "",
    ]
    for o in sorted(options, key=lambda o: OPTION_TITLES[o["id"]]):
        ev = " · ".join(f"`{e}` = {fmt(metrics, e.split('.', 1)[1])}" for e in o["evidence"])
        lines += [
            f"### {OPTION_TITLES[o['id']]}",
            f"- **일어나는 일**: {substitute(o['what_happens'], metrics)}",
            f"- **근거(진단 수치)**: {ev}",
            f"- **확정되는 것**: {substitute(o['locked_in'], metrics)}",
            f"- **알 수 없는 것**: {substitute(o['unknown'], metrics)}",
            "",
        ]
    lines += ["## ③ 실행 체크리스트", ""]
    targets = [chosen] if chosen else sorted(OPTION_TITLES, key=OPTION_TITLES.get)
    for oid in targets:
        lines.append(f"### {OPTION_TITLES[oid]} 선택 시")
        lines += [f"- [ ] {item}" for item in CHECKLISTS[oid]]
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="매매 의사결정 리포트 — 검증·조립")
    p.add_argument("diagnosis_json")
    p.add_argument("options_json")
    p.add_argument("--chosen", choices=sorted(OPTION_TITLES), default=None, help="사용자가 고른 선택지 (체크리스트 축소)")
    p.add_argument("--out", default="report.md")
    args = p.parse_args()

    diagnosis, diag_raw = load_json(args.diagnosis_json, "진단 결과")
    opts_doc, opts_raw = load_json(args.options_json, "선택지 JSON")
    metrics = diagnosis.get("metrics")
    if not isinstance(metrics, dict):
        fail("SCHEMA_INVALID", ["진단 JSON에 metrics 객체가 없습니다 — diagnose.py 출력을 그대로 넘기세요"])
    options = opts_doc.get("options")
    validate_options(options, metrics)

    report = build_report(metrics, options, args.chosen)
    stamp = hashlib.sha256(diag_raw + opts_raw).hexdigest()[:12]
    report += f"\n---\nreport-id: {stamp}\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"리포트 생성 완료 → {args.out} (report-id: {stamp})")


if __name__ == "__main__":
    main()
