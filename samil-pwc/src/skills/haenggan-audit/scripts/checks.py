#!/usr/bin/env python3
"""행간 감사 — 결정론 교차 대조 체커 (표준 라이브러리만 사용).

역할: 결산 데이터 패키지에서 '이상 후보(candidates)'를 재현 가능하게 계산한다.
판단·해석·보고는 하지 않는다 — 그것은 스킬(SKILL.md)을 따르는 에이전트의 몫.

사용: python3 checks.py <data_dir> [--out findings_candidates.json]
종료 코드: 0 = 정상(후보 유무 무관, 일부 가설군 skip 포함) / 2 = data_dir 없음
가설군은 독립 함수(check_h1/h2/h3) — 축소 시 함수와 HYPOTHESES 항목을 지우면 끝.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

# ── 판단 임계값 (스킬 문서에 공개된 '추론 방향성'의 일부) ────────────────
YOY_SWING_RATIO = 0.5        # 계정 전기 대비 ±50% 이상 변동
YOY_MIN_SCALE = 0.01         # 매출의 1% 미만 계정은 무시
PERIOD_END_FROM = "12-20"    # 기말 전표 스캔 시작일 (12/20 이후, MM-DD)
LARGE_JE_REVENUE_PCT = 0.01  # 연매출의 1% 이상이면 대형 전표
CAPEX_ACCOUNTS = ("유형자산", "무형자산", "건설중인자산")
REPAIR_KEYWORDS = ("수선", "보수", "수리", "정비")
DSO_TREND_RATIO = 1.5        # 3개월 이동평균 DSO가 기초 대비 1.5배 이상
QEND_SPIKE_RATIO = 1.4       # 분기말 월 매출이 분기 내 다른 달 평균의 1.4배 이상
AR_TOP_SHARE = 0.4           # 최대 거래처 채권 비중 40% 이상
AR_OVERDUE61_SHARE = 0.3     # 그 거래처의 61일+ 연체 비중 30% 이상
ALLOC_ALT_DRIVER = "기계가동시간"  # 대안 배부 기준
ALLOC_DELTA_PP = 0.08        # 마진 변화 8%p 이상이면 후보(부호 반전은 무조건)

FILES = {
    "trial_balance": "trial_balance.csv",
    "gl_entries": "gl_entries.csv",
    "monthly_series": "monthly_series.csv",
    "ar_aging": "ar_aging.csv",
    "cost_allocation": "cost_allocation.csv",
}
# 헤더 동의어 (최소한만 — 매핑 실패 시 skip 사유로 보고)
SYNONYMS = {
    "차변": ("차변", "차변액", "차변합계"),
    "대변": ("대변", "대변액", "대변합계"),
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(row, key):
    v = str(row.get(key, "")).replace(",", "").strip()
    return float(v) if v not in ("", "-") else 0.0


def candidate(cid, hypothesis, check, severity_hint, summary, evidence, metrics):
    return {
        "id": cid, "hypothesis": hypothesis, "check": check,
        "severity_hint": severity_hint, "summary": summary,
        "evidence": evidence, "metrics": metrics,
    }


# ── H1: 회계처리 오류 ────────────────────────────────────────────────────
def check_h1(data, out):
    tb, gl = data.get("trial_balance"), data.get("gl_entries")
    revenue = 0.0
    if tb:
        revenue = sum(num(r, "기말잔액") for r in tb if r.get("계정명") == "매출")
        # 1) 계정별 산술 검산: 기말 = 기초 ± (차변-대변)
        for r in tb:
            base, dr, cr, end = (num(r, k) for k in ("기초잔액", "차변합계", "대변합계", "기말잔액"))
            expect = base + (dr - cr) if r.get("정상잔액") == "차변" else base + (cr - dr)
            if abs(expect - end) > 0.5:
                out.append(candidate(
                    f"H1-TB-{r.get('계정코드')}", "H1", "tb_arithmetic", "high",
                    f"{r.get('계정명')} 기말잔액 불일치: 재계산 {expect:,.0f} vs 장부 {end:,.0f}",
                    {"file": FILES["trial_balance"], "계정코드": r.get("계정코드")},
                    {"expected": expect, "reported": end}))
        # 2) 차대 총잔액 균형
        tot_dr = sum(num(r, "기말잔액") for r in tb if r.get("정상잔액") == "차변")
        tot_cr = sum(num(r, "기말잔액") for r in tb if r.get("정상잔액") == "대변")
        if abs(tot_dr - tot_cr) > 0.5:
            out.append(candidate(
                "H1-TB-BAL", "H1", "tb_balance", "high",
                f"시산표 차/대 잔액 불균형: 차변 {tot_dr:,.0f} vs 대변 {tot_cr:,.0f}",
                {"file": FILES["trial_balance"]}, {"debit": tot_dr, "credit": tot_cr}))
        # 3) 전기 대비 급변 계정
        for r in tb:
            cur, prev = num(r, "기말잔액"), num(r, "전기잔액")
            scale = max(abs(cur), abs(prev))
            if prev and scale >= revenue * YOY_MIN_SCALE:
                ratio = (cur - prev) / abs(prev)
                if abs(ratio) >= YOY_SWING_RATIO:
                    out.append(candidate(
                        f"H1-YOY-{r.get('계정코드')}", "H1", "yoy_swing", "medium",
                        f"{r.get('계정명')} 전기 대비 {ratio:+.0%} ({prev:,.0f}→{cur:,.0f})",
                        {"file": FILES["trial_balance"], "계정코드": r.get("계정코드")},
                        {"prev": prev, "cur": cur, "ratio": round(ratio, 3)}))
    if gl:
        large = revenue * LARGE_JE_REVENUE_PCT if revenue else None
        for r in gl:
            je, date, acct = r.get("전표ID"), r.get("일자", ""), r.get("계정명", "")
            amt, memo = num(r, "금액"), r.get("적요", "")
            maker, approver = r.get("작성자", ""), r.get("승인자", "")
            # 4) 기말(12/20 이후) 대형 전표
            if len(date) >= 10 and date[5:10] >= PERIOD_END_FROM:
                if large and amt >= large:
                    out.append(candidate(
                        f"H1-PE-{je}-{r.get('차대')}", "H1", "period_end_large", "medium",
                        f"기말 대형 전표: #{je} {date} {acct} {r.get('차대')} {amt:,.0f} ({memo})",
                        {"file": FILES["gl_entries"], "전표ID": je},
                        {"amount": amt, "threshold": large}))
            # 5) 작성자=승인자
            if maker and maker == approver:
                out.append(candidate(
                    f"H1-SA-{je}-{r.get('차대')}", "H1", "self_approved", "medium",
                    f"작성자=승인자 전표: #{je} {date} {acct} {amt:,.0f} ({maker})",
                    {"file": FILES["gl_entries"], "전표ID": je},
                    {"amount": amt, "person": maker}))
            # 6) 수선성 지출의 자산 계상 패턴
            if r.get("차대") == "차변" and any(a in acct for a in CAPEX_ACCOUNTS) \
                    and any(k in memo for k in REPAIR_KEYWORDS):
                out.append(candidate(
                    f"H1-CAP-{je}", "H1", "capitalization_keyword", "high",
                    f"수선성 적요의 자산 계상: #{je} {date} 차변 {acct} {amt:,.0f} ('{memo}')",
                    {"file": FILES["gl_entries"], "전표ID": je},
                    {"amount": amt, "memo": memo}))


# ── H2: 현금흐름 이상 ────────────────────────────────────────────────────
def check_h2(data, out):
    ms, aging = data.get("monthly_series"), data.get("ar_aging")
    if ms:
        # 1) 이익-현금흐름 괴리 (연속 개월)
        run = best = 0
        months = []
        for r in ms:
            if num(r, "영업이익") > 0 and num(r, "영업활동현금흐름") < 0:
                run += 1
                months.append(r.get("월"))
            else:
                best, run = max(best, run), 0
        best = max(best, run)
        if best >= 2:
            out.append(candidate(
                "H2-DIV", "H2", "profit_cf_divergence", "high",
                f"영업이익 흑자인데 영업현금흐름 음수인 달 {len(months)}개 (최장 연속 {best}개월: {', '.join(months[-best:])})",
                {"file": FILES["monthly_series"], "months": months},
                {"max_consecutive": best}))
        # 2) DSO(3개월 이동평균) 추세
        rows = list(ms)
        if len(rows) >= 6:
            def dso(i):
                win = rows[max(0, i - 2):i + 1]
                avg_sales = sum(num(r, "매출") for r in win) / len(win)
                return num(rows[i], "매출채권잔액") / avg_sales * 30 if avg_sales else 0
            first, last = dso(2), dso(len(rows) - 1)
            if first and last / first >= DSO_TREND_RATIO:
                out.append(candidate(
                    "H2-DSO", "H2", "dso_trend", "high",
                    f"매출채권 회수기간(DSO, 3개월 평균) {first:.0f}일 → {last:.0f}일 ({last / first:.1f}배)",
                    {"file": FILES["monthly_series"]},
                    {"dso_first": round(first, 1), "dso_last": round(last, 1)}))
        # 3) 분기말 매출 스파이크 (밀어내기 신호)
        for i, r in enumerate(rows):
            month = r.get("월", "")
            if month[5:7] in ("03", "06", "09", "12"):
                q = rows[max(0, i - 2):i]
                others = [num(x, "매출") for x in q]
                if others:
                    avg = sum(others) / len(others)
                    ratio = num(r, "매출") / avg if avg else 0
                    if ratio >= QEND_SPIKE_RATIO:
                        out.append(candidate(
                            f"H2-SPK-{month}", "H2", "quarter_end_spike", "medium",
                            f"분기말 매출 스파이크: {month} 매출 {num(r, '매출'):,.0f} = 분기 내 평균의 {ratio:.2f}배",
                            {"file": FILES["monthly_series"], "월": month},
                            {"ratio": round(ratio, 2)}))
    if aging:
        # 4) 거래처 편중 + 장기 연체
        total = sum(num(r, "미회수총액") for r in aging)
        if total:
            top = max(aging, key=lambda r: num(r, "미회수총액"))
            share = num(top, "미회수총액") / total
            overdue61 = num(top, "연체61_90일") + num(top, "연체91일이상")
            ratio61 = overdue61 / num(top, "미회수총액") if num(top, "미회수총액") else 0
            if share >= AR_TOP_SHARE and ratio61 >= AR_OVERDUE61_SHARE:
                out.append(candidate(
                    "H2-CONC", "H2", "ar_concentration", "high",
                    f"채권 편중+장기연체: {top.get('거래처')} 비중 {share:.0%}, 61일+ 연체 {overdue61:,.0f} ({ratio61:.0%})",
                    {"file": FILES["ar_aging"], "거래처": top.get("거래처")},
                    {"share": round(share, 3), "overdue61_ratio": round(ratio61, 3)}))


# ── H3: 원가배분 왜곡 ────────────────────────────────────────────────────
def check_h3(data, out):
    ca = data.get("cost_allocation")
    if not ca:
        return
    total_oh = sum(num(r, "제조간접비배부액") for r in ca)
    alt_total = sum(num(r, ALLOC_ALT_DRIVER) for r in ca)
    if not (total_oh and alt_total):
        return
    for r in ca:
        sales = num(r, "매출액")
        if not sales:
            continue
        margin_cur = num(r, "매출총이익") / sales
        alt_alloc = total_oh * num(r, ALLOC_ALT_DRIVER) / alt_total
        gp_alt = num(r, "매출총이익") + num(r, "제조간접비배부액") - alt_alloc
        margin_alt = gp_alt / sales
        flip = (margin_cur > 0) != (margin_alt > 0)
        delta = margin_alt - margin_cur
        if flip or abs(delta) >= ALLOC_DELTA_PP:
            out.append(candidate(
                f"H3-ALLOC-{r.get('제품')}", "H3", "allocation_sensitivity",
                "high" if flip else "medium",
                f"제품 {r.get('제품')}: 현행({r.get('배부기준')}) 마진 {margin_cur:+.1%} → "
                f"{ALLOC_ALT_DRIVER} 기준 재배부 시 {margin_alt:+.1%}"
                + (" — 부호 반전" if flip else ""),
                {"file": FILES["cost_allocation"], "제품": r.get("제품")},
                {"margin_current": round(margin_cur, 4), "margin_alt": round(margin_alt, 4),
                 "alloc_current": num(r, "제조간접비배부액"), "alloc_alt": round(alt_alloc, 1),
                 "total_overhead": total_oh}))


HYPOTHESES = {
    "H1": (check_h1, ("trial_balance", "gl_entries"), "회계처리 오류"),
    "H2": (check_h2, ("monthly_series",), "현금흐름 이상"),   # ar_aging은 보조(선택)
    "H3": (check_h3, ("cost_allocation",), "원가배분 왜곡"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--out", default="findings_candidates.json")
    args = ap.parse_args()

    root = Path(args.data_dir)
    if not root.is_dir():
        print(f"오류: 데이터 폴더가 없습니다: {root}", file=sys.stderr)
        sys.exit(2)

    data, load_errors = {}, {}
    for key, fname in FILES.items():
        p = root / fname
        if p.exists():
            try:
                data[key] = read_csv(p)
            except Exception as e:  # 파손 파일 → 해당 가설군 skip 사유
                load_errors[key] = f"{fname} 파싱 실패: {e}"
        # 부재는 skip 판정에서 처리

    candidates, skipped = [], []
    for h, (fn, required, label) in HYPOTHESES.items():
        missing = [FILES[k] for k in required if k not in data and k not in load_errors]
        broken = [load_errors[k] for k in required if k in load_errors]
        if missing or broken:
            skipped.append({"hypothesis": h, "label": label,
                            "reason": "필수 파일 부재: " + ", ".join(missing) if missing
                            else "; ".join(broken)})
            continue
        fn(data, candidates)

    candidates.sort(key=lambda c: (c["hypothesis"], c["id"]))
    result = {
        "meta": {"data_dir": str(root), "files_loaded": sorted(data.keys()),
                 "checker_version": "1.0.0"},
        "skipped_hypotheses": skipped,
        "candidates": candidates,
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[checks] 파일 로드: {', '.join(sorted(data.keys())) or '없음'}")
    for s in skipped:
        print(f"[checks] {s['hypothesis']}({s['label']}) 건너뜀 — {s['reason']}")
    print(f"[checks] 이상 후보 {len(candidates)}건 → {args.out}")
    for c in candidates:
        print(f"  - [{c['hypothesis']}/{c['severity_hint']}] {c['id']}: {c['summary']}")


if __name__ == "__main__":
    main()
