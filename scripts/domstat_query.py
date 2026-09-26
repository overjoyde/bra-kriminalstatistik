#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.domstat_query (samma som kommandot `brastat-domstat-query`). Kör med --help."""
from brastat.cli.domstat_query import main

if __name__ == "__main__":
    main()
