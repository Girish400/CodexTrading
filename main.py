import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def main() -> int:
    from gstrading.cli import parse_args
    from gstrading.service import run_from_args

    return run_from_args(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
