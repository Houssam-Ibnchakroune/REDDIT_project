# scripts/debug_posts_sample.py
from datetime import datetime, timezone, timedelta
from src.reddit_ai.db.mongo import get_db

db = get_db()

# What subreddits are stored (exact strings)?
print("Distinct subreddits:", db.posts.distinct("subreddit")[:20])

# Show a few recent docs so we see fields as stored
cutoff = int((datetime.now(timezone.utc) - timedelta(days=14)).timestamp())
q = {"created_utc": {"$gte": cutoff}}
for d in db.posts.find(q, {"subreddit":1,"post_id":1,"seen_in":1,"time_filter":1,"title":1}).limit(5):
    print(d)
