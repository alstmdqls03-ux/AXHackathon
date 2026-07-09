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
