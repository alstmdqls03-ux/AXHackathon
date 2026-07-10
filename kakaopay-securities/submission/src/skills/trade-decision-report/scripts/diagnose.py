#!/usr/bin/env python3
"""결정론 진단: 거래 내역 CSV + 현재가·환율 → 실질 손익 metrics JSON.

리포트의 모든 숫자는 이 스크립트의 산출물이어야 한다 (solution.md §5 제약 2).
표준 라이브러리만 사용. 시세·뉴스 조회 없음 — 모든 수치는 입력에서 유도된다.
"""
import argparse
import csv
import datetime
import json
import math
import sys

CSV_HEADERS = ["date", "ticker", "side", "qty", "price_usd", "fee_usd", "fx_krw_per_usd"]
FLOWS_HEADERS = ["date", "buy_usd", "sell_usd"]


def fail(code, message, **extra):
    print(json.dumps({"error": code, "message": message, **extra}, ensure_ascii=False, indent=2))
    sys.exit(1)


def hafz(x, ndigits=0):
    """half-away-from-zero 반올림 (plan.md 수치 규칙 — 파이썬 기본 banker's rounding 회피)."""
    m = 10 ** ndigits
    return math.copysign(math.floor(abs(x) * m + 0.5), x) / m


def krw(x):
    return int(hafz(x, 0))


def pct(x):
    return hafz(x, 2)


def read_trades(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        fail("CSV_INVALID", f"거래 내역 파일을 찾을 수 없습니다: {path}")
    if not rows:
        fail("CSV_INVALID", "거래 내역이 비어 있습니다 — 최소 1건의 매수 행이 필요합니다.")
    if set(rows[0].keys()) != set(CSV_HEADERS):
        fail("CSV_INVALID", f"CSV 헤더가 다릅니다. 필요한 헤더: {','.join(CSV_HEADERS)}")

    errors = []
    trades = []
    for i, row in enumerate(rows, start=2):  # 헤더가 1행
        side = (row["side"] or "").strip().upper()
        if side == "SELL":
            fail("UNSUPPORTED_SCOPE",
                 f"{i}행: SELL 내역은 데모 범위 밖입니다 — 이 데모는 매수(BUY) 내역 기반 보유 포지션만 다룹니다.")
        if side != "BUY":
            errors.append(f"{i}행: side는 BUY여야 합니다 (입력: {row['side']!r})")
            continue
        try:
            qty = float(row["qty"])
            price = float(row["price_usd"])
            fee = float(row["fee_usd"])
            fx = float(row["fx_krw_per_usd"])
        except (TypeError, ValueError):
            errors.append(f"{i}행: qty/price_usd/fee_usd/fx_krw_per_usd는 숫자여야 합니다")
            continue
        if qty <= 0:
            errors.append(f"{i}행: qty는 0보다 커야 합니다 (입력: {row['qty']})")
        if price <= 0:
            errors.append(f"{i}행: price_usd는 0보다 커야 합니다 (입력: {row['price_usd']})")
        if fee < 0:
            errors.append(f"{i}행: fee_usd는 음수일 수 없습니다 (입력: {row['fee_usd']})")
        if fx <= 0:
            errors.append(f"{i}행: fx_krw_per_usd는 0보다 커야 합니다 (입력: {row['fx_krw_per_usd']})")
        trades.append({"ticker": (row["ticker"] or "").strip().upper(),
                       "qty": qty, "price": price, "fee": fee, "fx": fx})
    if errors:
        fail("CSV_INVALID", "거래 내역에 잘못된 행이 있습니다.", rows=errors)

    tickers = {t["ticker"] for t in trades}
    if len(tickers) != 1:
        fail("UNSUPPORTED_SCOPE",
             f"복수 종목({', '.join(sorted(tickers))})은 데모 범위 밖입니다 — 단일 종목 CSV로 나눠 실행하세요.")
    return trades


def read_flows(path):
    """매매동향(flows) CSV → flow_* metrics. 오류 메시지는 거래 내역 CSV와 혼동하지 않도록 flows 파일임을 명시한다."""
    try:
        # utf-8-sig: 엑셀 저장 파일의 BOM 허용 (사용자가 직접 만드는 파일이라 실제로 발생)
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            rows = list(reader)
    except OSError as e:
        fail("CSV_INVALID", f"매매동향(flows) 파일을 열 수 없습니다: {path} ({e})")
    except (UnicodeDecodeError, csv.Error) as e:
        fail("CSV_INVALID", f"매매동향(flows) 파일을 읽을 수 없습니다 — UTF-8 CSV여야 합니다: {path} ({e})")
    # list 비교: 중복·순서 어긋난 열까지 거부 (set 비교는 중복 열을 통과시켜 합계가 조용히 틀어진다)
    if header != FLOWS_HEADERS:
        fail("CSV_INVALID", f"매매동향(flows) CSV 헤더가 다릅니다: {path} — 필요한 헤더: {','.join(FLOWS_HEADERS)}")
    if not rows:
        fail("CSV_INVALID", f"매매동향(flows) CSV가 비어 있습니다: {path} — 최소 1행이 필요합니다.")

    errors = []
    dates = []
    seen = set()
    buy_total = sell_total = 0.0
    for i, row in enumerate(rows, start=2):  # 헤더가 1행
        if None in row:  # 헤더보다 많은 열 — DictReader가 잉여 값을 None 키에 몬다
            errors.append(f"{i}행: 열 개수가 헤더({len(FLOWS_HEADERS)}개)보다 많습니다")
            continue
        date = (row["date"] or "").strip()
        try:
            datetime.date.fromisoformat(date)  # 형식+실존 날짜 검증 (2026-99-99 거부)
        except ValueError:
            errors.append(f"{i}행: date는 YYYY-MM-DD 형식의 실존 날짜여야 합니다 (입력: {row['date']!r})")
        else:
            if date in seen:
                errors.append(f"{i}행: 중복 날짜입니다 (입력: {date})")
            else:
                seen.add(date)
                dates.append(date)
        amounts = {}
        for field in ("buy_usd", "sell_usd"):
            raw = row[field]
            try:
                val = float(raw)
            except (TypeError, ValueError):
                errors.append(f"{i}행: {field}는 숫자여야 합니다 (입력: {raw!r})")
                continue
            if not math.isfinite(val):
                errors.append(f"{i}행: {field}는 유한한 숫자여야 합니다 (입력: {raw!r})")
            elif val < 0:
                errors.append(f"{i}행: {field}는 음수일 수 없습니다 (입력: {raw!r})")
            else:
                amounts[field] = val
        if len(amounts) == 2:
            buy_total += amounts["buy_usd"]
            sell_total += amounts["sell_usd"]
    if errors:
        fail("CSV_INVALID", f"매매동향(flows) CSV에 잘못된 행이 있습니다: {path}", rows=errors)
    if not (math.isfinite(buy_total) and math.isfinite(sell_total)):
        fail("CSV_INVALID", f"매매동향(flows) 금액 합계가 표현 범위를 넘습니다: {path}")

    return {
        "flow_days": len(dates),
        "flow_from_date": min(dates),
        "flow_to_date": max(dates),
        "flow_buy_usd": hafz(buy_total, 2),
        "flow_sell_usd": hafz(sell_total, 2),
        "flow_net_buy_usd": hafz(buy_total - sell_total, 2),
    }


def main():
    p = argparse.ArgumentParser(description="매매 의사결정 리포트 — 결정론 진단")
    p.add_argument("trades_csv")
    p.add_argument("--price", type=float, default=None, help="현재가 (USD)")
    p.add_argument("--fx", type=float, default=None, help="현재 환율 (KRW/USD)")
    p.add_argument("--sell-fee-rate", type=float, default=0.0007, help="매도 수수료율 (기본 0.07%%)")
    p.add_argument("--flows", default=None,
                   help="(선택) 매매동향 CSV — 헤더 date,buy_usd,sell_usd (국내 투자자 매수·매도 결제액, USD)")
    p.add_argument("--out", default=None, help="출력 파일 (기본: stdout)")
    args = p.parse_args()

    missing = [("price", "현재 주가 없이는 손익을 계산할 수 없습니다"),
               ("fx", "현재 환율 없이는 원화 환산 손익을 계산할 수 없습니다")]
    missing = [(k, why) for k, why in missing if getattr(args, k) is None]
    if missing:
        fail("REQUIRED_INPUT_MISSING",
             "필수 입력이 없습니다. 사용자에게 아래 값을 물어보세요 — 임의 추정값을 넣지 마세요.",
             missing=[{"field": k, "why": why} for k, why in missing])
    if args.price <= 0 or args.fx <= 0:
        fail("REQUIRED_INPUT_MISSING", "price와 fx는 0보다 커야 합니다.")

    trades = read_trades(args.trades_csv)

    qty = sum(t["qty"] for t in trades)
    invested_usd = sum(t["qty"] * t["price"] + t["fee"] for t in trades)          # 매수 수수료 포함
    invested_krw = sum((t["qty"] * t["price"] + t["fee"]) * t["fx"] for t in trades)
    gross_usd = sum(t["qty"] * t["price"] for t in trades)                        # 가격만
    avg_buy_fx = invested_krw / invested_usd
    value_now_usd = qty * args.price
    value_now_krw = value_now_usd * args.fx

    true_usd = (value_now_usd - invested_usd) / invested_usd * 100
    true_krw = (value_now_krw - invested_krw) / invested_krw * 100

    sell_fee_usd = value_now_usd * args.sell_fee_rate
    proceeds_krw = (value_now_usd - sell_fee_usd) * args.fx
    realized_if_sell = proceeds_krw - invested_krw
    # 해외주식 양도세 단순화: 연간 기본공제 250만 원 초과 이익의 22% (손실이면 0) — 한계는 README 참조
    tax_if_sell = max(0.0, (realized_if_sell - 2_500_000)) * 0.22

    metrics = {
        "ticker": trades[0]["ticker"],
        "qty": hafz(qty, 4),
        "price_now_usd": hafz(args.price, 2),
        "fx_now": hafz(args.fx, 2),
        "avg_price_usd": hafz(gross_usd / qty, 2),
        "avg_cost_usd": hafz(invested_usd / qty, 2),
        "avg_buy_fx": hafz(avg_buy_fx, 1),
        "invested_usd": hafz(invested_usd, 2),
        "invested_krw": krw(invested_krw),
        "value_now_usd": hafz(value_now_usd, 2),
        "value_now_krw": krw(value_now_krw),
        "nominal_return_usd_pct": pct((args.price - gross_usd / qty) / (gross_usd / qty) * 100),
        "true_return_usd_pct": pct(true_usd),
        "true_return_krw_pct": pct(true_krw),
        "fx_effect_pp": pct(true_krw - true_usd),
        "unrealized_pnl_krw": krw(value_now_krw - invested_krw),
        "sell_fee_usd": hafz(sell_fee_usd, 2),
        "realized_loss_if_sell_krw": krw(realized_if_sell),  # 음수=손실, 양수=이익
        "tax_if_sell_krw": krw(tax_if_sell),
    }
    if args.flows is not None:  # 미제공 시 기존 산출물과 byte-identical ('--flows ""'는 조용히 무시하지 않고 열기 오류로 보고)
        metrics.update(read_flows(args.flows))
    out = json.dumps({"metrics": metrics}, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print(f"진단 완료 → {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
