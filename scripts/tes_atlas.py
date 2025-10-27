# scripts/test_atlas.py
import os, sys
from dotenv import load_dotenv
from src.reddit_ai.db.mongo import get_db, get_client

load_dotenv()



def main():
    client = get_client()

    # Déclenche la connexion et récupère des infos de topologie
    hello = client.admin.command("hello")  # (équiv. moderne de isMaster)
    nodes = getattr(client, "nodes", set())
    hosts = sorted(h for (h, _port) in nodes) if nodes else []

    # Heuristiques “Atlas”
    uri = os.getenv("MONGO_URI", "")
    set_name = str(hello.get("setName", ""))
    is_atlas = (
        ("mongodb.net" in uri) or
        any(h.endswith(".mongodb.net") for h in hosts) or
        set_name.startswith("atlas-")
    )

    print("✅ Connexion OK (ping):", client.admin.command("ping"))
    print("Replica set name   :", set_name or "(n/a)")
    print("Serveurs           :", ", ".join(hosts) if hosts else "(n/a)")

    if is_atlas:
        print("🎯 Détection: **Atlas** (hôtes .mongodb.net ou setName atlas-*)")
        sys.exit(0)
    else:
        print("ℹ️  Détection: probablement **local/self-hosted**.")
        sys.exit(1)

if __name__ == "__main__":
    main()
