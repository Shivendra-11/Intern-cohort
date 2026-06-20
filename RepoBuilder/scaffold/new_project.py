#!/usr/bin/env python3
"""Scaffold a greenfield project from a repo-builder template.

Copies one of the bundled templates into a destination directory and prints the
exact install / test / run commands for that stack. The agent then runs those
commands to prove the project works.

Usage:
  python3 new_project.py --list
  python3 new_project.py --template fastapi-service --dest /tmp/ledger
  python3 new_project.py --template node-api       --dest ./ledger-api [--name my-api]
  python3 new_project.py --template rust-cli        --dest ./logcount  [--force]
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

SCAFFOLD_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.normpath(os.path.join(SCAFFOLD_DIR, "..", "templates"))

# Per-template metadata: the commands to prove it runs, and an optional
# (filename, placeholder) the --name flag rewrites.
NEXT_STEPS = {
    "fastapi-service": {
        "install": "python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt",
        "test": "pytest -q",
        "run": "uvicorn app.main:app --reload",
        "name_token": ("README.md", "Ledger Service"),
    },
    "node-api": {
        "install": "npm install",
        "test": "npm test",
        "run": "npm start",
        "name_token": ("package.json", "ledger-api"),
    },
    "rust-cli": {
        "install": "cargo build",
        "test": "cargo test",
        "run": "cargo run -- path/to/app.log",
        "name_token": ("Cargo.toml", "logcount"),
    },
}


def list_templates():
    print("Available templates:\n")
    for name in sorted(NEXT_STEPS):
        present = "ok" if os.path.isdir(os.path.join(TEMPLATES_DIR, name)) else "MISSING"
        print(f"  {name:18} [{present}]")


def is_empty_dir(path):
    return os.path.isdir(path) and not os.listdir(path)


def apply_name(dest, template, name):
    """Best-effort rename: substitute the template's name token in one metadata file."""
    fname, token = NEXT_STEPS[template]["name_token"]
    target = os.path.join(dest, fname)
    if not os.path.exists(target):
        return
    with open(target, "r", encoding="utf-8") as fh:
        content = fh.read()
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(content.replace(token, name))


def scaffold(template, dest, name=None, force=False):
    src = os.path.join(TEMPLATES_DIR, template)
    if not os.path.isdir(src):
        print(f"error: unknown template '{template}'. Use --list to see options.", file=sys.stderr)
        return 2
    if os.path.exists(dest) and not is_empty_dir(dest):
        if not force:
            print(f"error: destination '{dest}' exists and is not empty (use --force).", file=sys.stderr)
            return 2
        shutil.rmtree(dest)
    shutil.copytree(src, dest, dirs_exist_ok=True)
    if name:
        apply_name(dest, template, name)

    steps = NEXT_STEPS[template]
    print(f"Scaffolded '{template}' into {os.path.abspath(dest)}\n")
    print("Next steps:")
    print(f"  cd {dest}")
    print(f"  {steps['install']}")
    print(f"  {steps['test']}      # prove it runs")
    print(f"  {steps['run']}       # start it")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scaffold a project from a repo-builder template")
    ap.add_argument("--list", action="store_true", help="list available templates")
    ap.add_argument("--template", help="template name (see --list)")
    ap.add_argument("--dest", help="destination directory")
    ap.add_argument("--name", help="optional project name to substitute")
    ap.add_argument("--force", action="store_true", help="overwrite a non-empty destination")
    args = ap.parse_args(argv)

    if args.list:
        list_templates()
        return 0
    if not args.template or not args.dest:
        ap.error("--template and --dest are required (or use --list)")
    return scaffold(args.template, args.dest, args.name, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
