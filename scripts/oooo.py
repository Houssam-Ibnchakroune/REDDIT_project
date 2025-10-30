
import praw

REDDIT_CLIENT_ID="e5sSkPUbHvjcXdCGzhNEFQ"
REDDIT_CLIENT_SECRET="GhkIlPy2335FN5myk41-eD6kls6xpg"
REDDIT_USER_AGENT="Social_Network_Analysis by u/Conscious_Place_9905"
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)
reddit.read_only = True

POST_ID = "1oixoow"  # replace with a real, visible post id
submission = reddit.submission(id=POST_ID)
submission.comment_sort = "top"
submission.comments.replace_more(limit=0)
for i, c in enumerate(submission.comments[:10], 1):
    print(i, c.id, c.score, (c.body[:80] if c.body else ""))
