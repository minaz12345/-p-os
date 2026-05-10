# 🛡️ P-OS CLI - QUICK REFERENCE CARD

## Basic Commands

```bash
# Show help
pos --help

# Validate document
pos validate docs/file.md

# Check status
pos status

# Inspect flags
pos flags
```

## Essential Flags

```bash
# Dry-run (preview without executing)
pos validate docs/file.md --dry-run

# Verbose (show underlying commands)
pos validate docs/file.md --verbose

# Strict mode (for validation)
pos validate docs/ --strict

# Combine flags
pos validate docs/file.md --dry-run --verbose
```

## Global vs Per-Command Flags

```bash
# Global flags (apply to all commands)
pos --dry-run validate docs/file.md

# Per-command flags
pos validate docs/file.md --dry-run

# Both work the same way
```

## Audit Trails

```bash
# View recent audits
ls logs/cli_audit/

# Check specific audit
cat logs/cli_audit/pos-20260510-*.json

# Pretty-print JSON
python -m json.tool logs/cli_audit/pos-20260510-*.json
```

## Common Workflows

### Before Making Changes
```bash
# 1. Check current status
pos status

# 2. Preview validation
pos validate docs/ --dry-run --verbose

# 3. Execute validation
pos validate docs/
```

### Investigating Issues
```bash
# 1. Check flags
pos flags --verbose

# 2. Review audit logs
ls -lt logs/cli_audit/ | head

# 3. Run with verbose output
pos status --verbose
```

### Safe Testing
```bash
# Always use dry-run first
pos validate docs/new-file.md --dry-run

# If satisfied, execute
pos validate docs/new-file.md

# Verify in audit log
cat logs/cli_audit/pos-*.json | tail
```

## Manual Fallback

CLI is optional. Original scripts still work:

```bash
# Using CLI
pos validate docs/file.md

# Direct script (same result)
python scripts/validate_docs.py docs/file.md
```

## Troubleshooting

### Command not found?
```bash
# Use python -m pos
python -m pos --help

# Or use wrapper
.\pos.bat --help        # Windows
./pos.sh --help         # Unix/Mac
```

### Need more details?
```bash
# Add --verbose flag
pos validate docs/file.md --verbose

# Check audit logs
cat logs/cli_audit/pos-*.json
```

### Want to see what would happen?
```bash
# Use --dry-run
pos validate docs/file.md --dry-run
```

## Correlation IDs

Every operation gets a unique ID:
- Format: `pos-YYYYMMDD-HHMMSS-XXXXXX`
- Example: `pos-20260510-060624-52c0c7`
- Used for tracking in audit logs

## Quick Health Check

```bash
# Full system check
pos status && pos flags

# With details
pos status --verbose && pos flags --verbose
```

## Safety Rules

✅ **DO:**
- Use `--dry-run` before new operations
- Check audit logs regularly
- Use `--verbose` when learning
- Fall back to scripts if needed

❌ **DON'T:**
- Skip dry-run for critical operations
- Ignore audit trails
- Assume CLI hides complexity
- Depend solely on CLI (scripts are primary)

## Support

- **Docs:** `pos/README.md`
- **Tests:** `python pos/test_cli.py`
- **Logs:** `logs/cli_audit/`
- **Emergency:** ops@milejczyce.gov.pl

---

**Version:** 7.5.0  
**Last Updated:** 2026-05-10  
**Status:** OPERATIONAL ✅
