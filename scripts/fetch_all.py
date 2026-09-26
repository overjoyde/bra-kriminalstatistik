#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.fetch_all (samma som kommandot `brastat-fetch-all`). Kör med --help."""
from brastat.cli.fetch_all import main

if __name__ == "__main__":
    main()
