#!/usr/bin/env python3
"""Tunt skal för bakåtkompatibilitet – koden finns i brastat.cli.export_data (samma som kommandot `brastat-export`). Kör med --help."""
from brastat.cli.export_data import main

if __name__ == "__main__":
    main()
