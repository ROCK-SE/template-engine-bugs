"""Batch Jinja Meta API analysis of a scenario/repository/template directory.

Requires Jinja2 (this evaluation uses 3.1.6). Run from this script directory:
    python -B run_jinja_meta.py
    python -B run_jinja_meta.py --overwrite

The default native profile uses an unmodified jinja2.Environment(). The optional
standard-extensions profile enables only Jinja's i18n, do and loopcontrols.
Every input file has a result JSON, including failures. Output names preserve
the entire template filename before appending .json. Run reports live outside
the result directory. Templates are parsed individually, without rendering,
loading parent/include templates, or importing application/framework code.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

from jinja2 import Environment, meta


ROOT = Path(__file__).resolve().parent
TOOL = "jinja2.meta.find_undeclared_variables"
STANDARD_EXTENSIONS = ("jinja2.ext.i18n", "jinja2.ext.do", "jinja2.ext.loopcontrols")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                     prefix=path.name + ".", suffix=".tmp",
                                     delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(encode(data))
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def create_environment(profile):
    if profile == "native":
        return Environment()
    if profile == "standard-extensions":
        environment = Environment(extensions=STANDARD_EXTENSIONS)
        environment.install_null_translations()
        return environment
    raise ValueError(f"Unknown environment profile: {profile}")


def analyze_file(source, relative, profile):
    """Keep the Meta API name set unchanged; empty values do not imply a schema."""
    result = {
        "tool": TOOL,
        "jinja2_version": version("Jinja2"),
        "environment_profile": profile,
        "template_path": str(source),
        "relative_template_path": relative.as_posix(),
        "scenario": relative.parts[0] if len(relative.parts) >= 3 else None,
        "repository": relative.parts[1] if len(relative.parts) >= 3 else None,
        "source_sha256": None,
        "status": None,
        "variables": None,
        "variable_count": None,
        "error": None,
    }
    phase = "read"
    started = time.perf_counter()
    try:
        raw = source.read_bytes()
        result["source_sha256"] = digest(raw)
        text = raw.decode("utf-8-sig")
        environment = create_environment(profile)
        phase = "parse"
        parsed = environment.parse(text, name=relative.as_posix(), filename=str(source))
        phase = "meta"
        names = sorted(meta.find_undeclared_variables(parsed))
        result["status"] = "success"
        # A normalized top-level name set, compatible with Extractor root keys.
        # Meta API does not infer properties, types, tags or filters.
        result["variables"] = {name: {} for name in names}
        result["variable_count"] = len(names)
    except Exception as exc:
        result["status"] = f"{phase}_failure"
        result["error"] = {
            "phase": phase,
            "type": type(exc).__name__,
            "message": str(exc),
            "line": getattr(exc, "lineno", None),
            "filename": getattr(exc, "filename", None) or str(source),
        }
    return result, round(time.perf_counter() - started, 6)


def summarize(records):
    groups = defaultdict(Counter)
    repositories = defaultdict(Counter)
    errors = Counter()
    for record in records:
        groups[record["scenario"] or "root"][record["status"]] += 1
        repositories[f"{record['scenario'] or 'root'}/{record['repository'] or 'root'}"][record["status"]] += 1
        if record["error"]:
            error = record["error"]
            errors[(error["phase"], error["type"], error["message"].splitlines()[0])] += 1
    return {
        "templates": len(records),
        "status_counts": dict(Counter(record["status"] for record in records)),
        "by_scenario": {key: dict(value) for key, value in sorted(groups.items())},
        "by_repository": {key: dict(value) for key, value in sorted(repositories.items())},
        "first_reported_error_groups": [
            {"phase": phase, "type": kind, "message": message, "templates": count}
            for (phase, kind, message), count in sorted(errors.items())
        ],
    }


def run(args):
    source_root, output_root = args.input.resolve(), args.output.resolve()
    if not source_root.is_dir():
        raise ValueError(f"Input directory does not exist: {source_root}")
    if output_root.is_relative_to(source_root) or source_root.is_relative_to(output_root):
        raise ValueError("Input and output directories must not overlap")
    if output_root.exists() and not args.overwrite:
        raise FileExistsError(f"Output already exists: {output_root}. Use --overwrite to replace this tool's results.")
    sources = sorted((p for p in source_root.rglob("*") if p.is_file()),
                     key=lambda p: p.relative_to(source_root).as_posix())
    if not sources:
        raise ValueError(f"No input files found: {source_root}")
    for source in sources:
        if not source.resolve().is_relative_to(source_root):
            raise ValueError(f"Template link escapes the input directory: {source}")
    previous = {}
    if output_root.exists():
        for path in output_root.rglob("*"):
            if not path.is_file():
                continue
            if not path.resolve().is_relative_to(output_root) or path.suffix != ".json":
                raise ValueError(f"Unexpected file in output directory: {path}")
            raw = path.read_bytes()
            if json.loads(raw.decode("utf-8-sig")).get("tool") != TOOL:
                raise ValueError(f"Refusing to overwrite a result not owned by this script: {path}")
            previous[path.resolve()] = digest(raw)
    stamp = datetime.now(ZoneInfo("Asia/Shanghai"))
    report_path = args.report.resolve() if args.report else (
        ROOT / "evaluation" / f"jinja_meta_{args.profile}_{stamp:%Y%m%d_%H%M%S_%f}" / "run_summary.json")
    if report_path.is_relative_to(source_root) or report_path.is_relative_to(output_root):
        raise ValueError("Keep the run report outside the input and result directories")
    if report_path.exists():
        raise FileExistsError(f"Choose a new report path: {report_path}")
    records, prepared = [], {}
    for source in sources:
        relative = source.relative_to(source_root)
        target = (output_root / relative.parent / (relative.name + ".json")).resolve()
        if not target.is_relative_to(output_root):
            raise ValueError(f"Result path escapes the output directory: {target}")
        if target in prepared:
            raise ValueError(f"Duplicate result path: {target}")
        result, seconds = analyze_file(source, relative, args.profile)
        prepared[target] = result
        records.append({
            "scenario": result["scenario"], "repository": result["repository"],
            "template_path": str(source), "json_result_path": str(target),
            "source_sha256": result["source_sha256"], "status": result["status"],
            "variable_count": result["variable_count"], "error": result["error"],
            "analysis_seconds": seconds, "result_sha256": digest(encode(result)),
        })
    # Analyze every file before touching existing output. Failures are results,
    # not grounds for dropping or replacing a template in the evaluation set.
    for source, record in zip(sources, records):
        if record["source_sha256"] is not None and digest(source.read_bytes()) != record["source_sha256"]:
            raise ValueError(f"Template changed during analysis: {source}")
    for path, previous_hash in previous.items():
        if digest(path.read_bytes()) != previous_hash:
            raise ValueError(f"Existing result changed during analysis: {path}")
    for target, result in prepared.items():
        save(target, result)
    obsolete = previous.keys() - prepared.keys()
    for path in sorted(obsolete):
        if not path.resolve().is_relative_to(output_root):
            raise ValueError(f"Obsolete result escapes the output directory: {path}")
        if digest(path.read_bytes()) != previous[path]:
            raise ValueError(f"Obsolete result changed during analysis: {path}")
        path.unlink()  # Only this tool's checked, obsolete JSON files.
    actual = {p.resolve() for p in output_root.rglob("*") if p.is_file()}
    if actual != set(prepared):
        raise RuntimeError("Output directory does not match the processed input files")
    for target, result in prepared.items():
        if target.read_bytes() != encode(result):
            raise RuntimeError(f"Result verification failed: {target}")
    environment = create_environment(args.profile)
    report = {
        "created_at": stamp.isoformat(), "tool": TOOL,
        "input_directory": str(source_root), "output_directory": str(output_root),
        "environment_profile": args.profile,
        "jinja2_version": version("Jinja2"), "python_version": platform.python_version(),
        "script_path": str(Path(__file__).resolve()),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "jinja_meta_source_path": str(Path(meta.__file__).resolve()),
        "jinja_meta_source_sha256": digest(Path(meta.__file__).read_bytes()),
        "enabled_extensions": sorted(environment.extensions),
        "environment_global_names": sorted(environment.globals),
        "policies": {
            "file_selection": "All files recursively under the input directory, sorted by relative path.",
            "analysis_unit": "One template source file; no rendering or dependency expansion.",
            "name_policy": "Unmodified Meta API name set; callable names are not post-filtered.",
            "variables_schema": "Top-level names mapped to empty objects; empty objects make no claim about attribute structure or types.",
            "failure_policy": "Keep one JSON per input; variables=null on failure and {} on successful empty extraction.",
            "custom_environment": "No custom filters, tests, application globals, dbt grammar, or Ansible/Flask runtime registered.",
            "scoring": "Not scored against Ground Truth in this run.",
        },
        "summary": summarize(records),
        "obsolete_owned_results_removed": [str(path) for path in sorted(obsolete)],
        "results": records,
    }
    save(report_path, report)
    print(json.dumps({"environment_profile": args.profile,
                      "output_directory": str(output_root), "report": str(report_path),
                      **report["summary"]}, ensure_ascii=False, indent=2))
    # A completed evaluation succeeds even when some templates are unsupported.
    # Per-template failures remain explicit in every result and the report.
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=ROOT / "sample_template")
    parser.add_argument("--output", type=Path, default=ROOT / "meta_outputs")
    parser.add_argument("--profile", choices=("native", "standard-extensions"), default="native")
    parser.add_argument("--report", type=Path, help="New report JSON outside input/output directories")
    parser.add_argument("--overwrite", action="store_true", help="Replace this script's existing result files")
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
