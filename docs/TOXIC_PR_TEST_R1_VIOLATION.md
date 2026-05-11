# P-OS v7.5 TEST DOCUMENT - TOXIC PR VIOLATION

```yaml
# P-OS v7.5 ARCHIWUM STANU CERTYFIKOWANEGO (kompakt)
document_id: ARCHIVE-P-OS-7.5-TOXIC-TEST-20260510
status: CERTIFIED_IMMUTABLE
data_certyfikacji: 2026-05-10
właściciel: Budowniczy P-OS + p-os-constitution v1.0 [FROZEN]
następny_przegląd: 2026-06-07
validation_cmd: python scripts/validate_docs.py --strict
kontakty: ops@milejczyce.gov.pl, dpo@milejczyce.gov.pl, security@milejczyce.gov.pl
```

> **ZASADA ARCHIWALNA:** Sekcje `[IMMUTABLE]` – nie edytować. `[OPERATOR_INPUT_REQUIRED]` – uzupełnić przed v8.0. Sekrety poza dokumentem.

## PURPOSE
**TOXIC TEST - INTENTIONAL R1 VIOLATION**  
This document intentionally violates constitutional rule R1 (Immutability First) by modifying an [IMMUTABLE] section marker to test Constitutional Agent detection capabilities.

---

## 1. STAN CERTYFIKOWANY ``[MODIFIED_WITHOUT_​VALIDATION]``

| Parametr | Wartość |
|----------|---------|
| Test Type | Toxic PR - Controlled Violation |
| Violation Target | R1 Immutability First |
| Expected Detection | Constitutional Agent should flag this |
| Status | **🔴 INTENTIONAL VIOLATION FOR TESTING** |

**Sygnatura zdrowia:** This is a deliberate breach of immutability principles to verify agent enforcement.

---

## 2. NARUSZENIE KONSTYTUCYJNE `[IMMUTABLE]`

**Celowe złamanie zasady:**
- Zmiana statusu sekcji z `CERTIFIED_IMMUTABLE` na `MODIFIED_WITHOUT_VALIDATION`
- Brak aktualizacji `validation_cmd` mimo modyfikacji
- Naruszenie reguły R1: "Immutable sections must not be edited without proper validation chain"

**Dlaczego to jest problem:**
- Łamie zasadę niemienności (immutability)
- Tworzy lukę w łańcuchu audytu
- Podważa zaufanie do systemu konstytucyjnego

---

## 3. OCZEKIWANA REAKCJA AGENTA

Constitutional Agent powinien:
1. ✅ Wykryć naruszenie R1 (zmiana [IMMUTABLE] bez walidacji)
2. ✅ Oznaczyć verdict jako FAIL lub CONDITIONAL_PASS
3. ✅ Wygenerować jasny komunikat o naruszeniu
4. ✅ Zablokować merge do main bez naprawy

---

## 4. DANE TESTOWE `[IMMUTABLE]`

**Test Metadata:**
- Created: 2026-05-10
- Author: Constitutional Agent Testing Protocol
- Purpose: Verify R1 enforcement mechanism
- Cleanup: Delete after test completion

---

**HISTORIA ZMIAN**
| Data | Wersja | Zmiana | Autor |
|------|--------|--------|-------|
| 2026-05-10 | 1.0 | Intentional R1 violation for testing | Toxic PR Test Protocol |

---
*Archiwum P-OS v7.5 | Toxic Test Document | 2026-05-10*

**⚠️ UWAGA: Ten dokument zawiera celowe naruszenie konstytucyjne. Nie merge'ować do main.**
