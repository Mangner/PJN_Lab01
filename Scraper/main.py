"""Punkt wejścia Bajtoparsera: wyłącznie deleguje do bajtoparser.cli.main()."""

import sys

from bajtoparser.cli import main

if __name__ == "__main__":
    sys.exit(main())
