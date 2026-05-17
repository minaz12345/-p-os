#!/usr/bin/env python3
"""
morning.py - Poranny/wieczorny punkt startowy P-OS + Milejczyce
Użycie: python morning.py  (lub: python scripts/morning.py)

Świadomy pory dnia:
  08:00-10:00  Poranek       — sprawdza bazy, uruchamia obserwację
  10:00-20:00  Dzień         — szybki status
  20:00-22:00  Wieczór       — status + pytania o dzień
  22:00-23:00  Późny wieczór — krótki status
  23:00+       Noc           — przypomnienie żeby kończyć
"""

import json
import os
import subprocess
import sys
from datetime import datetime


OK   = "OK"
FAIL = "BLAD"
WARN = "UWAGA"


def linia():
    print("=" * 60)


def naglowek(tekst):
    linia()
    print(f"  {tekst}")
    linia()


def status_linia(ikona, tekst):
    print(f"[{ikona}] {tekst}")


def pora_dnia(godzina):
    if godzina < 8:
        return "noc"
    elif 8 <= godzina < 10:
        return "poranek"
    elif 10 <= godzina < 20:
        return "dzien"
    elif 20 <= godzina < 22:
        return "wieczor"
    elif 22 <= godzina < 23:
        return "pozny_wieczor"
    else:  # godzina >= 23
        return "noc"


def wczytaj_env():
    env = {}
    for sciezka in [".env.db", ".env"]:
        if os.path.exists(sciezka):
            with open(sciezka, encoding="utf-8-sig") as f:
                for ln in f:
                    ln = ln.strip()
                    if ln and "=" in ln and not ln.startswith("#"):
                        k, _, v = ln.partition("=")
                        env[k.strip()] = v.strip()
            break
    return env


def sprawdz_postgres(env):
    print()
    print("PostgreSQL:")
    try:
        import psycopg2
    except ImportError:
        status_linia(WARN, "psycopg2 brak — pip install psycopg2-binary")
        return

    host     = env.get("POSTGRESQL_HOST", "localhost")
    port     = env.get("POSTGRESQL_PORT", "5432")
    user     = env.get("POSTGRESQL_USER", env.get("POS_ADMIN_USER", "pos_admin"))
    password = env.get("POSTGRESQL_PASSWORD", env.get("POS_ADMIN_PASSWORD", ""))

    for baza in ["pos_operational", "milejczyce_operational"]:
        try:
            conn = psycopg2.connect(
                host=host, port=port, dbname=baza,
                user=user, password=password,
                connect_timeout=5
            )
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'"
            )
            tabele = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM pg_stat_activity WHERE datname=%s", (baza,)
            )
            polaczenia = cur.fetchone()[0]
            conn.close()
            status_linia(OK, f"{baza}: {tabele} tabel, {polaczenia} połączeń")
        except Exception as e:
            status_linia(FAIL, f"{baza}: {str(e).split(chr(10))[0][:55]}")


def sprawdz_neo4j(env):
    print()
    print("Neo4j:")
    try:
        from neo4j import GraphDatabase
    except ImportError:
        status_linia(WARN, "neo4j brak — pip install neo4j")
        return

    uri      = env.get("NEO4J_URI", "bolt+ssc://localhost:7687")
    user_n   = env.get("NEO4J_USER", "neo4j")
    password = env.get("NEO4J_PASSWORD", "")

    try:
        driver = GraphDatabase.driver(uri, auth=(user_n, password))
        with driver.session() as s:
            wezly   = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            relacje = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            etyk    = s.run(
                "CALL db.labels() YIELD label RETURN count(label) AS c"
            ).single()["c"]
        driver.close()
        status_linia(OK, f"Neo4j: {wezly} węzłów, {relacje} relacji, {etyk} etykiet")
    except Exception as e:
        status_linia(WARN, f"Neo4j offline: {str(e).split(chr(10))[0][:50]}")
        status_linia(WARN, "Uruchom Neo4j Desktop jeśli potrzebujesz grafu")


def znajdz_skrypt(nazwa):
    base = os.path.dirname(os.path.abspath(__file__))
    kandydaci = [
        os.path.join(base, "pos", nazwa),
        os.path.join(base, "..", "pos", nazwa),
        os.path.join(base, nazwa),
    ]
    return next((s for s in kandydaci if os.path.exists(s)), None)


def znajdz_log():
    base = os.path.dirname(os.path.abspath(__file__))
    kandydaci = [
        os.path.join(base, "pos", "OBSERVATION_LOG.jsonl"),
        os.path.join(base, "..", "pos", "OBSERVATION_LOG.jsonl"),
    ]
    for s in kandydaci:
        if os.path.exists(s):
            return s
    # Jeśli nie istnieje — zwróć pierwszy możliwy
    return kandydaci[0]


def uruchom_obserwacje():
    print()
    print("Dzienny raport P-OS:")
    skrypt = znajdz_skrypt("daily_observation.py")
    if not skrypt:
        status_linia(WARN, "Nie znaleziono pos/daily_observation.py")
        return
    try:
        wynik = subprocess.run(
            [sys.executable, skrypt, "--auto"],
            capture_output=True, text=True, timeout=60
        )
        for ln in wynik.stdout.splitlines():
            if any(x in ln for x in ["[OK]", "[BLAD]", "[UWAGA]", "Raport zapisany"]):
                print(" ", ln.strip())
        if wynik.returncode != 0 and wynik.stderr:
            status_linia(WARN, wynik.stderr.strip()[:80])
    except subprocess.TimeoutExpired:
        status_linia(FAIL, "Timeout — daily_observation.py nie odpowiedział")
    except Exception as e:
        status_linia(FAIL, str(e)[:80])


def wieczorne_pytania():
    print()
    print("Podsumowanie dnia:")
    print()

    pytania = [
        ("Co dziś zrobiłeś z systemem?", "co_zrobiles"),
        ("Co nie działało lub frustrowało?", "frustracje"),
        ("Plan na jutro:",                   "plan_jutro"),
    ]

    odpowiedzi = {}
    for pytanie, klucz in pytania:
        print(f"  {pytanie}")
        try:
            odp = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            odp = ""
        odpowiedzi[klucz] = odp if odp else None
        print()

    if any(v for v in odpowiedzi.values()):
        log_path = znajdz_log()
        wpis = {
            "date": datetime.now().date().isoformat(),
            "timestamp": datetime.now().isoformat() + "Z",
            "type": "wieczorne_podsumowanie",
            "wieczor": odpowiedzi,
        }
        try:
            os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(wpis, ensure_ascii=False) + "\n")
            print(f"  Zapisano: {log_path}")
        except Exception as e:
            status_linia(WARN, f"Nie udało się zapisać: {e}")


def main():
    teraz    = datetime.now()
    godzina  = teraz.hour
    pora     = pora_dnia(godzina)
    czas_str = teraz.strftime("%Y-%m-%d %H:%M:%S")

    env = wczytaj_env()

    if pora == "poranek":
        naglowek(f"DOBRY RANEK — {czas_str}")
        sprawdz_postgres(env)
        sprawdz_neo4j(env)
        uruchom_obserwacje()

    elif pora == "dzien":
        naglowek(f"STATUS — {czas_str}")
        sprawdz_postgres(env)
        sprawdz_neo4j(env)

    elif pora == "wieczor":
        naglowek(f"DOBRY WIECZÓR — {czas_str}")
        sprawdz_postgres(env)
        sprawdz_neo4j(env)
        uruchom_obserwacje()
        wieczorne_pytania()

    elif pora == "pozny_wieczor":
        naglowek(f"PÓŹNO — {czas_str}")
        sprawdz_postgres(env)
        sprawdz_neo4j(env)
        print()
        print("  System sprawdzony. Dobranoc.")

    else:  # noc, przed 8 lub po 23
        naglowek(f"P-OS — {czas_str}")
        print()
        if godzina < 8:
            print("  Jest przed 8:00.")
            print("  System gotowy na poranek. Miłego dnia!")
        else:
            print("  Jest po 23:00.")
            print("  Jutro będzie system. Idź spać.")
        print()
        sprawdz_postgres(env)
        sprawdz_neo4j(env)

    print()
    linia()


if __name__ == "__main__":
    main()
