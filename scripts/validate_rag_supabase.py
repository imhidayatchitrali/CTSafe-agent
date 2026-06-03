from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.rag_factory import create_rag_search_tool
from app.services.rag_validation import evaluate_rag_cases, load_rag_eval_cases
from app.repositories.supabase_rest_client import SupabaseRestClient
from app.settings import AppSettings


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "file.env")
    fixture_path = ROOT / "tests" / "fixtures" / "rag_eval" / "dvr_core.json"
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print("Missing required env vars for Supabase RAG validation:")
        for key in missing:
            print(f"- {key}")
        print("No secrets were printed. Configure these in the backend environment and rerun.")
        return 2

    embedding_provider = os.getenv("DVR_EMBEDDING_PROVIDER", "openai_api").lower()
    has_embedding_credentials = (
        (embedding_provider == "openrouter" and (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_KEY")))
        or (embedding_provider == "openai_api" and os.getenv("OPENAI_API_KEY"))
    )

    if not has_embedding_credentials:
        print("Supabase credentials found. Checking corpus connectivity without printing secrets.")
        client = SupabaseRestClient(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
        for table in ("normativa", "indice", "dvr_pregressi"):
            rows = client.select(table=table, select="id,metadata", limit=1)
            print(f"{table}: ok, rows_returned={len(rows)}")
        print(
            "Semantic vector RAG evaluation skipped: missing credentials for "
            f"DVR_EMBEDDING_PROVIDER={embedding_provider!r}. This is separate "
            "from the LLM generation provider."
        )
        return 2

    settings = AppSettings(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_KEY"),
        embedding_provider=embedding_provider,
        embedding_model=os.getenv(
            "DVR_EMBEDDING_MODEL",
            "openai/text-embedding-3-small"
            if embedding_provider == "openrouter"
            else "text-embedding-3-small",
        ),
        rag_backend="supabase",
        rag_allow_fallback=True,
        rag_version=os.getenv("DVR_RAG_VERSION", "legacy"),
        rag_v2_legacy_fallback=os.getenv("DVR_RAG_V2_LEGACY_FALLBACK", "true").lower()
        in {"1", "true", "yes"},
    )
    tool = create_rag_search_tool(settings)
    print(
        "RAG mode: "
        f"backend={settings.rag_backend}, version={settings.rag_version}, "
        f"v2_legacy_fallback={settings.rag_v2_legacy_fallback}"
    )
    results = evaluate_rag_cases(tool, load_rag_eval_cases(fixture_path))
    failed = [result for result in results if not result.passed]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.name}: {result.result_count} chunks")
        if result.fallback_reason:
            print(f"  fallback: {result.fallback_reason}")
        if result.missing_terms:
            print(f"  missing terms: {', '.join(result.missing_terms)}")
        if result.missing_source_terms:
            print(f"  missing source terms: {', '.join(result.missing_source_terms)}")
        if result.chunk_ids:
            print(f"  chunks: {', '.join(result.chunk_ids[:5])}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
