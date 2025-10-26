import sys
import os

package_dir = os.path.join(os.path.dirname(__file__), 'verse_inserter')
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from verse_inserter.__main__ import main

if __name__ == "__main__":
    sys.exit(main())