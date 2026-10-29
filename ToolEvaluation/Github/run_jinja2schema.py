r"""Batch native jinja2schema inference for scenario/repository/template files.

Run this script using the dedicated jinja2schema evaluation environment:
    python -B run_jinja2schema.py
    python -B run_jinja2schema.py --overwrite

The default input/output directories are sample_template and schema_outputs.
Every input file has a result JSON, including failures. Native infer() uses a
fresh default Config per file; native to_json_schema() exports the structure.
No framework extensions, source rewrites, unsupported-call workarounds, or
post-filtering of inferred names are applied. Each file runs in its own process
with a timeout. Reports live outside the per-template result directory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

from jinja2 import Environment, TemplateSyntaxError

try:
    import jinja2schema
except ImportError as exc:
    raise SystemExit(
        "jinja2schema is not installed in this Python environment. Run this script "
        "with .venv_jinja2schema/Scripts/python.exe, or install "
        "jinja2schema==0.1.4 and Jinja2==3.1.6 into your chosen environment."
    ) from exc


ROOT = Path(__file__).resolve().parent
TOOL = "jinja2schema.infer"
REPOSITORY_URL = "https://github.com/aromanovich/jinja2schema"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=path.name + ".",
                                     suffix=".tmp", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(encode(value))
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def empty_result(source, relative):
    return {
        "tool": TOOL,
        "jinja2schema_version": version("jinja2schema"),
        "jinja2_version": version("Jinja2"),
        "environment_profile": "native",
        "template_path": str(source),
        "relative_template_path": relative.as_posix(),
        "scenario": relative.parts[0] if len(relative.parts) >= 3 else None,
        "repository": relative.parts[1] if len(relative.parts) >= 3 else None,
        "source_sha256": None,
        "status": None,
        "variables": None,
        "variable_count": None,
        "json_schema": None,
        "error": None,
    }


def error_info(exc, phase, source):
    lines = set()
    line = getattr(exc, "lineno", None)
    if isinstance(line, int):
        lines.add(line)
    for name in ("ast", "actual_ast"):
        value = getattr(getattr(exc, name, None), "lineno", None)
        if isinstance(value, int):
            lines.add(value)
    for name in ("fst", "snd", "actual_struct", "expected_struct"):
        lines.update(value for value in getattr(getattr(exc, name, None), "linenos", ())
                     if isinstance(value, int))
    return {"phase": phase, "type": type(exc).__name__, "message": str(exc),
            "line": min(lines) if lines else None, "lines": sorted(lines),
            "filename": getattr(exc, "filename", None) or str(source)}


def analyze_file(source, relative):
    """Call the public native API; only serialize, never reinterpret its schema."""
    result = empty_result(source, relative)
    phase = "read"
    started = time.perf_counter()
    try:
        raw = source.read_bytes()
        result["source_sha256"] = digest(raw)
        text = raw.decode("utf-8-sig")
        phase = "inference"
        inferred = jinja2schema.infer(text, config=jinja2schema.Config())
        phase = "serialization"
        schema = jinja2schema.to_json_schema(inferred)
        # variables is a root-key view of the official schema, not an
        # Extractor-style tree conversion. Preserve the full official output.
        properties = schema["properties"]
        variables = {name: properties[name] for name in sorted(properties)}
        encode(schema)  # Verify JSON serializability inside the failure boundary.
        result.update(status="success", variables=variables,
                      variable_count=len(variables), json_schema=schema)
    except Exception as exc:
        if phase == "inference" and isinstance(exc, TemplateSyntaxError):
            phase = "parse"
        result["status"] = f"{phase}_failure"
        result["error"] = error_info(exc, phase, source)
    return result, round(time.perf_counter() - started, 6)


def run_worker(source, relative, timeout):
    started = time.perf_counter()
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker",
               "--source", str(source), "--relative", relative.as_posix()]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if completed.returncode:
            raise RuntimeError(f"Worker exit {completed.returncode}: {completed.stderr[-4000:]}")
        response = json.loads(completed.stdout)
        result, seconds = response["result"], response["analysis_seconds"]
        if result["tool"] != TOOL or result["relative_template_path"] != relative.as_posix():
            raise ValueError("Worker returned a result for a different tool or source")
    except Exception as exc:
        result = empty_result(source, relative)
        result["status"] = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "worker_failure"
        result["error"] = {"phase": "worker", "type": type(exc).__name__,
                           "message": str(exc), "line": None, "lines": [],
                           "filename": str(source)}
        seconds = None
    return result, seconds, round(time.perf_counter() - started, 6)


def summarize(records):
    scenarios, repositories, errors = defaultdict(Counter), defaultdict(Counter), Counter()
    for row in records:
        scenarios[row["scenario"] or "root"][row["status"]] += 1
        repositories[f"{row['scenario'] or 'root'}/{row['repository'] or 'root'}"][row["status"]] += 1
        if row["error"]:
            error = row["error"]
            errors[(error["phase"], error["type"], error["message"].splitlines()[0])] += 1
    return {"templates": len(records),
            "status_counts": dict(Counter(row["status"] for row in records)),
            "by_scenario": {key: dict(value) for key, value in sorted(scenarios.items())},
            "by_repository": {key: dict(value) for key, value in sorted(repositories.items())},
            "first_reported_error_groups": [
                {"phase": phase, "type": kind, "message": message, "templates": count}
                for (phase, kind, message), count in sorted(errors.items())]}


def run(args):
    source_root, output_root = args.input.resolve(), args.output.resolve()
    if not source_root.is_dir():
        raise ValueError(f"Input directory does not exist: {source_root}")
    if args.timeout <= 0 or args.workers < 1:
        raise ValueError("Timeout and worker count must be positive")
    if output_root.is_relative_to(source_root) or source_root.is_relative_to(output_root):
        raise ValueError("Input and output directories must not overlap")
    if output_root.exists() and not args.overwrite:
        raise FileExistsError(f"Output already exists: {output_root}. Use --overwrite to replace this tool's results.")
    sources = sorted((p for p in source_root.rglob("*") if p.is_file()),
                     key=lambda p: p.relative_to(source_root).as_posix())
    if not sources:
        raise ValueError(f"No input files found: {source_root}")
    source_hashes = {}
    for source in sources:
        if not source.resolve().is_relative_to(source_root):
            raise ValueError(f"Template link escapes input directory: {source}")
        # Read failures still receive a worker result instead of being omitted.
        try:
            source_hashes[source] = digest(source.read_bytes())
        except OSError:
            source_hashes[source] = None
    previous = {}
    if output_root.exists():
        for path in output_root.rglob("*"):
            if not path.is_file():
                continue
            if not path.resolve().is_relative_to(output_root) or path.suffix != ".json":
                raise ValueError(f"Unexpected file in output directory: {path}")
            raw = path.read_bytes()
            owned = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(owned, dict) or owned.get("tool") != TOOL:
                raise ValueError(f"Refusing to replace a result not owned by this tool: {path}")
            previous[path.resolve()] = digest(raw)
    stamp = datetime.now(ZoneInfo("Asia/Shanghai"))
    report_path = args.report.resolve() if args.report else (
        ROOT / "evaluation" / f"jinja2schema_native_{stamp:%Y%m%d_%H%M%S_%f}" / "run_summary.json")
    if report_path.is_relative_to(source_root) or report_path.is_relative_to(output_root):
        raise ValueError("Keep the report outside input and result directories")
    if report_path.exists():
        raise FileExistsError(f"Choose a new report path: {report_path}")

    def analyze(source):
        return run_worker(source, source.relative_to(source_root), args.timeout)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        outcomes = list(executor.map(analyze, sources))
    records, prepared = [], {}
    for source, (result, seconds, process_seconds) in zip(sources, outcomes):
        relative = source.relative_to(source_root)
        target = (output_root / relative.parent / (relative.name + ".json")).resolve()
        if not target.is_relative_to(output_root) or target in prepared:
            raise ValueError(f"Invalid or colliding output path: {target}")
        source_hash = source_hashes[source]
        if source_hash is not None:
            if digest(source.read_bytes()) != source_hash:
                raise ValueError(f"Template changed during analysis: {source}")
            if result["source_sha256"] not in (None, source_hash):
                raise ValueError(f"Worker analyzed different source bytes: {source}")
            result["source_sha256"] = source_hash
        prepared[target] = result
        records.append({"scenario": result["scenario"], "repository": result["repository"],
                        "template_path": str(source), "json_result_path": str(target),
                        "source_sha256": result["source_sha256"], "status": result["status"],
                        "variable_count": result["variable_count"], "error": result["error"],
                        "analysis_seconds": seconds, "worker_process_seconds": process_seconds,
                        "result_sha256": digest(encode(result))})
    for path, previous_hash in previous.items():
        if digest(path.read_bytes()) != previous_hash:
            raise ValueError(f"Existing result changed during analysis: {path}")
    for target, result in prepared.items():
        save(target, result)
    obsolete = previous.keys() - prepared.keys()
    for path in sorted(obsolete):
        if not path.resolve().is_relative_to(output_root) or digest(path.read_bytes()) != previous[path]:
            raise ValueError(f"Unsafe or changed obsolete result: {path}")
        path.unlink()  # Only checked, previously owned JSON files; no recursive deletion.
    if {p.resolve() for p in output_root.rglob("*") if p.is_file()} != set(prepared):
        raise RuntimeError("Output directory does not match the processed input files")
    for target, result in prepared.items():
        if target.read_bytes() != encode(result):
            raise RuntimeError(f"Result verification failed: {target}")
    package = Path(jinja2schema.__file__).resolve().parent
    config = {name: value for name, value in vars(jinja2schema.Config()).items()
              if isinstance(value, (str, bool, int, float, type(None)))}
    report = {
        "created_at": stamp.isoformat(), "tool": TOOL, "repository_url": REPOSITORY_URL,
        "input_directory": str(source_root), "output_directory": str(output_root),
        "environment_profile": "native", "jinja2schema_version": version("jinja2schema"),
        "jinja2_version": version("Jinja2"), "python_version": platform.python_version(),
        "python_executable": sys.executable, "script_path": str(Path(__file__).resolve()),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "jinja2schema_package_path": str(package),
        "jinja2schema_python_file_sha256": {p.relative_to(package).as_posix(): digest(p.read_bytes())
                                          for p in sorted(package.rglob("*.py"))},
        "default_config": config,
        "native_parser_extensions": sorted(Environment().extensions),
        "worker_count": args.workers, "timeout_seconds_per_template": args.timeout,
        "policies": {
            "file_selection": "All input files recursively, sorted by relative path; no resampling or success-based selection.",
            "native_api": "infer(text, config=Config()) followed by to_json_schema(model); fresh default Config per file.",
            "variables_schema": "Root properties from the official JSON Schema; names and inferred structures are not post-filtered or converted into Extractor's schema.",
            "json_schema": "Complete unmodified official to_json_schema output, including root required/title information.",
            "failure_policy": "One JSON per input; variables and json_schema are null on failure; successful empty inference is distinct.",
            "environment": "No custom extensions, filters, tests, call handlers, application globals, source rewriting or library patches.",
            "dependencies": "No application loader/configuration or missing-template workaround; retain native treatment of includes and inheritance.",
            "isolation": "One subprocess per template with timeout; no modifications to templates, Extractor, Meta results or Ground Truth.",
            "scoring": "Not scored against Ground Truth in this run.",
        },
        "summary": summarize(records),
        "obsolete_owned_results_removed": [str(path) for path in sorted(obsolete)],
        "results": records,
    }
    save(report_path, report)
    print(json.dumps({"output_directory": str(output_root), "report": str(report_path),
                      "jinja2schema_version": report["jinja2schema_version"],
                      "jinja2_version": report["jinja2_version"],
                      **report["summary"]}, ensure_ascii=False, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=ROOT / "sample_template")
    parser.add_argument("--output", type=Path, default=ROOT / "schema_outputs")
    parser.add_argument("--report", type=Path, help="New run report JSON outside input/output")
    parser.add_argument("--overwrite", action="store_true", help="Replace this script's existing results")
    parser.add_argument("--timeout", type=float, default=30, help="Per-template timeout in seconds")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent isolated template workers")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--source", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--relative", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.source is None or args.relative is None:
            parser.error("Internal worker requires --source and --relative")
        result, seconds = analyze_file(args.source.resolve(), args.relative)
        print(json.dumps({"result": result, "analysis_seconds": seconds}, ensure_ascii=False))
        return
    try:
        run(args)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
