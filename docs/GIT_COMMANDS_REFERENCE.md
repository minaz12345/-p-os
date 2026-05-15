# P-OS Git Commands Reference Guide

**Purpose:** Quick reference for essential Git operations in P-OS workflow  
**Date:** 2026-05-10  
**Context:** Constitutional Quietness period - PR-only workflow enforced  

---

## ⚠️ IMPORTANT: Branch Protection Active

**Main branch is PROTECTED.** Direct pushes are blocked.

```
GH006: Protected branch update failed for refs/heads/main.
- Changes must be made through a pull request.
- Required status check "Constitutional Review / 🏛️ Constitutional Compliance Check" is expected.
```

**All changes to main MUST go through Pull Requests with Constitutional Agent review.**

---

## 🎯 Basic Git Commands

### 1. **git init** - Initialize a New Repository

Creates a new Git repository in the current directory.

```bash
git init
```

**Example:**
```bash
$ mkdir my-project
$ cd my-project
$ git init
Initialized empty Git repository in /path/to/my-project/.git/
```

This creates a `.git` folder that tracks all version control information.

---

### 2. **git clone** - Copy an Existing Repository

Downloads a repository from a remote source (like GitHub) to your local machine.

```bash
git clone <repository-url>
```

**Example:**
```bash
$ git clone https://github.com/minaz12345/-p-os.git
Cloning into '-p-os'...
remote: Enumerating objects: 15000, done.
remote: Counting objects: 100% (1000/1000), done.
Receiving objects: 100% (15000/15000), 12.5 MiB | 5.00 MiB/s
Resolving deltas: 100% (7500/7500), done.
```

You can also clone into a specific directory:
```bash
git clone <repository-url> <directory-name>
```

---

### 3. **git status** - Check Repository Status

Shows the current state of your working directory and staging area.

```bash
git status
```

**Example:**
```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to stage the file for commit)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        new-feature.js

nothing added to commit but untracked changes present (working directory)
```

---

### 4. **git add** - Stage Changes

Adds files to the staging area (preparing them for commit).

```bash
git add <file-name>
```

**Examples:**

Add a specific file:
```bash
$ git add README.md
```

Add all changes in the current directory:
```bash
$ git add .
```

Add all changes across the entire repository:
```bash
$ git add -A
```

Add changes interactively (choose which changes to stage):
```bash
$ git add -p
```

---

### 5. **git commit** - Save Changes to Repository

Creates a snapshot of your staged changes with a message describing what changed.

```bash
git commit -m "Your commit message"
```

**Examples:**

Basic commit with a message:
```bash
$ git commit -m "Add new feature to dashboard"
[main 1a2b3c4] Add new feature to dashboard
 1 file changed, 25 insertions(+)
```

Commit all modified files (without staging first):
```bash
$ git commit -am "Fix bug in login form"
```

Amend the previous commit (modify the last commit):
```bash
$ git commit --amend -m "Updated commit message"
```

---

### 6. **git push** - Send Changes to Remote Repository

Uploads your local commits to a remote repository (like GitHub).

```bash
git push <remote> <branch>
```

**Examples:**

Push to the main branch on origin (default remote):
```bash
$ git push origin main
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 342 bytes | 342.00 KiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), reused pack 0
To github.com:minaz12345/-p-os.git
   a1b2c3d..e4f5g6h main -> main
```

⚠️ **WARNING:** This will be **BLOCKED** by branch protection! Use Pull Requests instead.

Push a feature branch (allowed):
```bash
$ git push origin feature-branch
```

Push all branches:
```bash
$ git push origin --all
```

---

### 7. **git pull** - Fetch and Merge Remote Changes

Downloads changes from the remote repository and merges them into your local branch.

```bash
git pull <remote> <branch>
```

**Examples:**

Pull from main branch on origin:
```bash
$ git pull origin main
remote: Enumerating objects: 10, done.
remote: Counting objects: 100% (10/10), done.
Unpacking objects: 100% (6/6), done.
From github.com:minaz12345/-p-os
   e4f5g6h..i7j8k9l main -> origin/main
Updating e4f5g6h..i7j8k9l
Fast-forward
 README.md | 5 +++++
 1 file changed, 5 insertions(+)
```

Pull with automatic merge strategy:
```bash
$ git pull --rebase
```

---

## 🔄 P-OS Workflow Example (With Branch Protection)

Here's the correct workflow for P-OS with mandatory Constitutional Agent checks:

```bash
# 1. Clone the repository (one-time setup)
git clone https://github.com/minaz12345/-p-os.git
cd pos7

# 2. Create a feature branch (NEVER work directly on main)
git checkout -b feature/add-new-module

# 3. Make changes to files...
# Edit files, add new features, etc.

# 4. Check status
git status

# 5. Stage changes
git add .

# 6. Commit changes with descriptive message
git commit -m "feat: Add new monitoring module for constitutional health"

# 7. Push feature branch to remote
git push origin feature/add-new-module

# 8. Create Pull Request via GitHub web interface
#    - Go to: https://github.com/minaz12345/-p-os/pulls
#    - Click "New Pull Request"
#    - Select your feature branch → main
#    - Add title and description
#    - Submit PR

# 9. Wait for Constitutional Agent review (~19 seconds)
#    - Agent checks R1-R7 rules
#    - Verdict: PASS or FAIL
#    - If FAIL: fix violations and push new commits
#    - If PASS: request human review

# 10. After approval, merge PR via GitHub web interface
#     - Squash and merge (recommended)
#     - Or rebase and merge (preserves history)

# 11. Update local main branch
git checkout main
git pull origin main
```

---

## 🛡️ Branch Protection Rules (Active on main)

| Rule | Status | Purpose |
|------|--------|---------|
| **Require Pull Request** | ✅ ACTIVE | No direct commits to main |
| **Require Status Checks** | ✅ ACTIVE | Constitutional Agent must pass |
| **Required Check** | `Constitutional Review / 🏛️ Constitutional Compliance Check` | R1-R7 enforcement |
| **Include Administrators** | ✅ ACTIVE | Even admins must follow rules |
| **Allow Force Pushes** | ❌ BLOCKED | Prevents history rewriting |
| **Allow Deletions** | ❌ BLOCKED | Prevents branch deletion |
| **Require Linear History** | ✅ ACTIVE | Clean commit history |

---

## 🔍 Useful Git Commands for P-OS

### View Commit History
```bash
# Show last 10 commits
git log --oneline -10

# Show commits with dates and authors
git log --pretty=format:"%h - %an, %ar : %s"

# Show commits on a specific branch
git log origin/main --oneline
```

### Compare Changes
```bash
# See what changed since last commit
git diff HEAD~1

# Compare current branch with main
git diff main

# See staged changes before commit
git diff --staged
```

### Undo Operations
```bash
# Unstage a file (remove from staging area)
git reset HEAD <file>

# Discard local changes to a file
git checkout -- <file>

# Undo last commit (keep changes in working directory)
git reset --soft HEAD~1

# Undo last commit AND discard changes
git reset --hard HEAD~1  # ⚠️ DANGEROUS - irreversible
```

### Manage Branches
```bash
# List all branches
git branch -a

# Create new branch
git checkout -b feature/new-feature

# Switch to existing branch
git checkout main

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature
```

### Stash Changes (Save Work Temporarily)
```bash
# Stash current changes
git stash

# List stashed changes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{1}
```

---

## 📊 Quick Reference Table

| Command | Purpose | P-OS Context |
|---------|---------|--------------|
| `git init` | Initialize a new repository | One-time setup |
| `git clone <url>` | Copy a remote repository locally | First-time setup |
| `git status` | Check current status | Before every commit |
| `git add <file>` | Stage changes | Prepare for commit |
| `git commit -m "msg"` | Save staged changes | Atomic, descriptive messages |
| `git push <remote> <branch>` | Send changes to remote | Feature branches only |
| `git pull <remote> <branch>` | Fetch and merge remote changes | Keep local updated |
| `git checkout -b <branch>` | Create and switch to new branch | Always use feature branches |
| `git log --oneline` | View commit history | Understand project evolution |
| `git diff` | Compare changes | Review before commit |

---

## ⚠️ Common Mistakes to Avoid

### ❌ Mistake 1: Trying to Push Directly to Main
```bash
# WRONG - Will be blocked by branch protection
git checkout main
git add .
git commit -m "Quick fix"
git push origin main  # ❌ GH006 error

# CORRECT - Use feature branch + PR
git checkout -b fix/quick-fix
git add .
git commit -m "fix: Resolve issue with X"
git push origin fix/quick-fix
# Then create PR via GitHub web interface
```

### ❌ Mistake 2: Vague Commit Messages
```bash
# WRONG - Unclear what changed
git commit -m "Update stuff"
git commit -m "Fix bug"
git commit -m "Changes"

# CORRECT - Descriptive and specific
git commit -m "feat: Add constitutional health score endpoint"
git commit -m "fix: Resolve W11 flag detection in daily_observation.py"
git commit -m "docs: Update branch protection setup guide"
```

### ❌ Mistake 3: Large Monolithic Commits
```bash
# WRONG - Too many unrelated changes in one commit
git add .
git commit -m "Big update"

# CORRECT - Small, focused commits
git add pos/daily_observation.py
git commit -m "feat: Add W11 flag monitoring to daily observation"

git add docs/GITHUB_CLI_INSTALLATION_GUIDE.md
git commit -m "docs: Add GitHub CLI installation guide"
```

### ❌ Mistake 4: Forgetting to Pull Before Working
```bash
# WRONG - May cause merge conflicts
git checkout main
# ... make changes ...
git push origin main

# CORRECT - Always pull latest changes first
git checkout main
git pull origin main
git checkout -b feature/new-work
# ... make changes ...
git push origin feature/new-work
```

---

## 🎓 Git Best Practices for P-OS

### 1. **Commit Message Convention**
Use conventional commits format:
```
type: description

Optional longer description

type = feat | fix | docs | style | refactor | test | chore
```

**Examples:**
```
feat: Add daily observation script for v7.5 monitoring
fix: Correct W11 flag path from runtime to flags directory
docs: Update branch protection setup instructions
refactor: Simplify constitutional agent rule evaluation
test: Add unit tests for dry-run adoption analysis
chore: Update dependencies to latest versions
```

### 2. **Branch Naming Convention**
```
feature/<description>     # New features
fix/<description>         # Bug fixes
docs/<description>        # Documentation updates
refactor/<description>    # Code refactoring
test/<description>        # Test additions/updates
archive/<description>     # Certification archives
```

**Examples:**
```
feature/add-constitutional-metrics
fix/w11-flag-detection-path
docs/update-git-reference-guide
refactor/simplify-observer-class
test/add-daily-observation-tests
archive/certify-quietness-philosophy
```

### 3. **Atomic Commits**
Each commit should:
- ✅ Do ONE thing
- ✅ Be independently testable
- ✅ Have a clear purpose
- ✅ Not break the build

### 4. **Frequent Small Commits**
Better to have:
```
commit 1: Add basic observer class
commit 2: Implement W11 flag checking
commit 3: Add operator feedback collection
commit 4: Save reports to JSONL
```

Than:
```
commit 1: Complete daily observation system (huge monolith)
```

### 5. **Pull Early, Push Often**
- Pull from main before starting new work
- Push feature branches frequently (backup + visibility)
- Keep feature branches short-lived (< 1 week ideal)

---

## 🔗 Additional Resources

### P-OS Specific Documentation
- [CONSTITUTIONAL_QUIETNESS_MODE_ACTIVATED.md](../docs/CONSTITUTIONAL_QUIETNESS_MODE_ACTIVATED.md) - Quiet operations guide
- [MANUAL_BRANCH_PROTECTION_SETUP.md](../docs/MANUAL_BRANCH_PROTECTION_SETUP.md) - Manual setup alternative
- [FULL_CONSTITUTIONAL_SOVEREIGNTY_ACHIEVED.md](../docs/FULL_CONSTITUTIONAL_SOVEREIGNTY_ACHIEVED.md) - System overview

### External Resources
- **Git Official Docs:** https://git-scm.com/doc
- **GitHub CLI Docs:** https://cli.github.com/manual/
- **Conventional Commits:** https://www.conventionalcommits.org/
- **GitHub Flow:** https://docs.github.com/en/get-started/using-github/github-flow

---

## 💬 Final Notes

**Budowniczy,**

Git is the foundation of P-OS sovereignty. With branch protection active:

✅ **No direct pushes to main** - All changes require PRs  
✅ **Constitutional Agent reviews every PR** - R1-R7 enforcement  
✅ **Admin enforcement active** - Even you must follow the rules  
✅ **Linear history required** - Clean, readable commit log  

**The monotony test begins now.** Every PR, every commit, every merge is part of proving that constitutional governance works in routine operations.

**()()(())()()(())()()(())()()(())()()** 🛡️✨
