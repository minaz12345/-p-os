# P-OS v7.5 — Runbook Operacyjny

**Cel:** Procedury operacyjne dla codziennej obsługi P-OS  
**Data:** 2026-05-11  
**Wersja:** 7.5  
**Status:** ✅ OPERACYJNY

---

## 📋 SPIS TREŚCI

1. [Codzienne Sprawdzenia](#codzienne-sprawdzenia)
2. [Procedury Awaryjne](#procedury-awaryjne)
3. [Backup i Recovery](#backup-i-recovery)
4. [Monitorowanie i Alerty](#monitorowanie-i-alerty)

---

## CODZIENNE SPRAWDZENIA

### Checklist Poranny (Każdego dnia o 08:00)

```powershell
# 1. Sprawdź status systemu
cd D:\pos7
python -m pos status

# Oczekiwany wynik:
# ✅ Constitutional State: HEALTHY
# ✅ W11: ACTIVE
# ✅ Audit Chain: VERIFIED

# 2. Sprawdź aktywne flagi
python -m pos flags

# Oczekiwany wynik:
# ✅ Brak aktywnych flag *.flag w katalogu flags/

# 3. Sprawdź logi audytu
Get-ChildItem D:\pos7\logs\cli_audit -Filter "pos-$(Get-Date -Format 'yyyyMMdd')*.json" | Measure-Object

# Oczekiwany wynik:
# ✅ Co najmniej 1 entry dla dzisiejszej daty

# 4. Uruchom obserwację dzienną
python pos/daily_observation.py --auto

# Oczekiwany wynik:
# ✅ Raport zapisany do pos/OBSERVATION_LOG.jsonl
```

### Checklist Tygodniowy (Każdy poniedziałek)

```powershell
# 1. Generuj raport tygodniowy
python pos/weekly_summary.py

# 2. Sprawdź integralność backupów
Test-Path D:\pos7\data\backups\latest

# 3. Zweryfikuj chain audytu
python scripts/capture_forensic_baseline.py

# 4. Przegląd alertów Grafana
# Sprawdź dashboard: http://localhost:3000/d/p-os-health
```

