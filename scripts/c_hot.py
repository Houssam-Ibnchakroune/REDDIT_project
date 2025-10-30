# scripts/collect_comments_hot.py
from src.reddit_ai.utils.logging_setup import setup_logging
setup_logging()

import praw
from datetime import datetime, timezone, timedelta
from src.reddit_ai.config import REDDIT
from src.reddit_ai.db.mongo import get_db, ensure_indexes
from src.reddit_ai.collectors.comments import fetch_comments_details
from src.reddit_ai.db.repositories.comments_repo import upsert_comments

FAST    = ["DeepSeek", "ChatGPT","claude","Copilot"] 
CORE    = ["artificial", "MachineLearning", "deeplearning"]
CREATOR = ["LocalLLaMA", "StableDiffusion", "generativeAI"]

PER_SUB = {
    "FAST": 30,
    "CORE": 25,
    "CREATOR": 25,
}



def iter_post_ids(db, subreddit: str, per_sub: int):
    cur = (db.posts.find(
                {
                    "subreddit": subreddit,
                    "seen_in": "hot"
                },
                {"post_id": 1, "score_max": 1, "num_comments_max": 1}
           )
           .sort([("score_max", -1), ("num_comments_max", -1)])
           .limit(per_sub))
    for doc in cur:
        yield doc["post_id"]

def collect_for_group(db, reddit, subs: list[str], per_sub: int):
    for sub in subs:
        for pid in iter_post_ids(db, sub, per_sub):
            gen = fetch_comments_details(
                reddit, pid,
                sort="hot", cap=300, limit=120,
                top_level_only=True,
                skip_bots=True, english_only=True, debug_samples=2
            )
            upsert_comments(db, gen, batch_size=500)

def run():
    reddit = praw.Reddit(**REDDIT)
    db = get_db()
    ensure_indexes(db)

    collect_for_group(db, reddit, FAST,    PER_SUB["FAST"])
    collect_for_group(db, reddit, CORE,    PER_SUB["CORE"])
    collect_for_group(db, reddit, CREATOR, PER_SUB["CREATOR"])

if __name__ == "__main__":
    run()
