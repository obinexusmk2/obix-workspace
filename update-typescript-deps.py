#!/usr/bin/env python3
"""
OBINexus TypeScript Dependency Updater

Maintains TypeScript dependency metadata across the assembled OBIX workspace.

By default the script only updates source-controlled package.json files. It does
not run npm install unless --install is supplied.

Actions:
1. Lock TypeScript to a configurable minor version using a tilde range.
2. Remove obsolete obix-workspace dependency references.
3. Skip generated/vendor trees such as node_modules, dist and build.
4. Optionally run npm install once per detected repository/project root.
5. Print a summary and return a non-zero exit code on update/install failures.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

DEFAULT_TYPESCRIPT_VERSION = "5.4.0"
DEFAULT_WORKSPACE_ROOT = Path(__file__).resolve().parent / "obix"

# Never mutate generated, vendored, cache or VCS-owned package manifests.
EXCLUDED_DIRS: Set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".next",
    ".nuxt",
    ".parcel-cache",
    ".turbo",
    ".yarn",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
}

DEPENDENCY_SECTIONS: Tuple[str, ...] = (
    "dependencies",
    "devDependencies",
    "peerDependencies",
    "optionalDependencies",
)

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(message: str, level: str = "info") -> None:
    """Print a colored log message."""
    if level == "success":
        print(f"{GREEN}✓ {message}{RESET}")
    elif level == "warn":
        print(f"{YELLOW}⚠ {message}{RESET}")
    elif level == "error":
        print(f"{RED}✗ {message}{RESET}")
    elif level == "info":
        print(f"{BLUE}ℹ {message}{RESET}")
    else:
        print(message)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update TypeScript dependencies across the OBIX workspace."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help=f"Workspace root to scan (default: {DEFAULT_WORKSPACE_ROOT})",
    )
    parser.add_argument(
        "--typescript-version",
        default=DEFAULT_TYPESCRIPT_VERSION,
        help=f"TypeScript version to tilde-lock (default: {DEFAULT_TYPESCRIPT_VERSION})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing package.json files or running npm.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print unchanged files and npm stderr/stdout details.",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Run npm install once per detected repository/project root after updates.",
    )
    parser.add_argument(
        "--legacy-peer-deps",
        action="store_true",
        help="Pass --legacy-peer-deps to npm install.",
    )
    parser.add_argument(
        "--npm-timeout",
        type=int,
        default=600,
        metavar="SECONDS",
        help="Timeout for each npm install (default: 600 seconds).",
    )
    return parser.parse_args(argv)


def find_package_jsons(workspace_root: Path) -> List[Path]:
    """Find source package.json files while pruning generated/vendor trees."""
    if not workspace_root.exists():
        log(f"Workspace root not found: {workspace_root}", "error")
        return []
    if not workspace_root.is_dir():
        log(f"Workspace root is not a directory: {workspace_root}", "error")
        return []

    package_files: List[Path] = []

    for current_root, dirs, files in os.walk(workspace_root, followlinks=False):
        # Prune excluded directories in-place so os.walk never descends into them.
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        if "package.json" in files:
            package_files.append(Path(current_root) / "package.json")

    package_files.sort(key=lambda p: str(p.relative_to(workspace_root)).lower())
    log(f"Found {len(package_files)} source package.json files", "info")
    return package_files


def update_package_json(
    file_path: Path,
    typescript_version: str,
    dry_run: bool,
) -> Tuple[bool, Dict[str, Any]]:
    """Update one package.json and return (changed, change_summary)."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Failed to read/parse {file_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"package.json root must be an object: {file_path}")

    changes: Dict[str, Any] = {}
    new_ts_version = f"~{typescript_version.lstrip('~')}"

    dev_dependencies = data.get("devDependencies")
    if dev_dependencies is None:
        dev_dependencies = {}
        data["devDependencies"] = dev_dependencies
    elif not isinstance(dev_dependencies, dict):
        raise RuntimeError(f"devDependencies must be an object: {file_path}")

    old_ts_version = dev_dependencies.get("typescript")
    if old_ts_version != new_ts_version:
        dev_dependencies["typescript"] = new_ts_version
        changes["typescript"] = {"old": old_ts_version, "new": new_ts_version}

    for dep_type in DEPENDENCY_SECTIONS:
        dependencies = data.get(dep_type)
        if dependencies is None:
            continue
        if not isinstance(dependencies, dict):
            raise RuntimeError(f"{dep_type} must be an object: {file_path}")
        if "obix-workspace" in dependencies:
            removed = dependencies.pop("obix-workspace")
            changes.setdefault("removed", {})[dep_type] = removed

    if not changes:
        return False, {}

    if not dry_run:
        try:
            with file_path.open("w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
        except OSError as exc:
            raise RuntimeError(f"Failed to write {file_path}: {exc}") from exc

    return True, changes


def find_repo_root(path: Path, workspace_root: Path) -> Optional[Path]:
    """Return the nearest ancestor Git repository root inside the workspace."""
    current = path.resolve()
    workspace_root = workspace_root.resolve()

    while True:
        if (current / ".git").exists():
            return current
        if current == workspace_root:
            return None
        if workspace_root not in current.parents:
            return None
        current = current.parent


def has_workspace_declaration(package_json: Path) -> bool:
    """Return True when package.json declares npm/yarn-style workspaces."""
    try:
        with package_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, dict) and "workspaces" in data


def find_project_install_root(package_file: Path, workspace_root: Path) -> Path:
    """
    Select one npm install root for a changed package.

    Prefer the containing Git repository root when it has a package.json. This
    deduplicates nested workspace packages. Otherwise prefer the nearest ancestor
    package.json that declares workspaces, then fall back to the package itself.
    """
    package_dir = package_file.parent.resolve()
    repo_root = find_repo_root(package_dir, workspace_root)

    if repo_root is not None and (repo_root / "package.json").is_file():
        return repo_root

    stop = repo_root if repo_root is not None else workspace_root.resolve()
    current = package_dir
    workspace_candidate: Optional[Path] = None

    while True:
        candidate = current / "package.json"
        if candidate.is_file() and has_workspace_declaration(candidate):
            workspace_candidate = current
        if current == stop or current == workspace_root.resolve():
            break
        if current.parent == current:
            break
        current = current.parent

    return workspace_candidate or package_dir


def collect_install_roots(
    updated_files: Iterable[Path], workspace_root: Path
) -> List[Path]:
    roots = {
        find_project_install_root(package_file, workspace_root)
        for package_file in updated_files
    }
    return sorted(roots, key=lambda p: str(p).lower())


def resolve_npm_command() -> Optional[str]:
    """Resolve npm robustly on Windows and POSIX."""
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm", "npm.cmd"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def run_npm_install(
    install_root: Path,
    npm_command: str,
    legacy_peer_deps: bool,
    timeout: int,
    verbose: bool,
) -> bool:
    command = [npm_command, "install"]
    if legacy_peer_deps:
        command.append("--legacy-peer-deps")

    try:
        result = subprocess.run(
            command,
            cwd=install_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        log(f"npm install timed out in {install_root}", "warn")
        return False
    except OSError as exc:
        log(f"Failed to run npm install in {install_root}: {exc}", "error")
        return False

    if result.returncode == 0:
        if verbose and result.stdout.strip():
            print(result.stdout.rstrip())
        return True

    log(f"npm install failed in {install_root} (exit {result.returncode})", "warn")
    if verbose:
        if result.stdout.strip():
            print(result.stdout.rstrip())
        if result.stderr.strip():
            print(result.stderr.rstrip(), file=sys.stderr)
    return False


def print_changes_summary(changes_summary: Dict[str, Dict[str, Any]]) -> None:
    if not changes_summary:
        return

    print()
    log("Changes Summary:", "info")
    for file_path, changes in changes_summary.items():
        print(f"\n  {file_path}")
        for key, value in changes.items():
            if key == "removed":
                for dep_type, version in value.items():
                    print(f"    - Removed obix-workspace from {dep_type}: {version}")
            elif isinstance(value, dict) and "old" in value:
                print(f"    - {key}: {value['old']} → {value['new']}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    workspace_root = args.workspace.expanduser().resolve()

    log("OBINexus TypeScript Dependency Updater", "info")
    log(f"Workspace: {workspace_root}", "info")
    log(f"TypeScript will be locked to: ~{args.typescript_version.lstrip('~')}", "info")

    if args.dry_run:
        log("Running in DRY RUN mode (no files will be modified)", "warn")
    elif not args.install:
        log("Manifest-only mode; npm install is disabled (use --install to enable)", "info")
    print()

    package_files = find_package_jsons(workspace_root)
    if not package_files:
        log("No source package.json files found", "error")
        return 1

    updated_files: List[Path] = []
    failed_files: List[Path] = []
    changes_summary: Dict[str, Dict[str, Any]] = {}

    for i, pkg_file in enumerate(package_files, 1):
        rel_path = pkg_file.relative_to(workspace_root)
        try:
            changed, changes = update_package_json(
                pkg_file,
                typescript_version=args.typescript_version,
                dry_run=args.dry_run,
            )
            if changed:
                updated_files.append(pkg_file)
                changes_summary[str(rel_path)] = changes
                prefix = "Would update" if args.dry_run else "Updated"
                log(f"[{i}/{len(package_files)}] {prefix}: {rel_path}", "success")
            elif args.verbose:
                log(f"[{i}/{len(package_files)}] No changes: {rel_path}", "info")
        except Exception as exc:  # Keep scanning other repos and report all failures.
            failed_files.append(pkg_file)
            log(f"[{i}/{len(package_files)}] Error processing {rel_path}: {exc}", "error")

    print()
    action = "Would update" if args.dry_run else "Updated"
    log(f"{action} {len(updated_files)}/{len(package_files)} package.json files", "info")

    npm_failures: List[Path] = []
    if args.install and not args.dry_run and updated_files:
        npm_command = resolve_npm_command()
        if npm_command is None:
            log(
                "npm was not found in PATH. Install Node.js/npm or make npm.cmd/npm available.",
                "error",
            )
            npm_failures.append(workspace_root)
        else:
            install_roots = collect_install_roots(updated_files, workspace_root)
            print()
            log(
                f"Running npm install in {len(install_roots)} detected project root(s) using {npm_command}",
                "info",
            )

            npm_success = 0
            for index, install_root in enumerate(install_roots, 1):
                try:
                    rel_root = install_root.relative_to(workspace_root)
                except ValueError:
                    rel_root = install_root
                log(f"[{index}/{len(install_roots)}] npm install: {rel_root}", "info")
                if run_npm_install(
                    install_root,
                    npm_command=npm_command,
                    legacy_peer_deps=args.legacy_peer_deps,
                    timeout=args.npm_timeout,
                    verbose=args.verbose,
                ):
                    npm_success += 1
                else:
                    npm_failures.append(install_root)

            log(
                f"npm install: {npm_success} succeeded, {len(npm_failures)} failed",
                "success" if not npm_failures else "warn",
            )

    print_changes_summary(changes_summary)

    print()
    if args.dry_run:
        log("Dry run complete. No files were modified.", "warn")
    elif failed_files or npm_failures:
        if failed_files:
            log(f"Package update failures: {len(failed_files)}", "warn")
        if npm_failures:
            log(f"npm install failures: {len(npm_failures)}", "warn")
        return 1
    else:
        log("All requested updates completed successfully!", "success")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
