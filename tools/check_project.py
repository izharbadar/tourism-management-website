from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from jinja2 import Environment


ROOT = Path(__file__).resolve().parent.parent


def check_python() -> int:
    files = list((ROOT / "capture_pakistan").rglob("*.py"))
    files += [ROOT / "run.py", ROOT / "wsgi.py"]

    for path in files:
        ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

    return len(files)


def check_templates() -> int:
    environment = Environment()
    files = list((ROOT / "templates").rglob("*.html"))

    for path in files:
        environment.parse(path.read_text(encoding="utf-8"))

    return len(files)


def check_required_files() -> int:
    required = [
        ROOT / ".env.example",
        ROOT / "requirements.txt",
        ROOT / "wsgi.py",
        ROOT / "templates/public/_seo_meta.html",
        ROOT / "templates/public/_site_footer.html",
        ROOT / "static/documents/capture-pakistan-company-profile.pdf",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.exists()
    ]

    if missing:
        raise RuntimeError(
            "Missing required files: " + ", ".join(missing)
        )

    return len(required)


def check_static_references() -> int:
    pattern = re.compile(
        r"url_for\(\s*['\"]static['\"]\s*,\s*"
        r"filename\s*=\s*['\"]([^'\"]+)['\"]"
    )
    missing = []
    checked = set()

    for root in (ROOT / "templates", ROOT / "capture_pakistan"):
        for path in root.rglob("*"):
            if path.suffix not in {".html", ".py"}:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            for match in pattern.finditer(content):
                relative = match.group(1)
                if relative in checked:
                    continue
                checked.add(relative)
                if not (ROOT / "static" / relative).exists():
                    missing.append(relative)

    if missing:
        raise RuntimeError(
            "Missing statically referenced assets: "
            + ", ".join(sorted(missing))
        )

    return len(checked)


def check_no_sensitive_files() -> int:
    forbidden = [
        ROOT / ".env",
        ROOT / ".venv",
        ROOT / "venv",
    ]

    present = [
        str(path.relative_to(ROOT))
        for path in forbidden
        if path.exists()
    ]

    if present:
        raise RuntimeError(
            "Sensitive or machine-specific files are present: "
            + ", ".join(present)
        )

    return len(forbidden)


def main() -> None:
    python_count = check_python()
    template_count = check_templates()
    required_count = check_required_files()
    static_count = check_static_references()
    sensitive_count = check_no_sensitive_files()

    print(f"Python syntax: {python_count} files passed")
    print(f"Jinja syntax: {template_count} files passed")
    print(f"Required files: {required_count} files present")
    print(f"Static references: {static_count} assets present")
    print(f"Sensitive-file checks: {sensitive_count} checks passed")
    print("Project structure checks passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Project check failed: {error}", file=sys.stderr)
        raise
