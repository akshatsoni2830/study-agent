from __future__ import annotations

import sys

import uvicorn


def main() -> int:
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
