#!/usr/bin/env python
"""
Setup script for first-time initialization.
Run this after installing dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 50)
    print("Ticket Triage System - Setup")
    print("=" * 50)

    # Step 1: Initialize database
    print("\n[1/3] Initializing database...")
    from db.database import init_db
    init_db()
    print("Database initialized successfully")

    # Step 2: Index knowledge base
    print("\n[2/3] Indexing knowledge base...")
    from knowledge_base.indexer import KnowledgeBaseIndexer
    indexer = KnowledgeBaseIndexer()
    count = indexer.index_all_runbooks()
    print(f"Indexed {count} chunks from runbooks")

    # Step 3: Verify configuration
    print("\n[3/3] Verifying configuration...")
    from config.settings import get_settings
    settings = get_settings()

    checks = {
        "Groq API Key": bool(settings.groq_api_key),
        "Dashboard Password Set": settings.dashboard_password != "changeme",
        "Webex Configured": bool(settings.webex_access_token),
    }

    for check, passed in checks.items():
        status = "OK" if passed else "WARNING - Not configured"
        print(f"  {check}: {status}")

    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Update .env with your Webex tokens (optional)")
    print("2. Change DASHBOARD_PASSWORD in .env")
    print("3. Run the server: python -m cli.main serve")
    print("4. Visit http://localhost:8000/dashboard")
    print("\nOr use the CLI:")
    print("  python -m cli.main query 'high CPU usage'")
    print("  python -m cli.main suggest 'Server disk full alert'")


if __name__ == "__main__":
    main()
