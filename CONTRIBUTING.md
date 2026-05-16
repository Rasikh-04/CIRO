# CIRO Team Workflow Guide

## Setup (First Time Only)

```bash
git clone https://github.com/Rasikh-04/CIRO.git
cd CIRO
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## Daily Workflow

### 1. Start a Feature Branch
```bash
git fetch origin
git checkout -b <your-name>/<feature-name>
```

**Branch naming examples:**
```
tabeen/agent-1-fix
tabeen/agent-2-detection
ahmar/backend-setup
ahmar/agent-4-dispatch
abdul/web-dashboard-maps
```

### 2. Make Changes & Commit
```bash
git add <your-files-only>
git commit -m "Brief description of what you changed"
git push origin <your-branch-name>
```

**Commit often.** Small, focused commits are easier to review and less likely to conflict.

### 3. Open a Pull Request
On GitHub: create a PR from your branch → `main`. Abdul will review and merge.

---

## File Ownership — Avoid Conflicts

**Stay in your assigned folder.** This is the #1 way to prevent merge conflicts.

| Owner | Owns These Folders | 
|---|---|
| **Tabeen** | `agents/agent_1_*`, `agents/agent_2_*`, `agents/agent_3_*` |
| **Ahmar** | `backend/`, `agents/agent_4_*`, `agents/agent_5_*` |
| **Abdul** | `web-dashboard/`, `mobile-app/`, `agents/agent_6_*`, `.agy_rules` files |

**Do NOT edit files outside your folder.** If you need to change a shared file (README, CLAUDE.md, etc.), ask first.

---

## Best Practices to Avoid Conflicts

✅ **DO:**
- Pull latest `main` before starting work: `git fetch origin && git merge origin/main`
- Push your changes daily — don't accumulate uncommitted work
- Keep commits small and focused on one thing
- Ask before modifying shared files

❌ **DON'T:**
- Work directly on `main` — always use a feature branch
- Edit files outside your folder
- Commit `.env`, `node_modules/`, `__pycache__/`, or build artifacts
- Wait days before pushing — merge conflicts get worse with time
- Merge your own PRs — let Abdul review

---

## If Your Branch Gets Behind

```bash
git fetch origin
git merge origin/main
# If there are conflicts, git will tell you. Fix them and:
git add .
git commit -m "Merge latest main"
git push origin <your-branch-name>
```

---

## Quick Git Cheat Sheet

| Command | Purpose |
|---|---|
| `git fetch origin` | Get latest from GitHub (safe, no changes) |
| `git checkout -b name/feature` | Create & switch to new branch |
| `git status` | See what you've changed |
| `git add <file>` | Stage a file for commit |
| `git commit -m "msg"` | Commit staged changes |
| `git push origin <branch>` | Push your branch to GitHub |
| `git merge origin/main` | Update your branch with latest main |

---

## Questions?

ASK!
