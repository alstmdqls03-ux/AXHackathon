"""trade-decision-report 파이프라인 E2E 테스트 (블랙박스, CLI 호출).

실행 (zip 루트에서): python3 -m unittest discover src/tests -v
표준 라이브러리만 사용 — 프레임워크 설치 불요.
question.md 문항 5의 정상 1종 + 예외 3종과 정합.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills/trade-decision-report"
SCRIPTS = SKILL / "scripts"
SAMPLES = SKILL / "samples"


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True)


class TestDiagnose(unittest.TestCase):
    def test_happy_path_matches_expected_metrics(self):
        r = run("diagnose.py", SAMPLES / "trades.csv", "--price", 160, "--fx", 1380)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m = json.loads(r.stdout)["metrics"]
        expected = json.loads((SAMPLES / "diagnosis.json").read_text())["metrics"]
        self.assertEqual(m, expected)  # 결정론: 재실행해도 전항 일치

    def test_missing_price_asks_instead_of_guessing(self):
        r = run("diagnose.py", SAMPLES / "trades.csv", "--fx", 1380)
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertEqual(out["error"], "REQUIRED_INPUT_MISSING")
        self.assertEqual([m["field"] for m in out["missing"]], ["price"])

    def test_sell_row_rejected_as_out_of_scope(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("date,ticker,side,qty,price_usd,fee_usd,fx_krw_per_usd\n"
                    "2026-05-04,TSLA,SELL,1,180.00,0.25,1350\n")
        r = run("diagnose.py", f.name, "--price", 160, "--fx", 1380)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout)["error"], "UNSUPPORTED_SCOPE")

    def test_invalid_rows_reported_per_line(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("date,ticker,side,qty,price_usd,fee_usd,fx_krw_per_usd\n"
                    "2026-05-04,TSLA,BUY,0,abc,0.25,1350\n")
        r = run("diagnose.py", f.name, "--price", 160, "--fx", 1380)
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertEqual(out["error"], "CSV_INVALID")
        self.assertTrue(any("2행" in row for row in out["rows"]))


class TestFlows(unittest.TestCase):
    # samples/flows.csv 손계산 기대값: 매수 120+80+100+150+50 = 500 (백만 USD) / 매도 90+110+100+70+90 = 460
    FLOW_EXPECTED = {
        "flow_days": 5,
        "flow_from_date": "2026-06-30",
        "flow_to_date": "2026-07-06",
        "flow_buy_usd": 500000000.0,
        "flow_sell_usd": 460000000.0,
        "flow_net_buy_usd": 40000000.0,
    }

    def test_flows_happy_path_metrics_and_report_subsection(self):
        with tempfile.TemporaryDirectory() as d:
            diag = Path(d) / "diagnosis_flows.json"
            r = run("diagnose.py", SAMPLES / "trades.csv", "--price", 160, "--fx", 1380,
                    "--flows", SAMPLES / "flows.csv", "--out", diag)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            m = json.loads(diag.read_text())["metrics"]
            expected = dict(json.loads((SAMPLES / "diagnosis.json").read_text())["metrics"])
            expected.update(self.FLOW_EXPECTED)
            self.assertEqual(m, expected)  # 기존 metrics 불변 + flow_* 6종 전항 일치
            out = Path(d) / "report.md"
            r2 = run("render.py", diag, SAMPLES / "options.sample.json", "--out", out)
            self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
            report = out.read_text()
            self.assertEqual(report, (SAMPLES / "report_flows.md").read_text())  # 동봉 골든과 byte 동일
            self.assertIn("### 국내 투자자 매매동향 (입력 데이터 기준)", report)
            self.assertIn("매수·매도 신호가 아닙니다", report)  # 비신호 고지 하드코딩

    def test_no_flows_backward_compatible_same_report_id(self):
        r = run("diagnose.py", SAMPLES / "trades.csv", "--price", 160, "--fx", 1380)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout),
                         json.loads((SAMPLES / "diagnosis.json").read_text()))  # 미제공 시 무변경
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "report.md"
            r2 = run("render.py", SAMPLES / "diagnosis.json", SAMPLES / "options.sample.json",
                     "--out", out)
            self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
            report = out.read_text()
            # report-id는 입력 해시라 템플릿 변경을 못 잡는다 — 골든 파일 byte 동일성으로 하위 호환을 실증
            self.assertEqual(report, (SAMPLES / "report.md").read_text())
            self.assertIn("report-id: 8d1a510771e6", report)  # 기존 스탬프 불변
            self.assertNotIn("국내 투자자 매매동향", report)  # 서브섹션 없음

    def test_invalid_flows_row_rejected_with_row_numbers(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "flows.csv"
            p.write_text("date,buy_usd,sell_usd\n"
                         "2026-07-01,1000000,500000\n"
                         "2026/07/02,-5,abc\n")
            r = run("diagnose.py", SAMPLES / "trades.csv", "--price", 160, "--fx", 1380,
                    "--flows", p)
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertEqual(out["error"], "CSV_INVALID")
        self.assertIn("flows", out["message"])  # 거래 내역 CSV가 아니라 flows 파일임을 명시
        # 3행의 위반 3종(날짜 형식·음수·숫자 아님)이 각각 보고됨 — 한 필드 오류가 다른 검사를 삼키지 않는다
        self.assertEqual(sum("3행" in row for row in out["rows"]), 3)


class TestRender(unittest.TestCase):
    def test_happy_path_reproduces_stamped_report(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "report.md"
            r = run("render.py", SAMPLES / "diagnosis.json", SAMPLES / "options.sample.json",
                    "--out", out)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            report = out.read_text()
            self.assertIn("report-id: 8d1a510771e6", report)  # verification.md와 동일 스탬프
            self.assertIn("순위·추천을 제시하지 않으며", report)
            for title in ["보유 지속", "부분 매도", "분할 추가 매수", "전량 매도"]:
                self.assertIn(f"### {title}", report)

    def test_violating_options_rejected_and_no_report_written(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "report.md"
            r = run("render.py", SAMPLES / "diagnosis.json", SAMPLES / "options_violation.json",
                    "--out", out)
            self.assertEqual(r.returncode, 1)
            codes = {v["code"] for v in json.loads(r.stdout)["violations"]}
            self.assertIn("RANKING_LANGUAGE_DETECTED", codes)
            self.assertIn("UNGROUNDED_NUMBER", codes)
            self.assertFalse(out.exists())  # 위반 시 리포트 미생성

    def test_ranking_field_in_schema_rejected(self):
        opts = json.loads((SAMPLES / "options.sample.json").read_text())
        opts["options"][0]["rank"] = 1  # 순위 필드 주입
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "opts.json"
            p.write_text(json.dumps(opts, ensure_ascii=False))
            r = run("render.py", SAMPLES / "diagnosis.json", p, "--out", Path(d) / "report.md")
            self.assertEqual(r.returncode, 1)
            self.assertEqual(json.loads(r.stdout)["error"], "SCHEMA_INVALID")


if __name__ == "__main__":
    unittest.main()
