#!/usr/bin/env python3
"""resolution-lift 파이프라인 E2E 테스트 (stdlib만 사용).

실행: python3 tests/test_pipeline.py
전제: src/examples/*.csv 와 out/{gaps,faq_draft,simulation}.json (검증 세션 산출물)
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOAD = ROOT / "src/scripts/load.py"
SIM = ROOT / "src/scripts/simulate.py"
TICKETS = ROOT / "src/examples/tickets.csv"
FAQ = ROOT / "src/examples/faq.csv"
LLM_ARTIFACTS = ["gaps.json", "faq_draft.json", "simulation.json"]


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)],
                          capture_output=True, text=True)


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rl-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def load_ok(self):
        r = run(LOAD, TICKETS, FAQ, "--out", self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def copy_llm_artifacts(self):
        for name in LLM_ARTIFACTS:
            shutil.copy(ROOT / "out" / name, self.tmp / name)

    # ---- 정상 경로
    def test_happy_path_end_to_end(self):
        self.load_ok()
        summary = json.loads((self.tmp / "summary.json").read_text())
        self.assertEqual(summary["total"], 60)
        self.assertEqual(summary["unresolved"], 27)
        self.copy_llm_artifacts()
        r = run(SIM, self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in ["gap-report.md", "faq-draft.md", "validation-report.md", "report.html"]:
            self.assertTrue((self.tmp / f).exists(), f)
        self.assertIn("55.0% → 85.0%", r.stdout)  # question.md 문항 5와 정합

    # ---- load.py 예외 경로
    def test_missing_required_column_halts_with_template(self):
        bad = self.tmp / "bad.csv"
        bad.write_text("ticket_id,answer\nT-1,x\n", encoding="utf-8")
        r = run(LOAD, bad, FAQ, "--out", self.tmp / "o")
        self.assertEqual(r.returncode, 1)
        self.assertIn("필수 컬럼", r.stderr)
        self.assertIn("ticket_id,created_at,question", r.stderr)  # 템플릿 안내
        self.assertFalse((self.tmp / "o" / "summary.json").exists())  # 짐작 진행 없음

    def test_non_utf8_csv_halts_with_guidance(self):
        bad = self.tmp / "cp949.csv"
        bad.write_bytes(TICKETS.read_text(encoding="utf-8").encode("cp949"))
        r = run(LOAD, bad, FAQ, "--out", self.tmp / "o")
        self.assertEqual(r.returncode, 1)
        self.assertIn("UTF-8", r.stderr)

    def test_pii_masking_covers_rrn_card_phone_email(self):
        csvp = self.tmp / "pii.csv"
        csvp.write_text(
            'ticket_id,question,resolved,agent_answer\n'
            'T-1,"주민 900101-1234567 이메일 a@b.com",false,'
            '"카드 1234-5678-9012-3456 연락 010-1234-5678"\n', encoding="utf-8")
        r = run(LOAD, csvp, FAQ, "--out", self.tmp / "p")
        self.assertEqual(r.returncode, 0, r.stderr)
        raw = (self.tmp / "p" / "unresolved.json").read_text()
        for leak in ["900101-1234567", "1234-5678-9012-3456", "010-1234-5678", "a@b.com"]:
            self.assertNotIn(leak, raw)

    # ---- simulate.py 예외 경로
    def test_hallucinated_ticket_id_rejected(self):
        self.load_ok()
        self.copy_llm_artifacts()
        sims = json.loads((self.tmp / "simulation.json").read_text())
        sims[0]["ticket_id"] = "T-9999"  # 미해결 로그에 없는 ID
        (self.tmp / "simulation.json").write_text(json.dumps(sims, ensure_ascii=False))
        r = run(SIM, self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("환각", r.stderr)
        self.assertFalse((self.tmp / "gap-report.md").exists())  # 리포트 생성 거부

    def test_tampered_summary_rejected(self):
        self.load_ok()
        self.copy_llm_artifacts()
        summary = json.loads((self.tmp / "summary.json").read_text())
        summary["total"] = 0
        (self.tmp / "summary.json").write_text(json.dumps(summary))
        r = run(SIM, self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("summary.json", r.stderr)

    def test_pipe_and_newline_in_llm_text_escaped(self):
        self.load_ok()
        self.copy_llm_artifacts()
        gaps = json.loads((self.tmp / "gaps.json").read_text())
        gaps[0]["rationale"] = "파이프|와\n줄바꿈"
        (self.tmp / "gaps.json").write_text(json.dumps(gaps, ensure_ascii=False))
        r = run(SIM, self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        report = (self.tmp / "gap-report.md").read_text()
        self.assertIn("파이프\\|와 줄바꿈", report)  # 표가 깨지지 않음


if __name__ == "__main__":
    unittest.main(verbosity=2)
