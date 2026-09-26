#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.sol_watchlist (samma som kommandot `brastat-sol-watchlist`). Kör med --help."""
from brastat.cli.sol_watchlist import main

if __name__ == "__main__":
    main()
