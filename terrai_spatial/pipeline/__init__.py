"""Shared infrastructure for the data acquisition and build scripts.

Each module owns one concern the scripts used to copy:

- ``http`` — downloads: one User-Agent, one timeout policy, retry with backoff.
- ``io`` — atomic writes, JSON/GeoJSON validity, hashing, safe zip extraction.
- ``provenance`` — the ``retrieved_at`` timestamp format and its parser.
- ``regions`` — every study-area bounding box, defined once.

The library knows nothing about individual sources. If a helper needs to know
it is fetching MLIT or PLATEAU, it belongs in the script, not here.
"""
