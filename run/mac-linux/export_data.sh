#!/usr/bin/env bash
# Exportera hämtad data till Parquet/DuckDB. Ex: ./export_data.sh --format parquet duckdb
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/export_data.py "$@"
