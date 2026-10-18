"""Create a reviewable Moodle ZIP using an explicit allowlist; never package secrets."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
ROOT_FILES = ["README.md", "SUBMISSION_CHECKLIST.md", ".env.example", ".gitignore",
              "requirements.txt", "requirements-lock.txt", "tutorial-constraints.txt", "start.ps1",
              "package_submission.py"]
FRONTEND_FILES = ["package.json", "package-lock.json", "index.html", "vite.config.ts",
                  "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json", "eslint.config.js"]
DIRECTORIES = ["backend", "frontend/src", "tests", "tutorial_reference", "screenshots", "evidence"]


def main():
    files = [ROOT / value for value in ROOT_FILES]
    files.extend(ROOT / "frontend" / value for value in FRONTEND_FILES)
    for directory in DIRECTORIES:
        files.extend(path for path in (ROOT / directory).rglob("*") if path.is_file())
    files = sorted(set(path for path in files if path.is_file() and not any(
        part in {"__pycache__", "node_modules", ".pytest_cache", ".git", ".venv"}
        for part in path.relative_to(ROOT).parts
    ) and path.suffix not in {".pyc", ".log"}))
    for path in files:
        relative = path.relative_to(ROOT)
        if path.name == ".env" or path.name.endswith(".env") or path.name == "secrets.toml":
            raise RuntimeError(f"Refusing credential file: {relative}")
    with ZipFile(ROOT / "submission.zip", "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "AI-Financial-Analyst-Agent/" + path.relative_to(ROOT).as_posix())
    with ZipFile(ROOT / "submission.zip") as archive:
        assert archive.testzip() is None
        print(f"Created submission.zip: {len(archive.namelist())} files; "
              f"{(ROOT / 'submission.zip').stat().st_size:,} bytes; no credentials, dependencies or caches.")


if __name__ == "__main__":
    main()
