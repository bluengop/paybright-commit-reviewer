#!/usr/bin/env python3

"""Paybright Commit Review v2.0.0"""

import sys
import logging


def main() -> None:
    """Main"""
    logging.basicConfig(stream=sys.stdout,
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Hello, Paybright!")
    sys.exit(0)


if __name__ == "__main__":
    main()
