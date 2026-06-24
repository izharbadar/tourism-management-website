from pathlib import Path
import ast
import re
import stat
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Audit:
    def __init__(self):
        self.passed = 0
        self.warnings = 0
        self.failed = 0

    def pass_item(self, message):
        self.passed += 1
        print("[PASS] " + message)

    def warn_item(self, message):
        self.warnings += 1
        print("[WARN] " + message)

    def fail_item(self, message):
        self.failed += 1
        print("[FAIL] " + message)


def file_contains(path, needle):
    return (
        path.exists()
        and needle
        in path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    )


def audit_dependencies(audit):
    requirements = PROJECT_ROOT / "requirements.txt"
    content = requirements.read_text(
        encoding="utf-8",
        errors="ignore",
    ).lower()

    for dependency in [
        "flask-wtf",
        "flask-limiter",
    ]:
        if dependency in content:
            audit.pass_item(
                dependency + " is listed in requirements.txt"
            )
        else:
            audit.fail_item(
                dependency + " is missing from requirements.txt"
            )


def audit_configuration(audit):
    config_path = (
        PROJECT_ROOT
        / "capture_pakistan"
        / "config.py"
    )

    required = [
        "SESSION_COOKIE_HTTPONLY",
        "SESSION_COOKIE_SAMESITE",
        "WTF_CSRF_ENABLED",
        "MAX_FORM_PARTS",
        "RATELIMIT_STORAGE_URI",
        "TRUSTED_HOSTS",
    ]

    for item in required:
        if file_contains(config_path, item):
            audit.pass_item(
                item + " is configured"
            )
        else:
            audit.fail_item(
                item + " is not configured"
            )

    run_path = PROJECT_ROOT / "run.py"

    if file_contains(run_path, "debug=True"):
        audit.fail_item(
            "run.py still hardcodes debug=True"
        )
    else:
        audit.pass_item(
            "run.py does not hardcode debug=True"
        )


def audit_env(audit):
    env_path = PROJECT_ROOT / ".env"

    if not env_path.exists():
        audit.warn_item(".env is intentionally not bundled; create it from .env.example before launch")

        gitignore = PROJECT_ROOT / ".gitignore"
        if file_contains(gitignore, ".env"):
            audit.pass_item(".env is excluded by .gitignore")
        else:
            audit.fail_item(".env is not excluded by .gitignore")
        return

    content = env_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    match = re.search(
        r"(?m)^SECRET_KEY=(.*)$",
        content,
    )

    if match and len(match.group(1).strip()) >= 32:
        audit.pass_item(
            "SECRET_KEY is present and sufficiently long"
        )
    else:
        audit.fail_item(
            "SECRET_KEY is missing or too short"
        )

    try:
        mode = stat.S_IMODE(
            env_path.stat().st_mode
        )

        if mode & 0o077:
            audit.warn_item(
                ".env permissions are broader than 600"
            )
        else:
            audit.pass_item(
                ".env permissions restrict other users"
            )
    except OSError:
        audit.warn_item(
            ".env file permissions could not be checked"
        )

    gitignore = PROJECT_ROOT / ".gitignore"

    if file_contains(gitignore, ".env"):
        audit.pass_item(
            ".env is excluded by .gitignore"
        )
    else:
        audit.fail_item(
            ".env is not excluded by .gitignore"
        )


def audit_csrf_forms(audit):
    form_pattern = re.compile(
        r"(?P<open><form\b[^>]*>)"
        r"(?P<body>[\s\S]*?)"
        r"</form>",
        flags=re.IGNORECASE,
    )

    missing = []
    total_protected = 0

    for path in (PROJECT_ROOT / "templates").rglob("*.html"):
        relative = path.relative_to(
            PROJECT_ROOT / "templates"
        )

        if relative.parts and relative.parts[0] in {
            "emails",
            "errors",
        }:
            continue

        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for match in form_pattern.finditer(content):
            opening = match.group("open")
            body = match.group("body")
            method_match = re.search(
                r"method\s*=\s*['\"]?([^'\"\s>]+)",
                opening,
                flags=re.IGNORECASE,
            )
            method = (
                method_match.group(1).upper()
                if method_match
                else "GET"
            )

            if method not in {
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            }:
                continue

            if "csrf_token" in body:
                total_protected += 1
            else:
                line = (
                    content[: match.start()]
                    .count("\n")
                    + 1
                )
                missing.append(
                    f"{relative}:{line}"
                )

    if missing:
        audit.fail_item(
            "POST forms missing CSRF tokens: "
            + ", ".join(missing[:10])
        )
    else:
        audit.pass_item(
            f"All {total_protected} unsafe HTML forms have CSRF tokens"
        )


def decorator_name(node):
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return (
            decorator_name(node.value)
            + "."
            + node.attr
        )

    if isinstance(node, ast.Call):
        return decorator_name(node.func)

    return ""


def audit_admin_routes(audit):
    admin_root = (
        PROJECT_ROOT
        / "capture_pakistan"
        / "blueprints"
        / "admin"
    )

    missing = []
    route_count = 0

    for path in admin_root.glob("*.py"):
        if path.name in {
            "__init__.py",
            "decorators.py",
        }:
            continue

        try:
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except SyntaxError:
            audit.fail_item(
                f"Could not parse {path.name}"
            )
            continue

        for node in tree.body:
            if not isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue

            decorators = [
                decorator_name(item)
                for item in node.decorator_list
            ]

            is_route = any(
                name.endswith("admin_bp.route")
                or name.endswith("admin_bp.get")
                or name.endswith("admin_bp.post")
                for name in decorators
            )

            if not is_route:
                continue

            route_count += 1

            if not any(
                name.endswith("admin_required")
                for name in decorators
            ):
                missing.append(
                    f"{path.name}:{node.lineno}:{node.name}"
                )

    if missing:
        audit.fail_item(
            "Admin routes missing @admin_required: "
            + ", ".join(missing)
        )
    else:
        audit.pass_item(
            f"All {route_count} admin routes use @admin_required"
        )


def audit_security_files(audit):
    checks = {
        "security service": (
            PROJECT_ROOT
            / "capture_pakistan"
            / "security.py"
        ),
        "CSRF browser helper": (
            PROJECT_ROOT
            / "static"
            / "js"
            / "security-csrf.js"
        ),
        "security error template": (
            PROJECT_ROOT
            / "templates"
            / "errors"
            / "security_error.html"
        ),
    }

    for name, path in checks.items():
        if path.exists():
            audit.pass_item(name + " exists")
        else:
            audit.fail_item(name + " is missing")

    app_factory = (
        PROJECT_ROOT
        / "capture_pakistan"
        / "__init__.py"
    )

    for item in [
        "csrf.init_app(app)",
        "limiter.init_app(app)",
        "register_security(app)",
    ]:
        if file_contains(app_factory, item):
            audit.pass_item(item + " is registered")
        else:
            audit.fail_item(item + " is not registered")


def audit_test_routes(audit):
    forbidden_routes = {
        "/auth-test",
        "/structure-test",
        "/booking-model-test",
        "/gallery-model-test",
        "/inquiry-model-test",
    }
    found = []

    route_pattern = re.compile(
        r"@[^\n]+(?:route|get|post)\(\s*['\"]([^'\"]+)['\"]"
    )

    for path in (PROJECT_ROOT / "capture_pakistan").rglob("*.py"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        for route in route_pattern.findall(content):
            if route in forbidden_routes:
                found.append(f"{path.name}:{route}")

    if found:
        audit.fail_item(
            "Development test routes are registered: " + ", ".join(found)
        )
    else:
        audit.pass_item("No development test routes are registered")


def main():
    audit = Audit()

    print("Capture Pakistan Security Phase 1 Audit")
    print("=" * 42)

    audit_dependencies(audit)
    audit_configuration(audit)
    audit_env(audit)
    audit_security_files(audit)
    audit_csrf_forms(audit)
    audit_admin_routes(audit)
    audit_test_routes(audit)

    print("\nSummary")
    print("- Passed:", audit.passed)
    print("- Warnings:", audit.warnings)
    print("- Failed:", audit.failed)

    if audit.failed:
        print(
            "\nSecurity audit found items that need attention."
        )
        sys.exit(1)

    print(
        "\nSecurity Phase 1 audit passed."
    )


if __name__ == "__main__":
    main()
