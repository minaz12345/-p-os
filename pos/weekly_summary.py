#!/usr/bin/env python3
"""
P-OS CLI Weekly Observation Summary

Generates weekly summaries from daily observation logs.
Run at the end of each week during the 30-day observation period.

Usage:
    python pos/weekly_summary.py          # auto-detect current week
    python pos/weekly_summary.py 2        # specific week number
    python pos/weekly_summary.py --week 2 # alternative syntax
"""

import json
import sys
from datetime import datetime
from pathlib import Path


class WeeklySummarizer:
    """Generates weekly summaries from daily observation data."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.observation_log = self.project_root / "pos" / "OBSERVATION_LOG.jsonl"
        self.observation_start = datetime(2026, 5, 10).date()

    def load_observation_data(self) -> list:
        """Load all daily observation records."""
        if not self.observation_log.exists():
            return []

        records = []
        with open(self.observation_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        continue

        return records

    def filter_week(self, records: list, week_number: int) -> list:
        """Filter records to specific week (1-indexed, 7 days each)."""
        start_day = (week_number - 1) * 7 + 1
        end_day = week_number * 7

        filtered = []
        for record in records:
            try:
                date_obj = datetime.fromisoformat(record.get("date", "")).date()
                day_number = (date_obj - self.observation_start).days + 1
                if start_day <= day_number <= end_day:
                    filtered.append(record)
            except Exception:
                continue

        return filtered

    def calculate_trends(self, records: list) -> dict:
        """Calculate trends from daily data."""
        if not records:
            return {"message": "Brak danych"}

        confidence_scores = [
            r.get("operator_feedback", {}).get("confidence_score")
            for r in records
            if r.get("operator_feedback", {}).get("confidence_score") is not None
        ]

        dry_run_rates = [
            r.get("automated_metrics", {})
             .get("dry_run_adoption", {})
             .get("adoption_rate", 0)
            for r in records
        ]

        audit_totals = [
            r.get("automated_metrics", {})
             .get("audit_logs", {})
             .get("total", 0)
            for r in records
        ]

        doc_consultations = [
            r.get("operator_feedback", {}).get("consulted_documentation", False)
            for r in records
            if "operator_feedback" in r
        ]

        # Trend kierunkowy: porównaj pierwszą połowę z drugą
        if len(confidence_scores) >= 2:
            trend = "poprawa" if confidence_scores[-1] > confidence_scores[0] else "stabilny"
        else:
            trend = "za malo danych"

        return {
            "days_with_data": len(records),
            "avg_confidence": round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else None,
            "confidence_trend": trend,
            "avg_dry_run_adoption": round(sum(dry_run_rates) / len(dry_run_rates), 1) if dry_run_rates else 0,
            "audit_log_growth": audit_totals[-1] - audit_totals[0] if len(audit_totals) >= 2 else 0,
            "doc_consultation_rate": round(sum(doc_consultations) / len(doc_consultations) * 100, 1) if doc_consultations else 0,
        }

    def identify_pain_points(self, records: list) -> list:
        return [
            {"date": r.get("date"), "issue": r["operator_feedback"]["pain_point"]}
            for r in records
            if r.get("operator_feedback", {}).get("pain_point")
        ]

    def identify_feature_requests(self, records: list) -> list:
        return [
            {"date": r.get("date"), "request": r["operator_feedback"]["feature_request"]}
            for r in records
            if r.get("operator_feedback", {}).get("feature_request")
        ]

    def _generate_recommendations(self, trends: dict, pain_points: list, feature_requests: list) -> list:
        recs = []

        avg_confidence = trends.get("avg_confidence")
        if avg_confidence is not None:
            if avg_confidence < 6:
                recs.append("Dodatkowe szkolenie operatora — pewność siebie poniżej progu")
                recs.append("Rozbuduj przykłady w QUICK_REFERENCE lub CLI_PRZEWODNIK")
            elif avg_confidence >= 8:
                recs.append("Wysoka pewność siebie — rozważ gotowość do v8.0")

        if trends.get("avg_dry_run_adoption", 0) < 30:
            recs.append("Niska adopcja dry-run — przypomnij operatorowi o korzyściach")

        if len(pain_points) > 3:
            recs.append(f"Uwaga: {len(pain_points)} zgłoszonych problemów — przejrzyj przed v8.0")

        if feature_requests:
            recs.append(f"Do przeglądu: {len(feature_requests)} propozycji funkcji na listę v8.0")

        recs.append("Kontynuuj codzienne obserwacje do końca tygodnia 4")
        return recs

    def generate_weekly_summary(self, week_number: int) -> dict:
        all_records = self.load_observation_data()
        week_records = self.filter_week(all_records, week_number)

        if not week_records:
            return {
                "week": week_number,
                "status": "BRAK_DANYCH",
                "message": f"Brak danych obserwacji dla tygodnia {week_number}. Czy uruchomiono daily_observation.py?",
            }

        trends = self.calculate_trends(week_records)
        pain_points = self.identify_pain_points(week_records)
        feature_requests = self.identify_feature_requests(week_records)

        insights = []
        avg_conf = trends.get("avg_confidence")
        if avg_conf:
            if avg_conf >= 8:
                insights.append("Wysoka pewność operatora — ergonomia CLI działa")
            elif avg_conf < 5:
                insights.append("Niska pewność — rozważ uproszczenie UX lub więcej szkolenia")

        dry = trends.get("avg_dry_run_adoption", 0)
        if dry > 50:
            insights.append("Wysoka adopcja dry-run — operator ceni bezpieczeństwo")
        elif dry < 20:
            insights.append("Niska adopcja dry-run — możliwe niezrozumienie korzyści")

        doc_rate = trends.get("doc_consultation_rate", 0)
        if doc_rate > 70:
            insights.append("Częste zaglądanie do dokumentacji — operator nadal buduje model mentalny")
        elif doc_rate < 30:
            insights.append("Rzadkie zaglądanie — operator działa z pamięci (dobry znak)")

        return {
            "week": week_number,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "period": {
                "start": week_records[0].get("date"),
                "end": week_records[-1].get("date"),
            },
            "data_points": len(week_records),
            "trends": trends,
            "pain_points": pain_points,
            "feature_requests": feature_requests,
            "insights": insights,
            "recommendations": self._generate_recommendations(trends, pain_points, feature_requests),
        }

    def print_summary(self, summary: dict):
        print("\n" + "=" * 70)
        print(f"P-OS CLI — PODSUMOWANIE TYGODNIA {summary['week']}")
        print("=" * 70)

        if summary.get("status") == "BRAK_DANYCH":
            print(f"\n⚠️  {summary.get('message')}")
            return

        print(f"\nOkres: {summary['period']['start']} — {summary['period']['end']}")
        print(f"Dni z danymi: {summary['data_points']}")

        print("\n--- TRENDY ---")
        t = summary.get("trends", {})
        if t.get("avg_confidence"):
            print(f"Średnia pewność siebie:  {t['avg_confidence']}/10 ({t.get('confidence_trend')})")
        print(f"Adopcja dry-run:          {t.get('avg_dry_run_adoption', 0)}%")
        print(f"Wzrost logów audytu:      {t.get('audit_log_growth', 0)} wpisów")
        print(f"Konsultacje dokumentacji: {t.get('doc_consultation_rate', 0)}% dni")

        if summary.get("pain_points"):
            print("\n--- PROBLEMY ---")
            for pp in summary["pain_points"]:
                print(f"  [{pp['date']}] {pp['issue']}")

        if summary.get("feature_requests"):
            print("\n--- PROPOZYCJE FUNKCJI ---")
            for req in summary["feature_requests"]:
                print(f"  [{req['date']}] {req['request']}")

        if summary.get("insights"):
            print("\n--- WNIOSKI ---")
            for insight in summary["insights"]:
                print(f"  • {insight}")

        if summary.get("recommendations"):
            print("\n--- REKOMENDACJE ---")
            for rec in summary["recommendations"]:
                print(f"  ✓ {rec}")

        print("\n" + "=" * 70)


def parse_week_arg() -> int:
    """
    Obsługuje dwie formy argumentu:
      python weekly_summary.py 2        (pozycyjny)
      python weekly_summary.py --week 2 (z flagą)

    POPRAWKA: Poprzedni kod używał tylko formy pozycyjnej,
    co nie zgadzało się z dokumentacją która mówiła --week N.
    """
    args = sys.argv[1:]

    if not args:
        # Auto-detekcja na podstawie daty
        today = datetime.utcnow().date()
        observation_start = datetime(2026, 5, 10).date()
        days_elapsed = (today - observation_start).days + 1
        week = max(1, min(4, (days_elapsed - 1) // 7 + 1))
        print(f"Auto-detekcja: tydzień {week} (dzień {days_elapsed} obserwacji)")
        return week

    # Forma: --week 2
    if "--week" in args:
        idx = args.index("--week")
        if idx + 1 < len(args):
            try:
                return max(1, min(4, int(args[idx + 1])))
            except ValueError:
                print(f"Błąd: '{args[idx + 1]}' nie jest numerem tygodnia")
                sys.exit(1)

    # Forma: 2 (pozycyjny)
    try:
        return max(1, min(4, int(args[0])))
    except ValueError:
        print(f"Błąd: '{args[0]}' nie jest numerem tygodnia (podaj 1-4)")
        sys.exit(1)


def main():
    week = parse_week_arg()

    summarizer = WeeklySummarizer()
    summary = summarizer.generate_weekly_summary(week)
    summarizer.print_summary(summary)

    summary_file = Path(__file__).parent / f"WEEKLY_SUMMARY_WEEK{week}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nPodsumowanie zapisane: {summary_file}")


if __name__ == "__main__":
    main()
