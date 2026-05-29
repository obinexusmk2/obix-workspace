#!/usr/bin/env python3
"""
OBINexus TypeScript Dependency Updater
Scans all package.json files in the workspace and:
1. Locks TypeScript to a specific minor version (tilde lock)
2. Removes obix-workspace references from dependencies
3. Runs npm install to update package-lock.json
4. Generates a report of changes
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
TYPESCRIPT_VERSION = "5.4.0"  # Will be locked as ~5.4.0
WORKSPACE_ROOT = Path(__file__).parent / "obix"
DRY_RUN = "--dry-run" in sys.argv
VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv

# Color codes for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(message: str, level: str = "info"):
    """Print colored log messages."""
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


def find_package_jsons() -> List[Path]:
    """Find all package.json files in the workspace."""
    if not WORKSPACE_ROOT.exists():
        log(f"Workspace root not found: {WORKSPACE_ROOT}", "error")
        return []

    package_files = list(WORKSPACE_ROOT.rglob("package.json"))
    log(f"Found {len(package_files)} package.json files", "info")
    return package_files


def update_package_json(file_path: Path) -> Tuple[bool, Dict]:
    """
    Update a package.json file:
    - Add typescript@~5.4.0 to devDependencies
    - Remove obix-workspace from dependencies
    Returns: (changed, changes_dict)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log(f"Failed to parse {file_path}: {e}", "error")
        return False, {}

    changes = {}

    # Initialize devDependencies if not present
    if "devDependencies" not in data:
        data["devDependencies"] = {}

    # Update TypeScript version (tilde lock to minor)
    old_ts_version = data["devDependencies"].get("typescript")
    new_ts_version = f"~{TYPESCRIPT_VERSION}"

    if old_ts_version != new_ts_version:
        data["devDependencies"]["typescript"] = new_ts_version
        changes["typescript"] = {
            "old": old_ts_version,
            "new": new_ts_version
        }

    # Remove obix-workspace from dependencies
    for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
        if dep_type in data and "obix-workspace" in data[dep_type]:
            removed = data[dep_type].pop("obix-workspace")
            if "removed" not in changes:
                changes["removed"] = {}
            changes["removed"][dep_type] = removed

    if not changes:
        return False, {}

    # Write back to file
    if not DRY_RUN:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")  # Add trailing newline
        except IOError as e:
            log(f"Failed to write {file_path}: {e}", "error")
            return False, changes

    return True, changes


def run_npm_install(file_path: Path) -> bool:
    """Run npm install in the directory containing package.json."""
    if DRY_RUN:
        log(f"[DRY RUN] Would run: npm install in {file_path.parent}", "info")
        return True

    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return True
        else:
            if VERBOSE:
                log(f"npm install failed in {file_path.parent}:\n{result.stderr}", "warn")
            return False
    except subprocess.TimeoutExpired:
        log(f"npm install timed out in {file_path.parent}", "warn")
        return False
    except Exception as e:
        log(f"Failed to run npm install in {file_path.parent}: {e}", "error")
        return False


def main():
    """Main execution."""
    log("OBINexus TypeScript Dependency Updater", "info")

    if DRY_RUN:
        log("Running in DRY RUN mode (no changes will be made)", "warn")

    log(f"TypeScript will be locked to: ~{TYPESCRIPT_VERSION}", "info")
    print()

    # Find all package.json files
    package_files = find_package_jsons()

    if not package_files:
        log("No package.json files found", "error")
        return 1

    # Update each package.json
    updated_files = []
    failed_files = []
    changes_summary = {}

    for i, pkg_file in enumerate(package_files, 1):
        rel_path = pkg_file.relative_to(WORKSPACE_ROOT)

        try:
            changed, changes = update_package_json(pkg_file)

            if changed:
                updated_files.append(pkg_file)
                changes_summary[str(rel_path)] = changes
                log(f"[{i}/{len(package_files)}] Updated: {rel_path}", "success")

                if VERBOSE and changes:
                    for key, value in changes.items():
                        if key == "removed":
                            for dep_type, version in value.items():
                                print(f"    Removed {key} ({dep_type}): {version}")
                        elif isinstance(value, dict) and "old" in value:
                            print(f"    {key}: {value['old']} → {value['new']}")
            else:
                if VERBOSE:
                    log(f"[{i}/{len(package_files)}] No changes: {rel_path}", "info")
        except Exception as e:
            failed_files.append(pkg_file)
            log(f"[{i}/{len(package_files)}] Error processing {rel_path}: {e}", "error")

    print()
    log(f"Updated {len(updated_files)}/{len(package_files)} package.json files", "info")

    # Optionally run npm install
    if updated_files and not DRY_RUN:
        print()
        log("Running npm install in updated packages...", "info")

        npm_success = 0
        npm_failed = 0

        for pkg_file in updated_files:
            if run_npm_install(pkg_file):
                npm_success += 1
            else:
                npm_failed += 1

        log(f"npm install: {npm_success} succeeded, {npm_failed} failed", "info")

    # Print summary
    if changes_summary:
        print()
        log("Changes Summary:", "info")
        for file_path, changes in changes_summary.items():
            print(f"\n  {file_path}")
            for key, value in changes.items():
                if key == "removed":
                    for dep_type, version in value.items():
                        print(f"    - Removed {key} from {dep_type}: {version}")
                elif isinstance(value, dict) and "old" in value:
                    print(f"    - {key}: {value['old']} → {value['new']}")

    # Final status
    print()
    if DRY_RUN:
        log("Dry run complete. No files were modified.", "warn")
    else:
        if failed_files:
            log(f"Completed with {len(failed_files)} errors", "warn")
            return 1
        else:
            log("All updates completed successfully!", "success")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
