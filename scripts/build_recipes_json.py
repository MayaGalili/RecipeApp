#!/usr/bin/env python3
"""Convert category folders of DOCX recipes to the existing migrate-ready JSON format.

Progress is saved in OUTPUT.progress.json after each successful recipe. Rerunning
resumes without new API calls for unchanged, already processed files.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from docx import Document
from dotenv import load_dotenv
from openai import APITimeoutError, APIConnectionError, RateLimitError

from recipe_app.ai_parser import create_openai_client, parse_recipe_text
from recipe_app.recipes_api import VALID_CATEGORIES

RETRYABLE_ERRORS = (APITimeoutError, APIConnectionError, RateLimitError, json.JSONDecodeError)
REQUIRED_FIELDS = ("nameEn", "nameHe", "emoji", "ingredientsHe", "ingredientsEn", "instructionsHe", "instructionsEn")


def atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def extract_text(file_path):
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    # Some recipe documents contain their ingredient lists in tables.
    for table in doc.tables:
        for row in table.rows:
            line = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if line:
                paragraphs.append(line)
    return "\n".join(paragraphs)


def empty_data():
    return {
        "recipes": {},
        "recipeTranslations": {"he": {}, "en": {}},
        "recipeCategoryMap": {category: [] for category in VALID_CATEGORIES},
    }


def validate_parsed(parsed):
    if not isinstance(parsed, dict):
        raise ValueError("Parser returned a non-object")
    missing = [field for field in REQUIRED_FIELDS if field not in parsed]
    if missing:
        raise ValueError(f"Missing parser fields: {', '.join(missing)}")
    for field in ("nameEn", "nameHe", "emoji"):
        if not isinstance(parsed[field], str) or not parsed[field].strip():
            raise ValueError(f"Invalid {field}")
    if len(parsed["nameEn"]) > 255 or len(parsed["nameHe"]) > 255 or len(parsed["emoji"]) > 10:
        raise ValueError("Recipe name or emoji exceeds database length limit")
    for field in ("ingredientsHe", "ingredientsEn", "instructionsHe", "instructionsEn"):
        if not isinstance(parsed[field], list):
            raise ValueError(f"{field} must be a list")
    if parsed.get("category") not in VALID_CATEGORIES:
        raise ValueError(f"Invalid recipe category: {parsed.get('category')!r}")


def assemble(entries, overrides):
    data = empty_data()
    for relative_path, record in sorted(entries.items()):
        parsed = record["parsed"]
        category = overrides.get(Path(relative_path).parts[0], parsed["category"])
        base_key = parsed["nameEn"]
        key = base_key
        number = 1
        while key in data["recipes"]:
            key = f"{base_key}_{number}"
            number += 1
        if len(key) > 255:
            raise ValueError(f"Generated key exceeds 255 characters: {key[:60]}")
        data["recipes"][key] = {
            "name": f"{parsed['emoji']} {parsed['nameHe']}",
            "emoji": parsed["emoji"],
            "ingredients": {"he": parsed["ingredientsHe"], "en": parsed["ingredientsEn"]},
            "instructions": {"he": parsed["instructionsHe"], "en": parsed["instructionsEn"]},
        }
        data["recipeTranslations"]["he"][key] = parsed["nameHe"]
        data["recipeTranslations"]["en"][key] = parsed["nameEn"]
        data["recipeCategoryMap"][category].append(key)
    return data


def validate_output(data):
    # Validate the essential shape; migrate_to_db should still validate before DB import.
    errors = []
    recipes = data["recipes"]
    for category in VALID_CATEGORIES:
        if not isinstance(data["recipeCategoryMap"].get(category), list):
            errors.append(f"Missing category list: {category}")
    for key, recipe in recipes.items():
        if len(key) > 255 or len(recipe["name"]) > 255:
            errors.append(f"Recipe name/key too long: {key[:40]}")
        for field in ("ingredients", "instructions"):
            for lang in ("he", "en"):
                if not isinstance(recipe[field][lang], list):
                    errors.append(f"Invalid {field}.{lang} for {key}")
    return errors


def scan(folder):
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")
    return sorted(
        file for subfolder in folder.iterdir() if subfolder.is_dir()
        for file in subfolder.iterdir()
        if file.is_file() and file.suffix.lower() == ".docx" and not file.name.startswith("~$")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", help="Folder containing category subfolders with .docx files")
    parser.add_argument("--output", default="data/recipes_import.json")
    parser.add_argument("--map", dest="mappings", action="append", default=[], help='Override folder category: "folder=category"')
    parser.add_argument("--dry-run", action="store_true", help="List files without API calls or writes")
    parser.add_argument("--allow-partial", action="store_true", help="Write output even if some recipes fail")
    parser.add_argument("--force", action="store_true", help="Allow overwriting an existing final output")
    parser.add_argument("--restart", action="store_true", help="Ignore existing progress and reprocess all files (costs API calls)")
    args = parser.parse_args()

    overrides = {}
    for mapping in args.mappings:
        if "=" not in mapping:
            parser.error(f"Invalid --map: {mapping}")
        folder_name, category = mapping.split("=", 1)
        if not folder_name or category not in VALID_CATEGORIES:
            parser.error(f"Invalid --map: {mapping}")
        overrides[folder_name] = category

    folder = Path(args.folder).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    progress_path = output.with_name(output.name + ".progress.json")
    failed_path = output.with_name(output.name + ".failed.json")
    try:
        files = scan(folder)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Found {len(files)} DOCX files")
    if args.dry_run:
        for file in files:
            print(f"  {file.relative_to(folder)}")
        return 0
    if output.exists() and not args.force:
        print(f"ERROR: Output already exists: {output}. Use --force to overwrite (progress is preserved).")
        return 1

    entries = {}
    if progress_path.exists() and not args.restart:
        try:
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            if progress.get("source_folder") != str(folder):
                print("ERROR: Progress belongs to a different source folder. Use --restart to start over.")
                return 1
            entries = progress["entries"]
            print(f"Resuming from {len(entries)} saved recipes")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"ERROR: Invalid progress file: {exc}. Back it up and use --restart if appropriate.")
            return 1

    load_dotenv()
    client = create_openai_client()
    if client is None:
        print("ERROR: OPENAI_API_KEY is not configured")
        return 1
    # Increase per-attempt timeout without changing the shared parser or app settings.
    if hasattr(client, "with_options"):
        client = client.with_options(timeout=120.0, max_retries=1)

    skipped = succeeded = 0
    failures = {}
    current_paths = set()
    for index, file in enumerate(files, start=1):
        relative = file.relative_to(folder).as_posix()
        current_paths.add(relative)
        try:
            raw = file.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if relative in entries and entries[relative]["sha256"] == digest:
                skipped += 1
                print(f"[{index}/{len(files)}] SKIP {relative}")
                continue
            text = extract_text(file)
            if not text.strip():
                raise ValueError("Document contains no readable text")
            print(f"[{index}/{len(files)}] PARSE {relative}", flush=True)
            for attempt in range(1, 3):
                try:
                    parsed = parse_recipe_text(client, text)
                    validate_parsed(parsed)
                    break
                except RETRYABLE_ERRORS as exc:
                    if attempt == 2:
                        raise
                    print(f"  Retrying after {type(exc).__name__} (attempt {attempt + 1}/2)", flush=True)
            entries[relative] = {"sha256": digest, "parsed": parsed}
            atomic_write_json(progress_path, {"source_folder": str(folder), "entries": entries})
            succeeded += 1
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:
            failures[relative] = f"{type(exc).__name__}: {exc}"
            print(f"  FAILED {relative}: {failures[relative]}", file=sys.stderr, flush=True)

    # Do not silently include recipes from deleted/renamed source files.
    entries = {path: record for path, record in entries.items() if path in current_paths}
    atomic_write_json(progress_path, {"source_folder": str(folder), "entries": entries})
    if failures:
        atomic_write_json(failed_path, failures)
    elif failed_path.exists():
        failed_path.unlink()

    print(f"Summary: {succeeded} newly parsed, {skipped} reused, {len(failures)} failed")
    if failures and not args.allow_partial:
        print(f"Output not written because some files failed. Progress saved: {progress_path}")
        print("Rerun with --allow-partial to export successful recipes, or rerun normally to retry failures.")
        return 1
    try:
        data = assemble(entries, overrides)
        errors = validate_output(data)
        if errors:
            raise ValueError("; ".join(errors))
        atomic_write_json(output, data)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: Could not generate output: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {len(data['recipes'])} recipes to {output}")
    if failures:
        print(f"Failed files listed in {failed_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
