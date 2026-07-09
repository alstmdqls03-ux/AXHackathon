"""checks.py E2E 테스트 — 동봉 데모 데이터 기준 (stdlib unittest만 사용).

실행: python3 -m unittest tests.test_checks -v  (프로젝트 루트에서)
question.md 문항 5의 정상/예외 예시와 정합해야 한다.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKS = ROOT / "src/skills/haenggan-audit/scripts/checks.py"
DEMO = ROOT / "src/skills/haenggan-audit/data/demo"


def run_checks(data_dir, out):
    return subprocess.run(
        [sys.executable, str(CHECKS), str(data_dir), "--out", str(out)],
        capture_output=True, text=True,
    )


class TestChecksE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "out.json"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _copy_demo(self, exclude=()):
        d = self.tmp / "data"
        d.mkdir()
        for f in DEMO.glob("*.csv"):
            if f.name not in exclude:
                shutil.copy(f, d)
        return d

    def test_happy_path_demo_data(self):
        """정상: 데모 데이터 → exit 0, 후보 19건, 심은 문제 3건 신호 포착."""
        r = run_checks(self._copy_demo(), self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(len(result["candidates"]), 19)
        self.assertEqual(result["skipped_hypotheses"], [])
        ids = {c["id"] for c in result["candidates"]}
        self.assertIn("H1-CAP-4712", ids)   # 심은 문제 ① 자본화 의심 전표
        self.assertIn("H2-DSO", ids)        # 심은 문제 ② 현금흐름/DSO
        self.assertIn("H3-ALLOC-B", ids)    # 심은 문제 ③ 원가배분 부호 반전
        # 가설군 3종 모두 후보를 냈는지
        self.assertEqual({c["hypothesis"] for c in result["candidates"]},
                         {"H1", "H2", "H3"})

    def test_missing_file_skips_only_that_hypothesis(self):
        """예외: monthly_series.csv 부재 → H2만 skip, H1·H3 정상, exit 0."""
        r = run_checks(self._copy_demo(exclude=("monthly_series.csv",)), self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(self.out.read_text(encoding="utf-8"))
        skipped = {s["hypothesis"] for s in result["skipped_hypotheses"]}
        self.assertEqual(skipped, {"H2"})
        self.assertIn("필수 파일 부재", result["skipped_hypotheses"][0]["reason"])
        remaining = {c["hypothesis"] for c in result["candidates"]}
        self.assertEqual(remaining, {"H1", "H3"})

    def test_broken_file_skips_with_reason(self):
        """예외: 파싱 불가 파일 → 해당 가설군만 '파싱 실패' 사유로 skip, exit 0."""
        d = self._copy_demo()
        (d / "monthly_series.csv").write_bytes(b"\xff\xfe\x00 garbage \xff")
        r = run_checks(d, self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(self.out.read_text(encoding="utf-8"))
        skipped = {s["hypothesis"] for s in result["skipped_hypotheses"]}
        self.assertEqual(skipped, {"H2"})
        self.assertIn("파싱 실패", result["skipped_hypotheses"][0]["reason"])

    def test_all_files_missing_reports_all_skipped(self):
        """예외: 전 파일 부재 → 가설군 3종 전부 skip 보고, 후보 0건, exit 0."""
        d = self.tmp / "empty"
        d.mkdir()
        r = run_checks(d, self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(result["candidates"], [])
        self.assertEqual({s["hypothesis"] for s in result["skipped_hypotheses"]},
                         {"H1", "H2", "H3"})

    def test_missing_data_dir_exits_2(self):
        """예외: data_dir 자체가 없음 → exit 2, 안내 메시지."""
        r = run_checks(self.tmp / "no-such-dir", self.out)
        self.assertEqual(r.returncode, 2)
        self.assertIn("데이터 폴더가 없습니다", r.stderr)


if __name__ == "__main__":
    unittest.main()
