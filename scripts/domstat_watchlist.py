#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.domstat_watchlist (samma som kommandot `brastat-domstat-watchlist`). Kör med --help."""
from brastat.cli.domstat_watchlist import main

if __name__ == "__main__":
    main()
