# P-OS v7.5 — Przewodnik Operatora CLI

**Cel:** Kompletny przewodnik obsługi interfejsu linii poleceń P-OS  
**Data:** 2026-05-11  
**Wersja:** 7.5  
**Status:** ✅ OPERACYJNY

---

## 📋 SPIS TREŚCI

1. [Wprowadzenie](#wprowadzenie)
2. [Instalacja i Konfiguracja](#instalacja-i-konfiguracja)
3. [Podstawowe Komendy](#podstawowe-komendy)
4. [Tryby Operacyjne](#tryby-operacyjne)
5. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)

---

## WPROWADZENIE

P-OS CLI to **konstytucyjny interfejs operacyjny** zapewniający:
- ✅ Pełną przejrzystość operacji
- ✅ Ślad audytowy z ID korelacji
- ✅ Deterministyczną odtwarzalność
- ✅ Manualne override'y zawsze dostępne
- ✅ Transparentność ponad wygodę

**Filozofia:** Brak ukrytej logiki lub automatyzacji black-box.

---

## INSTALACJA I KONFIGURACJA

### Wymagania Systemowe
- Python 3.12+
- Windows PowerShell 7+ lub Linux bash
- Dostęp do katalogu projektu P-OS

### Szybki Start

```powershell
# Przejdź do katalogu projektu
cd D:\pos7

# Sprawdź status systemu
python -m pos status

# Waliduj dokument
python -m pos validate docs/file.md

# Sprawdź flagi operacyjne
python -m pos flags
```

---

## PODSTAWOWE KOMENDY

### 1. `pos status` — Status Systemu

Wyświetla aktualny stan runtime P-OS:
- Stan konstytucyjny (W11)
- Flagi runtime
- Zdrowie systemu

**Użycie:**
```powershell
python -m pos status
python -m pos status --verbose    # Szczegółowy output
python -m pos status --dry-run    # Podgląd bez wykonania
```

**Przykładowy Output:**
```
Constitutional State:
 w11                    ACTIVE
 state                  HEALTHY
 audit_chain            VERIFIED

Runtime Flags (Recent):
  [W11_CHECK] PASS
  [RUNTIME_GUARD] OK

System Health:
 CPU Usage              12%
 Memory Usage           45%
 Disk Usage             67%
```

