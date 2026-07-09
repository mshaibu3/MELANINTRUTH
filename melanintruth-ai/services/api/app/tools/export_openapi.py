from __future__ import annotations

import json
import sys
from pathlib import Path

from app.api.router import create_fastapi_app


def main() -> None:
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/api/openapi.json")
    app = create_fastapi_app()
    spec = app.openapi() if hasattr(app, "openapi") else app.openapi_contract()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
