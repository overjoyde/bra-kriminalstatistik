#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.sol_query (samma som kommandot `brastat-sol-query`). Kör med --help."""
from brastat.cli.sol_query import main

if __name__ == "__main__":
    main()
