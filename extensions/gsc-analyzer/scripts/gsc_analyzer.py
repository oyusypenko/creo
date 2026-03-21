#!/usr/bin/env python3
"""
Google Search Console Analyzer - Legacy Entry Point

This script is maintained for backward compatibility.
For new usage, please use: python -m gsc_toolkit <command>

All functionality has been moved to the gsc_toolkit package.
See CLAUDE.md for usage instructions.
"""

if __name__ == '__main__':
    from gsc_toolkit.__main__ import main
    main()
