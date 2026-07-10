#!/usr/bin/env python3
"""문서 규율 검사 (solution.md §5 제약 4): 공백 주장 (추정) 표기 + 납득 프레임.

- README.md·question.md에서 'I-1'/'I-2'/'로드맵 공백'/'업계 공백'이 있는 줄에 '(추정)'이 없으면 실패.
- README.md에 "정답이 아니라 납득 과정" 프레임 문구가 없으면 실패.
submission.zip 생성 전 체크리스트에서 실행한다.
"""
import sys
from pathlib import Path

GAP_TERMS = ["I-1", "I-2", "로드맵 공백", "업계 공백"]
FRAME = "정답이 아니라 납득 과정"


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    violations = []

    readme = root / "README.md"
    if not readme.exists():
        violations.append("README.md가 없습니다")
    else:
        if FRAME not in readme.read_text(encoding="utf-8"):
            violations.append(f'README.md에 프레임 문구 "{FRAME}"가 없습니다 (S1-9 [01:51])')

    for name in ["README.md", "question.md"]:
        path = root / name
        if not path.exists():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if any(t in line for t in GAP_TERMS) and "(추정)" not in line:
                violations.append(f"{name}:{i} 공백 주장에 (추정) 표기 누락: {line.strip()[:80]}")

    if violations:
        print("문서 규율 위반:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    print("문서 규율 통과: (추정) 표기·납득 프레임 확인")


if __name__ == "__main__":
    main()
