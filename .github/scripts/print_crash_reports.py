"""Temporary diagnostic: print the faulting thread of each macOS crash report (.ips).

macOS writes one report per crashed process to ~/Library/Logs/DiagnosticReports. An .ips
file is a JSON header line followed by a JSON body; the body names the faulting thread and
lists its frames with the library and symbol of each.
"""

import json
import sys
from pathlib import Path

REPORTS = Path.home() / "Library" / "Logs" / "DiagnosticReports"
MAX_FRAMES = 40


def describe(report: Path) -> None:
    print(f"\n===== {report.name} =====")
    try:
        _, body = report.read_text(encoding="utf-8", errors="replace").split("\n", 1)
        data = json.loads(body)
    except (ValueError, OSError) as exc:
        print(f"(unreadable: {exc})")
        return
    exception = data.get("exception", {})
    print("exception:", exception.get("type"), exception.get("signal"), exception.get("subtype", ""))
    images = data.get("usedImages", [])
    index = data.get("faultingThread", 0)
    thread = (data.get("threads") or [{}])[index]
    print(f"faulting thread {index}: {thread.get('name') or thread.get('queue') or ''}")
    for number, frame in enumerate(thread.get("frames", [])[:MAX_FRAMES]):
        image = images[frame["imageIndex"]] if frame.get("imageIndex", -1) < len(images) else {}
        name = image.get("name") or Path(image.get("path", "?")).name
        print(f"  #{number:<2} {name:<28} {frame.get('symbol', '?')}+{frame.get('symbolLocation', 0)}")


def main() -> None:
    reports = sorted(REPORTS.glob("*.ips")) if REPORTS.is_dir() else []
    if not reports:
        print(f"no crash reports in {REPORTS}")
    for report in reports:
        describe(report)


if __name__ == "__main__":
    main()
    sys.exit(0)
