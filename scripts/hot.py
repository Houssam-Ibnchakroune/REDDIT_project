# scripts/collect_hot.py
from src.reddit_ai.utils.logging_setup import setup_logging
setup_logging()

import praw
from src.reddit_ai.config import REDDIT
from src.reddit_ai.db.mongo import get_db, ensure_indexes
from src.reddit_ai.collectors.posts import fetch_posts_details
from src.reddit_ai.db.repositories.posts_repo import upsert_posts

FAST    = ["DeepSeek", "ChatGPT","claude","Copilot"] 
CORE    = ["artificial", "MachineLearning", "deeplearning"]
CREATOR = ["LocalLLaMA", "StableDiffusion", "generativeAI"]
LIMITS = {
    "FAST": 80,
    "CORE": 60,
    "CREATOR": 60,
}

def run():
    reddit = praw.Reddit(**REDDIT)
    db = get_db()
    ensure_indexes(db)

    def collect_for(subs: list[str], limit: int):
            gen = fetch_posts_details(
                reddit, subs,
                listing="hot",
                limit=limit, window_days=14,
                english_only=True, skip_bots=True, include_nsfw=False
            )
            upsert_posts(db, gen, batch_size=500)

    collect_for(FAST,    LIMITS["FAST"])
    collect_for(CORE,    LIMITS["CORE"])
    collect_for(CREATOR, LIMITS["CREATOR"])


if __name__ == "__main__":
    run()
