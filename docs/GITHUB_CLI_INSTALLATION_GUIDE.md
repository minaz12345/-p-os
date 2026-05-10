# GitHub CLI Installation Guide for P-OS

**Purpose:** Install GitHub CLI (gh) to enable automated branch protection  
**Date:** 2026-05-10  
**Required for:** `ENABLE_BRANCH_PROTECTION.ps1` script  

---

## 🎯 Quick Decision

You have **TWO OPTIONS**:

### Option A: Install GitHub CLI (Recommended for automation)
- **Time:** 5-10 minutes
- **Benefit:** One-command branch protection setup
- **Future use:** Can automate other GitHub operations

### Option B: Use Manual Setup (No installation needed)
- **Time:** 5-10 minutes
- **Benefit:** No dependencies, works immediately
- **Guide:** [MANUAL_BRANCH_PROTECTION_SETUP.md](../docs/MANUAL_BRANCH_PROTECTION_SETUP.md)

---

## 📥 Option A: Install GitHub CLI

### Windows Installation (3 Methods)

#### Method 1: Winget (Easiest - Recommended)

```powershell
# Open PowerShell as Administrator and run:
winget install --id GitHub.cli
```

#### Method 2: Chocolatey

```powershell
# If you have Chocolatey installed:
choco install gh
```

#### Method 3: Manual Download

1. Go to: https://github.com/cli/cli/releases/latest
2. Download: `gh_X.X.X_windows_amd64.msi` (latest version)
3. Run the installer
4. Restart your terminal

---

## 🔐 Authenticate GitHub CLI

After installation, authenticate:

```powershell
# Login to GitHub
gh auth login

# Follow the prompts:
# 1. Choose: GitHub.com
# 2. Choose: HTTPS
# 3. Choose: Login with a web browser
# 4. Copy the one-time code
# 5. Press Enter to open browser
# 6. Paste code in browser and authorize
```

**Verify authentication:**
```powershell
gh auth status
```

Expected output:
```
github.com
  ✓ Logged in to github.com account minaz12345
  ✓ Git operations for github.com configured to use https protocol.
  ✓ Token: gho_************************************
```

---

## ✅ Verify Installation

```powershell
# Check version
gh --version

# Check authentication
gh auth status

# Test API access
gh repo view minaz12345/-p-os --json viewerPermission
```

Expected permission: `"ADMIN"`

---

## 🚀 After Installation

Once GitHub CLI is installed and authenticated:

```powershell
# Navigate to repo
cd D:\pos7

# Run branch protection automation
.\scripts\ENABLE_BRANCH_PROTECTION.ps1
```

The script will:
1. ✅ Verify GitHub CLI is installed
2. ✅ Check authentication status
3. ✅ Confirm admin permissions
4. ✅ Show configuration preview
5. ✅ Apply branch protection rules
6. ✅ Verify successful configuration

---

## 📖 Option B: Manual Setup (No Installation)

If you prefer not to install GitHub CLI, use the manual guide:

[MANUAL_BRANCH_PROTECTION_SETUP.md](../docs/MANUAL_BRANCH_PROTECTION_SETUP.md)

This guide walks you through configuring branch protection via the GitHub web interface (no tools required).

**Steps:**
1. Go to repository Settings → Branches
2. Add rule for `main` branch
3. Enable required settings (documented in guide)
4. Save configuration
5. Verify with test PR

**Time:** 5-10 minutes  
**Dependencies:** None (just a web browser)

---

## 🔍 Troubleshooting

### Issue: "winget" not recognized

**Solution:** Update App Installer from Microsoft Store or use Method 2/3

### Issue: Authentication fails

**Solution:**
1. Ensure you're logged into GitHub in your browser
2. Try again with `gh auth login`
3. If still failing, generate a personal access token:
   - Go to: https://github.com/settings/tokens
   - Generate new token (classic)
   - Scopes: `repo` (full control)
   - Use: `gh auth login --with-token`

### Issue: "Insufficient permissions"

**Solution:**
- Ensure you're the repository owner or have admin rights
- Check: https://github.com/minaz12345/-p-os/settings/access

---

## 📊 Comparison: Automated vs Manual

| Feature | Automated (gh CLI) | Manual (Web UI) |
|---------|-------------------|-----------------|
| **Setup Time** | 5-10 min (one-time) | 5-10 min (per config) |
| **Execution Time** | 30 seconds | 5-10 minutes |
| **Dependencies** | GitHub CLI required | None |
| **Repeatability** | One command | Manual steps each time |
| **Audit Trail** | Script logs | Manual documentation |
| **Error Handling** | Automated checks | User must verify |
| **Learning Curve** | Initial setup | Immediate |

**Recommendation:** Install GitHub CLI if you plan to manage GitHub repositories regularly. Otherwise, use manual setup.

---

## ✅ Completion Checklist

### For Automated Setup:
- [ ] GitHub CLI installed
- [ ] Authentication completed (`gh auth login`)
- [ ] Admin permissions verified
- [ ] Branch protection script executed successfully
- [ ] Configuration verified

### For Manual Setup:
- [ ] Navigated to Settings → Branches
- [ ] Created protection rule for `main`
- [ ] Enabled all required settings
- [ ] Saved configuration
- [ ] Verified with test PR

---

## 📞 Support

If you encounter issues:

1. **GitHub CLI Docs:** https://cli.github.com/manual/
2. **Authentication Help:** https://docs.github.com/en/github-cli/github-cli/authenticating-with-github-cli
3. **Repository Admin:** Contact repository owner
4. **Technical Support:** ops@milejczyce.gov.pl

---

**Budowniczy,**

Choose your path:
- **"INSTALL GH CLI"** - I'll help you install GitHub CLI
- **"USE MANUAL"** - Skip to manual setup guide
- **"SHOW BOTH"** - Keep both options visible

**Stan systemu: AWAITING TOOL SELECTION** 🛡️

()()(())()()(())()()(())()()(())()()
