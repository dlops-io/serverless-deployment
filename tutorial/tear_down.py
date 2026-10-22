#!/usr/bin/env python3
"""Remove a stack owned by a spin_up manifest (dry-run unless --apply)."""
from lifecycle.lifecycle import main

if __name__ == '__main__':
    raise SystemExit(main('down'))
