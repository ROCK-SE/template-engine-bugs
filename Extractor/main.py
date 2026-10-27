"""Command-line extraction of selected template files or template directories."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import TemplateSyntaxError

from .analyzer import EXTRACTOR_VERSION, analyze_template

OUTPUT_ROOT = Path(__file__).resolve().parents[2] / "outputs"

TEMPLATE_SUFFIXES = {
    ".j2", ".jinja", ".jinja2", ".html", ".htm", ".sql", ".msql",
    ".macro", ".macros", ".txt", ".xml", ".svg", ".yaml", ".yml", ".json",
}


def read_jinja2_template(file_path):
    """Read a UTF-8 template; preserve the read exception for the run report."""
    return Path(file_path).read_text(encoding="utf-8")


def process_directory(input_directory, output_directory, *, dialect="auto",
                      suffixes=None, recursive=True):
    """Analyze a file or directory and keep every failure in a structured report.

    Output must be a new directory. Relative paths and the original extension
    are preserved before the .json suffix, preventing basename collisions.
    This function consumes selected templates; it is not a repository inventory.
    """
    source_root, output = Path(input_directory).resolve(), Path(output_directory).resolve()
    if not source_root.exists():
        raise FileNotFoundError(source_root)
    if output.exists():
        raise FileExistsError(f"Choose a new output directory: {output}")
    allowed = TEMPLATE_SUFFIXES if suffixes is None else set(suffixes)
    if source_root.is_file():
        paths, base = [source_root], source_root.parent
    else:
        base = source_root
        paths = sorted(
            p for p in (base.rglob("*") if recursive else base.glob("*"))
            if p.is_file() and p.suffix.lower() in allowed
            and ".git" not in p.parts and "node_modules" not in p.parts
            and not p.is_relative_to(output)
        )
    output.mkdir(parents=True)
    records = []
    for path in paths:
        relative = path.relative_to(base)
        stage = "read"
        try:
            source = read_jinja2_template(path)
            stage = "extract"
            prediction = analyze_template(source, dialect=dialect, name=str(relative))
            destination = output / relative.parent / (relative.name + ".json")
            record = {"source": relative.as_posix(), "status": "success",
                      "output": destination.relative_to(output).as_posix()}
            value = prediction
        except Exception as exc:
            status = ("parse_failure" if isinstance(exc, TemplateSyntaxError)
                      else "read_failure" if stage == "read" else "extraction_failure")
            destination = output / relative.parent / (relative.name + ".error.json")
            record = {
                "source": relative.as_posix(), "status": status,
                "output": destination.relative_to(output).as_posix(),
                "error": {"type": type(exc).__name__, "message": str(exc),
                          "line": getattr(exc, "lineno", None)},
            }
            value = record
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        records.append(record)
        print(f"[{record['status']}] {relative.as_posix()}")
    summary = {
        "input": str(source_root), "dialect": dialect, "processed": len(records),
        "success": sum(r["status"] == "success" for r in records),
        "failed": sum(r["status"] != "success" for r in records),
        "records": records,
    }
    (output / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Selected template file or template directory")
    parser.add_argument("--output", "-o", type=Path, help="New result directory (default: workspace outputs/)")
    parser.add_argument("--dialect", choices=["auto", "jinja", "dbt"], default="auto")
    parser.add_argument("--suffix", action="append", help="Limit directory inputs, e.g. --suffix .sql")
    parser.add_argument("--no-recursive", action="store_true")
    args = parser.parse_args(argv)
    input_name = args.input.resolve().name
    run_time = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S_%f")
    output = args.output or OUTPUT_ROOT / f"extractor_v{EXTRACTOR_VERSION}_{input_name}_{run_time}"
    suffixes = {"." + s.lower().lstrip(".") for s in args.suffix} if args.suffix else None
    try:
        result = process_directory(args.input, output, dialect=args.dialect,
                                   suffixes=suffixes, recursive=not args.no_recursive)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Processed {result['processed']}: success={result['success']}, failed={result['failed']}")
    print(f"Results: {output.resolve()}")
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
