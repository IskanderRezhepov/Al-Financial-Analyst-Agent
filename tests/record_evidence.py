"""Preserve real public test outputs and checksum the downloaded tutorial reference."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    evidence = root / "evidence"
    evidence.mkdir(exist_ok=True)
    for ticker in ("AAPL", "MSFT"):
        original = root / "outputs" / f"{ticker}-analysis.json"
        report = json.loads(original.read_text(encoding="utf-8"))
        assert report["analysis_status"] == "complete"
        assert len(report["selected_summary_signals"]) >= 3
        for index in range(1, 9):
            assert f"## {index}." in report["analysis"]
        (evidence / original.name).write_bytes(original.read_bytes())
        (evidence / f"{ticker}-report.md").write_text(
            f"# {ticker} — dated example report\n\nGenerated UTC: {report['generated_at_utc']}\n\n"
            "Source records and exact values are in the adjacent JSON file.\n\n" + report["analysis"],
            encoding="utf-8",
        )
    reference = root / "tutorial_reference"
    files = sorted(path for directory in ("backend", "frontend")
                   for path in (reference / directory).rglob("*") if path.is_file())
    checksums = [hashlib.sha256(path.read_bytes()).hexdigest() + "  " +
                 path.relative_to(reference).as_posix() for path in files]
    (reference / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    assert len(list((root / "screenshots").glob("*.png"))) == 8
    print("Preserved two real, complete reports; eight screenshots; tutorial source checksums.")


if __name__ == "__main__":
    main()
