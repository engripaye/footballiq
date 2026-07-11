from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


ADDITIVE_COLUMNS = {
    "teams": {
        "provider_id": "INTEGER",
        "league_id": "INTEGER",
        "short_name": "VARCHAR(100)",
        "abbreviation": "VARCHAR(20)",
        "crest_url": "VARCHAR(500)",
        "stadium": "VARCHAR(150)",
    },
    "matches": {
        "provider_id": "INTEGER",
        "league_id": "INTEGER",
        "matchday": "INTEGER",
        "stage": "VARCHAR(100)",
        "group_name": "VARCHAR(100)",
        "half_time_home_goals": "INTEGER",
        "half_time_away_goals": "INTEGER",
        "venue": "VARCHAR(200)",
        "referee": "VARCHAR(150)",
    },
}


def upgrade_legacy_schema(engine: Engine) -> None:
    """Add nullable ingestion columns to databases created by the demo version."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table, columns in ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table)}
            for name, column_type in columns.items():
                if name not in existing_columns:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {column_type}'))
