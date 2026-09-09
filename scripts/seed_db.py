"""Seed the demo analytics database with a story worth uncovering.

    python scripts/seed_db.py --dry-run                     # print, touch nothing
    python scripts/seed_db.py                               # write to Postgres
    python scripts/seed_db.py --registrations acea.csv      # use real ACEA/KBA numbers

Scope is EU-27 members only: 14 markets, 2022-2025. Norway and the UK are excluded
on purpose - both are large EV markets, neither is in the EU, and conflating them is
the most common error in EV market analysis. If the agent quietly pulls Norway in
from a web source, that is a factual error your critics should catch.

THE PLANTED STORY
-----------------
Across 14 markets, Acme's gross margin is flat everywhere except where a government
withdrew a purchase subsidy. Two markets have a cliff, and they happen in DIFFERENT
YEARS - this is the point:

    Sweden      klimatbonus abolished abruptly in Nov 2022 -> margin breaks in 2023
    Germany     Umweltbonus terminated abruptly in Dec 2023 -> margin breaks in 2024

An agent that pattern-matches "something bad happened in 2024" finds Germany and
stops. Only an agent that looks for the *mechanism* finds both and generalises:
abrupt subsidy withdrawal destroys margin; gradual tapering does not.

Three legs, each visible to exactly one specialist:

    SQL only        Which markets have a margin discontinuity, in which year, and
                    how large. Nothing about why - policy data is deliberately NOT
                    in the database.

    Web only        Sweden ended klimatbonus Nov 2022. Germany ended Umweltbonus
                    Dec 2023. France restructured rather than ended. The
                    Netherlands tapered. That asymmetry is the cause.

    Corpus only     (a) AFIR (Reg. EU 2023/1804) charging obligations raise the
                        cost of entry in every market.
                    (b) Acme's pricing policy sets a 15% margin floor with a
                        mandatory escalation - so the cliffs are a POLICY BREACH.
                    (c) A take-or-pay battery contract explains why COGS stayed
                        high when volume fell.

A correct report finds both cliffs, attributes the common cause, and prices in AFIR.
Finding only Germany is the near-miss the completeness critic must catch.

SECOND PLANT: STALE DATA
------------------------
`competitors` holds 2023 shares only. Ask who leads a market *now* and the database
answers with year-old rows while the corpus answers with current ones.

THIRD PLANT: PROVENANCE
-----------------------
`ev_registrations.source` marks each row 'reported' or 'estimated'. Smaller markets
are estimated. An agent that cites an estimated figure as established fact, without
saying so, is making an error - and the column gives the fact critic what it needs
to catch it.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

random.seed(42)

YEARS = (2022, 2023, 2024, 2025)


# --------------------------------------------------------------------------- #
# Markets
#
# `regime` drives the margin trajectory. Confidence notes refer to the real-world
# policy claim, which the web agent must independently confirm - they are here for
# YOU, not for the model.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Market:
    country: str
    region: str
    population_m: float
    scale: float           # relative monthly unit volume vs Germany = 1.0
    baseline_margin: float
    regime: str
    policy_note: str
    confidence: str        # confidence in the real policy claim: high | medium | low


MARKETS: list[Market] = [
    # ---- the two cliffs: the whole point of the dataset ----
    Market("Germany", "Western", 83.3, 1.00, 0.220, "cliff_2024",
           "Umweltbonus terminated abruptly Dec 2023", "high"),
    Market("Sweden", "Nordic", 10.5, 0.22, 0.215, "cliff_2023",
           "Klimatbonus abolished abruptly Nov 2022", "high"),

    # ---- controls: incentive maintained or restructured ----
    Market("France", "Western", 68.1, 0.71, 0.210, "stable",
           "Bonus ecologique restructured (eco-score) rather than withdrawn", "high"),
    Market("Belgium", "Western", 11.7, 0.26, 0.205, "stable",
           "Company-car taxation strongly favours BEV; fleet-driven", "medium"),
    Market("Spain", "Southern", 48.4, 0.31, 0.195, "stable",
           "MOVES III extended", "medium"),

    # ---- tapers: gradual withdrawal, NOT a cliff. The contrast that proves
    #      the mechanism is abruptness, not the mere absence of a subsidy.  ----
    Market("Netherlands", "Western", 17.9, 0.30, 0.212, "taper",
           "SEPP private-purchase subsidy declining year on year", "medium"),
    Market("Denmark", "Nordic", 5.9, 0.14, 0.208, "taper",
           "Registration-tax phase-in raising effective BEV price", "medium"),
    Market("Poland", "CEE", 36.7, 0.16, 0.185, "taper",
           "Moj elektryk budget-limited", "low"),

    # ---- volatile: stop-start policy. Noise the agent must not mistake
    #      for a cliff.                                                     ----
    Market("Italy", "Southern", 58.9, 0.34, 0.190, "volatile",
           "Ecobonus repeatedly paused and relaunched", "medium"),

    # ---- quiet markets ----
    Market("Austria", "Western", 9.1, 0.13, 0.200, "stable",
           "Purchase bonus maintained", "medium"),
    Market("Portugal", "Southern", 10.5, 0.11, 0.192, "stable", "", "low"),
    Market("Ireland", "Western", 5.3, 0.09, 0.190, "taper",
           "SEAI grant tapering", "medium"),
    Market("Finland", "Nordic", 5.6, 0.08, 0.198, "stable", "", "low"),
    Market("Czechia", "CEE", 10.9, 0.07, 0.180, "stable", "", "low"),
]

# Margin multiplier by regime, per year in YEARS order (2022, 2023, 2024, 2025).
# A cliff halves margin the year AFTER withdrawal, then partially recovers -
# partially, because discounting becomes structural and AFIR costs land on top.
REGIME_MARGIN: dict[str, tuple[float, ...]] = {
    "stable":     (1.00, 0.99, 0.99, 0.98),
    "cliff_2024": (1.00, 1.00, 0.50, 0.68),
    "cliff_2023": (1.00, 0.52, 0.66, 0.74),
    "taper":      (1.00, 0.95, 0.89, 0.83),
    "volatile":   (1.00, 0.87, 1.03, 0.89),
}

# Unit-volume multiplier. Cliffs cost volume too, but less than margin - because
# Acme discounted to defend share. That gap IS the story.
REGIME_VOLUME: dict[str, tuple[float, ...]] = {
    "stable":     (1.00, 1.08, 1.14, 1.20),
    "cliff_2024": (1.00, 1.12, 0.78, 0.94),
    "cliff_2023": (1.00, 0.74, 0.88, 1.00),
    "taper":      (1.00, 1.05, 1.02, 1.04),
    "volatile":   (1.00, 0.92, 1.10, 1.01),
}

GERMANY_BASE_UNITS = 900
GERMANY_ASP_EUR = 42_000

# Registrations peak in March and December across most EU markets.
SEASONALITY = [0.82, 0.88, 1.24, 1.02, 1.00, 1.06, 0.95, 0.84, 1.10, 0.98, 0.95, 1.16]


# --------------------------------------------------------------------------- #
# Reference BEV registrations.
#
# WARNING: approximate, written from memory, placeholders. Rows generated from
# this table are marked source='estimated' unless listed in REPORTED below.
# Replace by downloading the ACEA "new car registrations by power source" series
# (EU-27, per country) and passing it via --registrations.
# --------------------------------------------------------------------------- #
REPORTED_BEV: dict[str, dict[int, int]] = {
    # Reasonable confidence on these; still verify before presenting them.
    "Germany": {2022: 470_559, 2023: 524_219, 2024: 380_609},
    "France":  {2022: 203_121, 2023: 298_522, 2024: 290_531},
}

# Rough per-capita BEV registration rate (registrations per million people) used
# to synthesise every other market. Deliberately crude: these rows are labelled
# 'estimated' in the database precisely because they are.
ESTIMATED_RATE_PER_M = {2022: 2_800, 2023: 3_600, 2024: 3_300, 2025: 4_100}

# 2023 shares only - see "SECOND PLANT". Illustrative, not researched.
COMPETITORS_2023 = [
    ("Volkswagen Group", "Germany", 21.4),
    ("Tesla", "Germany", 13.8),
    ("Mercedes-Benz Group", "Germany", 9.1),
    ("BMW Group", "Germany", 8.7),
    ("Stellantis", "France", 26.9),
    ("Renault Group", "France", 19.3),
    ("Tesla", "France", 11.5),
    ("Volvo Cars", "Sweden", 24.1),
    ("Tesla", "Sweden", 14.7),
    ("Stellantis", "Italy", 22.8),
    ("Tesla", "Netherlands", 16.2),
    ("Volkswagen Group", "Poland", 15.9),
]


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
@dataclass
class RevenueRow:
    market: str
    month: date
    units: int
    revenue_eur: float
    cogs_eur: float


def generate_revenue() -> list[RevenueRow]:
    rows: list[RevenueRow] = []

    for market in MARKETS:
        margins = REGIME_MARGIN[market.regime]
        volumes = REGIME_VOLUME[market.regime]

        for year_index, year in enumerate(YEARS):
            base_units = GERMANY_BASE_UNITS * market.scale * volumes[year_index]
            year_margin = market.baseline_margin * margins[year_index]

            # Cliff markets discount hard; that is why margin falls faster than volume.
            asp = GERMANY_ASP_EUR * (0.92 if margins[year_index] < 0.7 else 1.0)

            for month_index in range(12):
                units = max(1, round(base_units * SEASONALITY[month_index]
                                     * random.uniform(0.94, 1.06)))
                revenue = units * asp * random.uniform(0.985, 1.015)
                margin = year_margin * random.uniform(0.96, 1.04)

                rows.append(
                    RevenueRow(
                        market=market.country,
                        month=date(year, month_index + 1, 1),
                        units=units,
                        revenue_eur=round(revenue, 2),
                        cogs_eur=round(revenue * (1.0 - margin), 2),
                    )
                )
    return rows


def build_registrations(
    override: Path | None,
) -> tuple[list[tuple[str, int, int, str]], int]:
    """Return [(market, year, registrations, source)], plus the estimated-row count.

    CSV override header: market,year,registrations[,source]
    """
    if override is not None:
        rows: list[tuple[str, int, int, str]] = []
        with override.open(encoding="utf-8-sig", newline="") as fh:
            for record in csv.DictReader(fh):
                rows.append(
                    (
                        record["market"].strip(),
                        int(record["year"]),
                        int(record["registrations"]),
                        record.get("source", "reported").strip() or "reported",
                    )
                )
        if not rows:
            raise SystemExit(f"{override} produced no rows (header: market,year,registrations)")
        estimated = sum(1 for r in rows if r[3] == "estimated")
        return rows, estimated

    rows = []
    estimated = 0
    for market in MARKETS:
        for year in YEARS:
            reported = REPORTED_BEV.get(market.country, {}).get(year)
            if reported is not None:
                rows.append((market.country, year, reported, "reported"))
            else:
                count = round(market.population_m * ESTIMATED_RATE_PER_M[year])
                rows.append((market.country, year, count, "estimated"))
                estimated += 1
    return rows, estimated


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def print_story(rows: list[RevenueRow], registrations: list[tuple[str, int, int, str]]) -> None:
    yearly: dict[str, dict[int, float]] = {}
    for market in MARKETS:
        yearly[market.country] = {}
        for year in YEARS:
            subset = [r for r in rows if r.market == market.country and r.month.year == year]
            revenue = sum(r.revenue_eur for r in subset)
            cogs = sum(r.cogs_eur for r in subset)
            yearly[market.country][year] = (revenue - cogs) / revenue if revenue else 0.0

    print("\nAnnual gross margin by EU market - what the SQL agent must discover:\n")
    row_fmt = "  {:<13}" + "{:>8.1%}" * len(YEARS) + "  {:<11}{:>8.1f}pp{}"
    head_fmt = "  {:<13}" + "{:>8}" * len(YEARS) + "  {:<11}{:>10}"
    print(head_fmt.format("market", *YEARS, "regime", "worst YoY"))
    print("  " + "-" * 13 + " " + "-" * (8 * len(YEARS) - 1) + "  " + "-" * 11 + "-" * 10)

    for market in MARKETS:
        series = [yearly[market.country][y] for y in YEARS]
        drops = [(series[i] - series[i - 1]) * 100 for i in range(1, len(series))]
        worst = min(drops)
        flag = "  <-- CLIFF" if worst < -7 else ""
        print(row_fmt.format(market.country, *series, market.regime, worst, flag))

    cliffs = [m.country for m in MARKETS if m.regime.startswith("cliff")]
    print(f"\n  Cliffs planted in: {', '.join(cliffs)} - in different years, on purpose.")

    reported = sum(1 for r in registrations if r[3] == "reported")
    print(
        f"\nRegistrations: {len(registrations)} rows "
        f"({reported} reported, {len(registrations) - reported} estimated)"
    )


def write_db(rows: list[RevenueRow], registrations: list[tuple[str, int, int, str]]) -> None:
    from sqlalchemy import text  # imported late so --dry-run needs no driver

    from app.db.session import engine

    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE revenue_monthly, competitors, ev_registrations RESTART IDENTITY")
        )
        conn.execute(
            text(
                "INSERT INTO companies (name, home_market, founded_year) "
                "VALUES ('Acme Mobility', 'Ireland', 2016) ON CONFLICT DO NOTHING"
            )
        )

        for market in MARKETS:
            conn.execute(
                text(
                    "INSERT INTO markets (country, region, currency, population_m, eu_member) "
                    "VALUES (:c, :r, 'EUR', :p, TRUE) ON CONFLICT (country) DO UPDATE "
                    "SET region = EXCLUDED.region, population_m = EXCLUDED.population_m"
                ),
                {"c": market.country, "r": market.region, "p": market.population_m},
            )

        market_ids = {
            country: mid
            for country, mid in conn.execute(text("SELECT country, id FROM markets")).all()
        }
        company_id = conn.execute(text("SELECT id FROM companies LIMIT 1")).scalar_one()

        conn.execute(
            text(
                "INSERT INTO revenue_monthly "
                "(company_id, market_id, month, units, revenue_eur, cogs_eur) "
                "VALUES (:co, :m, :month, :u, :rev, :cogs)"
            ),
            [
                {
                    "co": company_id,
                    "m": market_ids[r.market],
                    "month": r.month,
                    "u": r.units,
                    "rev": r.revenue_eur,
                    "cogs": r.cogs_eur,
                }
                for r in rows
            ],
        )

        conn.execute(
            text(
                "INSERT INTO competitors (name, market_id, market_share, year) "
                "VALUES (:n, :m, :s, 2023)"
            ),
            [
                {"n": name, "m": market_ids[country], "s": share}
                for name, country, share in COMPETITORS_2023
                if country in market_ids
            ],
        )

        conn.execute(
            text(
                "INSERT INTO ev_registrations (market_id, year, registrations, powertrain, source) "
                "VALUES (:m, :y, :n, 'BEV', :src)"
            ),
            [
                {"m": market_ids[country], "y": year, "n": count, "src": source}
                for country, year, count, source in registrations
                if country in market_ids
            ],
        )

    print(
        f"\nwrote {len(rows)} revenue rows across {len(MARKETS)} markets, "
        f"{len(registrations)} registration rows"
    )


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the EU demo analytics database.")
    parser.add_argument("--dry-run", action="store_true", help="print the story, write nothing")
    parser.add_argument(
        "--registrations",
        type=Path,
        help="CSV of real registrations (header: market,year,registrations[,source])",
    )
    args = parser.parse_args()

    rows = generate_revenue()
    registrations, estimated = build_registrations(args.registrations)

    print_story(rows, registrations)

    if args.registrations is None:
        print(
            "\n  WARNING: no --registrations file given.\n"
            f"  {estimated} rows are synthesised from population and marked\n"
            "  source='estimated' in the database. Only Germany and France carry\n"
            "  approximate real figures, and those are from memory - verify them.\n"
            "  Download the ACEA EU-27 registrations series and re-run with\n"
            "  --registrations, or the database will contradict your own corpus."
        )

    if args.dry_run:
        print("\ndry run - nothing written")
        return 0

    write_db(rows, registrations)
    print("seeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
