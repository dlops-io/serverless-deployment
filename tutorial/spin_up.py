#!/usr/bin/env python3
"""Create an isolated, journaled tutorial stack (dry-run unless --apply)."""
from lifecycle.lifecycle import main

if __name__ == '__main__':
    raise SystemExit(main('up'))
