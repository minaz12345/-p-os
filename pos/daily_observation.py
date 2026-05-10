#!/usr/bin/env python3
"""
P-OS CLI Daily Observation Checklist

Automated daily checks for the 30-day v7.5 observation period.
Run this script once per day to collect telemetry and operator feedback.

Usage:
    python pos/daily_observation.py           # tryb interaktywny
    python pos/daily_observation.py --auto    # tryb automatyczny, bez pytań
"""

import json
import sys
from datetime import datetime
from pathlib import Path


class DailyObserver:
    """Collects daily operational metrics during v7.5 observation period."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.audit_dir = self.project_root / "logs" / "cli_audit"
        self.observation_log = self.project_root / "pos" / "OBSERVATION_LOG.jsonl"
        self.flags_dir = self.project_root / "flags"  # D:\pos7\flags\
        self.today = datetime.utcnow().date()

    def check_pos_status(self) -> dict:
        """Run pos status and capture output."""
        import subprocess

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pos", "status"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "exit_code": result.returncode,
                "output_length": len(result.stdout),
                "has_errors": result.returncode != 0,
            }
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "exit_code": -1,
                "error": str(e),
            }

    def count_audit_logs(self) -> dict:
        """Count audit logs created today."""
        if not self.audit_dir.exists():
            return {"total": 0, "today": 0}

        all_logs = list(self.audit_dir.glob("pos-*.json"))
        today_str = self.today.strftime("%Y%m%d")
        today_logs = [log for log in all_logs if today_str in log.stem]

        return {
            "total": len(all_logs),
            "today": len(today_logs),
        }

    def analyze_dry_run_adoption(self) -> dict:
        """Analyze dry-run vs execution ratio from audit logs."""
        if not self.audit_dir.exists():
            return {"dry_run_count": 0, "execution_count": 0, "adoption_rate": 0}

        all_logs = list(self.audit_dir.glob("pos-*.json"))
        dry_run_count = 0
        execution_count = 0

        for log_file in all_logs:
            try:
                with open(log_file, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    if data.get("dry_run", False):
                        dry_run_count += 1
                    else:
                        execution_count += 1
            except Exception:
                continue

        total = dry_run_count + execution_count
        adoption_rate = (dry_run_count / total * 100) if total > 0 else 0

        return {
            "dry_run_count": dry_run_count,
            "execution_count": execution_count,
            "adoption_rate": round(adoption_rate, 2),
        }

    def check_w11_flag_activations(self) -> dict:
        """
        Sprawdza aktywne flagi W11 w D:\\pos7\\flags\\*.flag

        POPRAWKA: Poprzedni kod szukał pliku runtime/runtime_guard.log
        który nie istnieje w v7.5. Flagi W11 są plikami w katalogu flags/.
        """
        if not self.flags_dir.exists():
            return {
                "activations": 0,
                "active_flags": [],
                "flags_dir": str(self.flags_dir),
                "flags_dir_exists": False,
                "system_state": "HEALTHY",  # No flags = healthy
            }

        active_flags = list(self.flags_dir.glob("*.flag"))

        flag_details = []
        for flag_path in active_flags:
            try:
                content = flag_path.read_text(encoding="utf-8").strip()
                stat = flag_path.stat()
                flag_details.append({
                    "name": flag_path.name,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "content_preview": content[:120],  # pierwsze 120 znaków
                })
            except Exception as e:
                flag_details.append({
                    "name": flag_path.name,
                    "error": str(e),
                })

        return {
            "activations": len(active_flags),
            "active_flags": flag_details,
            "flags_dir": str(self.flags_dir),
            "flags_dir_exists": True,
            "system_state": "HEALTHY" if len(active_flags) == 0 else "DEGRADED",
        }

    def measure_document_usage(self) -> dict:
        """
        Sprawdza czy dokumenty operatorskie istnieją i kiedy były tworzone.

        POPRAWKA: Poprzedni kod śledził st_mtime (czas modyfikacji), nie odczytu.
        Czytanie dokumentu nie zmienia st_mtime — więc tracking był ślepy.
        Na Windows st_atime (access time) też jest zawodny (często wyłączony).

        Zamiast tego: odnotowujemy że dokumenty ISTNIEJĄ i podajemy ich rozmiar.
        Faktyczne śledzenie użycia robimy przez pytanie operatora (feedback).
        """
        docs_to_check = [
            self.project_root / "docs" / "NON_GOALS_AND_BOUNDARIES_PL.md",
            self.project_root / "docs" / "OPERATIONAL_STABILITY_DIRECTIVE_PL.md",
            self.project_root / "docs" / "CLI_PRZEWODNIK_OPERATORA_PL.md",
            self.project_root / "docs" / "RUNBOOK_P-OS_v7_5.md",
        ]

        found = []
        missing = []

        for doc in docs_to_check:
            if doc.exists():
                stat = doc.stat()
                found.append({
                    "file": doc.name,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                })
            else:
                missing.append(doc.name)

        return {
            "documents_found": len(found),
            "documents_missing": len(missing),
            "missing_names": missing,
            "details": found,
            "note": "Faktyczne uzycie sledzone przez pytanie operatora w sekcji feedback",
        }

    def collect_operator_feedback(self) -> dict:
        """Prompt for manual operator feedback (interactive mode only)."""
        print("\n" + "=" * 70)
        print("FEEDBACK OPERATORA")
        print("=" * 70)
        print(f"Data: {self.today.isoformat()}")
        print()

        feedback = {}

        # Pytanie 1: Pewność siebie
        print("1. Jak pewnie czujesz się używając P-OS CLI? (1-10)")
        print("   1 = cały czas zaglądasz do dokumentacji")
        print("   10 = działasz z pamięci, bez podpowiedzi")
        try:
            confidence = int(input("   Twoja ocena: "))
            feedback["confidence_score"] = max(1, min(10, confidence))
        except ValueError:
            feedback["confidence_score"] = None

        # Pytanie 2: Użycie dokumentacji
        print("\n2. Czy zaglądałeś dzisiaj do dokumentacji? (t/n)")
        doc_usage = input("   Odpowiedź: ").strip().lower()
        feedback["consulted_documentation"] = doc_usage in ("t", "tak", "y", "yes")

        # Pytanie 3: Która dokumentacja
        if feedback["consulted_documentation"]:
            print("\n   Który dokument? (wpisz nazwę lub fragment)")
            doc_name = input("   Dokument: ").strip()
            feedback["documentation_consulted"] = doc_name if doc_name else None

        # Pytanie 4: Problem dnia
        print("\n3. Co było dziś najbardziej irytujące? (Enter = nic)")
        pain_point = input("   Opisz: ").strip()
        feedback["pain_point"] = pain_point if pain_point else None

        # Pytanie 5: Czego brakowało
        print("\n4. Czy chciałeś żeby P-OS coś umiał czego nie umie? (Enter = nie)")
        feature_request = input("   Opisz: ").strip()
        feedback["feature_request"] = feature_request if feature_request else None

        # Pytanie 6: Czas operacyjny
        print("\n5. Ile minut spędziłeś dzisiaj na operacjach P-OS?")
        try:
            time_spent = int(input("   Minuty: "))
            feedback["time_spent_minutes"] = max(0, time_spent)
        except ValueError:
            feedback["time_spent_minutes"] = None

        print()
        return feedback

    def run_daily_check(self, interactive: bool = False) -> dict:
        """Run complete daily observation check."""
        print("=" * 70)
        print(f"P-OS CLI DZIENNY RAPORT - {self.today.isoformat()}")
        print("=" * 70)
        print()

        print("Uruchamiam automatyczne sprawdzenia...")

        status_check = self.check_pos_status()
        status_msg = 'OK' if status_check['exit_code'] == 0 else 'BLAD'
        print(f"[OK] Status gateway: {status_msg}")

        audit_count = self.count_audit_logs()
        print(f"[OK] Logi audytu: {audit_count['today']} nowych, {audit_count['total']} lacznie")

        dry_run_analysis = self.analyze_dry_run_adoption()
        print(f"[OK] Adopcja dry-run: {dry_run_analysis['adoption_rate']}%")

        w11_check = self.check_w11_flag_activations()
        state_symbol = "[OK]" if w11_check["system_state"] == "HEALTHY" else "[BLAD]"
        print(f"[OK] Flagi W11: {w11_check['activations']} aktywnych - {state_symbol} {w11_check['system_state']}")
        if w11_check["activations"] > 0:
            for flag in w11_check["active_flags"]:
                print(f"  [!] {flag['name']} (od: {flag.get('created', 'nieznane')})")

        doc_usage = self.measure_document_usage()
        print(f"[OK] Dokumenty: {doc_usage['documents_found']} znalezionych")
        if doc_usage.get("missing_names"):
            print(f"  [!] Brakuje: {', '.join(doc_usage['missing_names'])}")

        daily_report = {
            "date": self.today.isoformat(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "automated_metrics": {
                "status_check": status_check,
                "audit_logs": audit_count,
                "dry_run_adoption": dry_run_analysis,
                "w11_activations": w11_check,
                "document_usage": doc_usage,
            },
        }

        if interactive:
            feedback = self.collect_operator_feedback()
            daily_report["operator_feedback"] = feedback

        self.save_daily_report(daily_report)

        print()
        print("=" * 70)
        print(f"Raport zapisany: {self.observation_log}")
        print("=" * 70)

        return daily_report

    def save_daily_report(self, report: dict):
        """Append daily report to observation log."""
        self.observation_log.parent.mkdir(parents=True, exist_ok=True)

        with open(self.observation_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")


def main():
    observer = DailyObserver()

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        observer.run_daily_check(interactive=False)
    else:
        observer.run_daily_check(interactive=True)


if __name__ == "__main__":
    main()
