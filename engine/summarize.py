#!/usr/bin/env python3
"""Print aggregate stats from the incident log.

Usage: python3 summarize.py [path/to/incidents.jsonl]
"""

import json
import sys
from pathlib import Path

from config import DEFAULT_LOG_PATH
from incident_log import summarize_log


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG_PATH)
    print(json.dumps(summarize_log(path), indent=2))


if __name__ == "__main__":
    main()
