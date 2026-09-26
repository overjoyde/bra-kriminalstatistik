#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.fetch_tables (samma som kommandot `brastat-fetch-tables`). Kör med --help."""
from brastat.cli.fetch_tables import main

if __name__ == "__main__":
    main()
