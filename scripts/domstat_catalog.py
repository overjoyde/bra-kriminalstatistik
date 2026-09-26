#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.domstat_catalog (samma som kommandot `brastat-domstat-catalog`). Kör med --help."""
from brastat.cli.domstat_catalog import main

if __name__ == "__main__":
    main()
