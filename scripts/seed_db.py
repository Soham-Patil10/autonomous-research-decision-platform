"""Populate the demo analytics database.

Make the data *interesting*: the German margin should be worse than the French one
for a reason the documents explain. A dataset with no story in it cannot demonstrate
that your agents found the story.
"""

from __future__ import annotations

import random
from datetime import date

from sqlalchemy import text

from app.db.session import engine

random.seed(42)

MARKETS = [("Germany", "EU", "EUR"), ("France", "EU", "EUR"), ("Ireland", "EU", "EUR")]


def main() -> None:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO companies (name, home_market, founded_year) "
                          "VALUES ('Acme Mobility', 'Ireland', 2016) ON CONFLICT DO NOTHING"))
        for country, region, currency in MARKETS:
            conn.execute(
                text("INSERT INTO markets (country, region, currency) VALUES (:c, :r, :cur) "
                     "ON CONFLICT (country) DO NOTHING"),
                {"c": country, "r": region, "cur": currency},
            )

        # TODO(v1): 36 months of revenue_monthly per market, EV registrations 2019-2025,
        # and a competitor table where the top-3 German share is genuinely concentrated.
        _ = date

    print("seeded")


if __name__ == "__main__":
    main()
