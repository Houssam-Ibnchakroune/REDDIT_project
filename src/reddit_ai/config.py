import os
from dotenv import load_dotenv

load_dotenv()
MONGO_DB  = os.getenv("MONGO_DB")
HOST = os.getenv("MONGO_HOST")
USER = os.getenv("MONGO_USER")
PW   = os.getenv("MONGO_PASS")
REDDIT = {
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "user_agent": os.getenv("REDDIT_USER_AGENT", "RedditAITrend by u/unknown"),
}