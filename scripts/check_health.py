#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.check_health (samma som kommandot `brastat-health`). Kör med --help."""
from brastat.cli.check_health import main

if __name__ == "__main__":
    main()
