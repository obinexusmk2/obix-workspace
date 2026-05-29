# OBINexus TypeScript Dependency Updater

## Overview
This toolset automatically updates all `package.json` files in the OBINexus workspace to use a consistent, locked TypeScript version and removes `obix-workspace` references from dependency trees.

### What it does:
1. ✓ Scans all `package.json` files in the workspace
2. ✓ Locks TypeScript to `~5.4.0` (tilde lock = any patch version within 5.4.x)
3. ✓ Removes `obix-workspace` from all dependency lists
4. ✓ Runs `npm install` to update package-lock.json files
5. ✓ Generates a detailed report of all changes

## Quick Start

### Option 1: PowerShell (Recommended for Windows)

```powershell
# Navigate to obix workspace root
cd C:\Users\Nnamdi\Documents\obix\obix

# Dry run first (see what will change)
.\update-typescript-deps.ps1 -DryRun -Verbose

# Apply changes and install
.\update-typescript-deps.ps1 -Install
```

### Option 2: Direct Python

```bash
cd C:\Users\Nnamdi\Documents\obix\obix

# Dry run
python ../update-typescript-deps.py --dry-run --verbose

# Apply changes
python ../update-typescript-deps.py

# Apply and show verbose output
python ../update-typescript-deps.py --verbose
```

## Command-line Options

### Python Script
```
python update-typescript-deps.py [OPTIONS]

Options:
  --dry-run     Show what would change without modifying files
  --verbose     Print detailed information about each change
```

### PowerShell Wrapper
```powershell
.\update-typescript-deps.ps1 [OPTIONS]

Options:
  -DryRun       Show what would change without modifying files
  -Verbose      Print detailed information about each change
  -Install      Run full workspace npm install after updates
```

## Recommended Workflow

### Step 1: Dry Run (No Changes)
```powershell
.\update-typescript-deps.ps1 -DryRun -Verbose
```

This will show you:
- How many `package.json` files will be updated
- What changes will be made to each file
- Which dependencies will be removed
- No files are modified

### Step 2: Review Output
Examine the report to ensure all changes are expected. Look for:
- ✓ All TypeScript versions updated to `~5.4.0`
- ✓ All `obix-workspace` references removed
- ✓ No unexpected dependency changes

### Step 3: Apply Changes
```powershell
.\update-typescript-deps.ps1 -Install
```

This will:
1. Update all `package.json` files
2. Run `npm install` in each updated package
3. Lock versions in `package-lock.json` files

## Dependency Lock Strategy

### Before Update
```json
{
  "devDependencies": {
    "typescript": "^5.4.0"  // Allows 5.x.x
  }
}
```

### After Update
```json
{
  "devDependencies": {
    "typescript": "~5.4.0"  // Locks to 5.4.x only
  }
}
```

**Tilde Lock Behavior:**
- `~5.4.0` = `>=5.4.0 <5.5.0` (allows patch updates only)
- Safer than `^` (which allows minor updates)
- Matches production stability requirements

## Resolving the ERESOLVE Conflict

The peer dependency conflict between:
- `@obinexusltd/obix-config-eslint` (requires `typescript@5.4.0`)
- `typescript-eslint@8.60.0` (requires `typescript@>=4.8.4 <6.1.0`)

Is resolved by:
1. **Locking TypeScript version** to a compatible version in all packages
2. **Using `npm install --legacy-peer-deps`** as fallback if needed

## Troubleshooting

### npm install still fails after update
```bash
npm install --legacy-peer-deps
npm run build
```

### Python script not found
Ensure you're running from the obix workspace root:
```powershell
cd C:\Users\Nnamdi\Documents\obix\obix
# Then run the script from parent directory
python ../update-typescript-deps.py
```

### Permission denied on PowerShell
Enable script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Need to revert changes
Git makes this easy:
```bash
git status  # See changed files
git diff package.json  # Review changes
git checkout .  # Revert all changes
```

## Session State (OBINexus Continuity)

**Status:** In Recovery - Dependency Resolution Phase  
**Blocker:** ERESOLVE conflict resolved by TypeScript lock  
**Build Status:** Ready for `npm run build` after update  
**Next Phase:** riftlang.exe → .so.a compilation  

## Script Structure

```
obix/
├── update-typescript-deps.py    # Main Python updater
├── update-typescript-deps.ps1   # PowerShell wrapper
└── TYPESCRIPT-UPDATE-README.md  # This file
```

## Technical Details

### What Files Are Updated
- All `package.json` files found recursively in the workspace
- Includes workspace root and all sub-packages
- Workspace definitions (glob patterns) are preserved

### What Gets Locked
- `devDependencies.typescript` → `~5.4.0`
- Removes `obix-workspace` from any dependency section
- Preserves all other dependencies

### What Gets Installed
- After each `package.json` update, `npm install` runs
- Creates/updates `package-lock.json` for that package
- Ensures consistent dependency resolution

## Success Indicators

✓ All package.json files updated  
✓ No errors during npm install  
✓ `npm run build` completes without ERESOLVE errors  
✓ All workspaces have `node_modules/typescript` locally available  

## Further Help

For detailed TypeScript version information:
```bash
npm view typescript versions --json | head -20
npm view typescript@5.4.0
```

For workspace diagnostics:
```bash
npm query .workspace  # List all workspaces
npm ls typescript     # Show typescript versions across workspace
```
