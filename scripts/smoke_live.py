#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.smoke_live (samma som kommandot `brastat-smoke`). Kör med --help."""
from brastat.cli.smoke_live import main

if __name__ == "__main__":
    main()
