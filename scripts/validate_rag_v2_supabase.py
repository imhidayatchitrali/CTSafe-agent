from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_rag_supabase import main


if __name__ == "__main__":
    os.environ["DVR_RAG_VERSION"] = "v2"
    os.environ.setdefault("DVR_RAG_V2_LEGACY_FALLBACK", "false")
    sys.exit(main())
