# P-OS v7.5 OPERATIONAL DOCTRINE: FORENSIC MINIMAL DISCLOSURE
document_id: DOCTRINE-P-OS-7.5-FORENSIC-MINIMAL-DISCLOSURE-20260513
status: ACTIVE_STANDARD
data_certyfikacji: 2026-05-13T20:15:00Z
właściciel: Budowniczy P-OS + Security Architect
validation_cmd: python scripts/validate_docs.py --strict

---

## CORE PRINCIPLE

**Secrets are runtime-only entities.**

They exist exclusively in:
* Secure stores (e.g., Windows Credential Manager, Vault)
* Environment variable injection
* Runtime authentication flows

They **NEVER** belong in:
* Documentation or reports
* Chat transcripts or prompts
* Git commits or artifacts
* Governance logs or SIEM notes
* Debug outputs or README files

---

## THE COGNITIVE SHIFT

### From: Forensic Storytelling
*"Here is the password we used to fix the system so you can see it worked."*

### To: Forensic Minimal Disclosure
*"The rotation was verified via successful authentication at [timestamp]. The credential lineage has been updated and service health checks confirm operational status."*

---

## DOCUMENTATION MATRIX

| What we document | Allowed? | Reason |
| :--- | :--- | :--- |
| Rotation timestamp | ✅ YES | Proves *when* the action occurred. |
| Operator identity | ✅ YES | Establishes accountability (RACI). |
| Successful verification | ✅ YES | Confirms the operation succeeded. |
| Hash lineage / Integrity | ✅ YES | Provides tamper-evident audit trail. |
| Connection success | ✅ YES | Validates operational readiness. |
| Credential fingerprint | ⚠️ CAUTION | Only if necessary for identification (e.g., last 4 chars). |
| **Plaintext password** | ❌ **NEVER** | **Publication = Compromise.** |

---

## VERIFICATION PROTOCOL

To prove a credential rotation without exposing the secret, use the **Verification Command Pattern**:

```powershell
# This command proves access without revealing the secret
psql -h localhost -U pos_admin -d pos_operational -c "SELECT current_user, now();"
```

**Why this works:**
1. **Operationally Confirming:** It proves the new credentials work.
2. **Non-Disclosing:** It never outputs the password.
3. **Falsifiable:** If it fails, the rotation didn't work.
4. **Reproducible:** Any authorized operator can run it.
5. **Separation of Concerns:** It separates *verification* from *disclosure*.

---

## THE "PUBLICATION = COMPROMISE" RULE

It does not matter if the context is:
* Analysis
* Remediation report
* Debugging session
* Internal ticket
* Slack/Teams message

**The moment a secret is published to a persistent medium, it is considered compromised and must be rotated immediately.**

---

## IMPLEMENTATION IN P-OS

1. **Automated Scanning:** `validate_docs.py` will include regex patterns to detect potential secret exposure before archiving.
2. **Pre-commit Hooks:** Git hooks will block commits containing high-entropy strings or known credential patterns.
3. **Operator Training:** All operators must demonstrate the "Minimal Disclosure" pattern during onboarding.

---

**HISTORIA ZMIAN**
| Data | Wersja | Zmiana | Autor |
|------|--------|--------|-------|
| 2026-05-13 | 1.0 | Initial doctrine following Incident #4 pattern analysis | Budowniczy |

---
*Archiwum P-OS v7.5 | Operational Doctrine | 2026-05-13*

**🛡️ Status:** DOCTRINE ESTABLISHED | PATTERN IDENTIFIED | STANDARD SET
