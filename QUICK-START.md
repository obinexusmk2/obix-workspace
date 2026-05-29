# TypeScript Updater - Quick Start

## One-Command Fix

```powershell
# Windows PowerShell
cd C:\Users\Nnamdi\Documents\obix\obix
..\update-typescript-deps.ps1 -Install
```

```bash
# macOS/Linux
cd ~/obix/obix
../update-typescript-deps.sh --install
```

## What It Does (30 seconds)

1. **Finds** all `package.json` files in workspace
2. **Locks** TypeScript to `~5.4.0` (compatible with typescript-eslint@8.60.0)
3. **Removes** `obix-workspace` reference from dependencies
4. **Installs** locked versions via `npm install`

## The Problem It Solves

```
npm error ERESOLVE unable to resolve dependency tree
peer typescript@">=4.8.4 <6.1.0" from typescript-eslint@8.60.0
```

**Solution:** Explicitly lock TypeScript version across all packages.

## Three-Step Workflow

### Step 1: Preview (No Changes)
```powershell
..\update-typescript-deps.ps1 -DryRun -Verbose
```
Read the output to verify all changes look correct.

### Step 2: Apply Updates
```powershell
..\update-typescript-deps.ps1
```
All `package.json` files are updated with locked versions.

### Step 3: Build
```bash
npm run build
```
Should now complete without ERESOLVE errors.

## Expected Output

```
✓ Found 87 package.json files
ℹ TypeScript will be locked to: ~5.4.0
...
✓ Updated 87/87 package.json files
ℹ npm install: 87 succeeded, 0 failed
✅ All updates completed successfully!
```

## If Something Goes Wrong

```bash
# Quick fallback (legacy peer deps)
npm install --legacy-peer-deps
npm run build
```

## Version Lock Explanation

| Range | Meaning | Example |
|-------|---------|---------|
| `^5.4.0` | Any 5.x | ✗ Conflicts |
| `~5.4.0` | Only 5.4.x | ✓ **USED** |
| `5.4.0` | Exact | Too strict |

The tilde `~` ensures patch updates (security) but blocks minor updates (stability).

---

**Need more info?** → Read `TYPESCRIPT-UPDATE-README.md`
