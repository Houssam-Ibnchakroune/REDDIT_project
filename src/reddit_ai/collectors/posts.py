import time
import logging
from datetime import timedelta
from ..utils.common import ts_now, is_englishish

logger = logging.getLogger(__name__)

def fetch_posts_details(
    reddit,
    subreddit: list[str] ,
    listing: str = "new",
    limit: int = 100,
    window_days: int = 14,
    time_filter: str = "day",
    include_nsfw: bool = False,
    skip_bots: bool = True,
    english_only: bool = True,
    debug_samples: int = 3,
):
    """
    Fetch posts for a given Reddit subreddit.

    Args:
        reddit: Authenticated PRAW Reddit instance.
        subreddit (list[str]): Name of the subreddit(s) to fetch posts from.
        listing (str): Type of listing to fetch (new, hot, top).
        limit (int): Maximum number of posts to fetch.
        window_days (int): Time window in days to consider for posts.
        time_filter (str): Time filter for top listings (day, week, month).
        include_nsfw (bool): Whether to include NSFW posts.
        skip_bots (bool): Whether to skip posts made by bots.
        english_only (bool): Whether to include only English-like posts.
        debug_samples (int): Number of sample posts to log for debugging.
    """   
    # 1) validate listing
    valid_listings = {"new", "hot", "top"}
    if listing not in valid_listings:
        logger.error("Failed to access subreddits r/%s | Invalid listing '%s'. Expected one of %s.", subreddit, listing, sorted(valid_listings))
        raise ValueError(f"Invalid listing '{listing}'. Expected one of {sorted(valid_listings)}.")
    for subs in subreddit:
        sr = reddit.subreddit(subs)
        if listing == "new":
            gen = sr.new(limit=limit)
        elif listing == "hot":
            gen = sr.hot(limit=limit)
        else:
            gen = sr.top(time_filter=time_filter, limit=limit)

        cutoff_ts = (ts_now() - timedelta(days=window_days)).timestamp()
        logger.info(
            "Fetching %d posts from r/%s | listing=%s%s | window=%dd",
            limit,
            subs,
            listing,
            f"({time_filter})" if listing == "top" else "",
            window_days,
        )

        stats = dict(
            seen=0, yielded=0,
            skipped_old=0, skipped_removed=0, skipped_bots=0,
            skipped_nsfw=0, skipped_lang=0
        )
        sample_left = debug_samples

        for sub in gen:
            stats["seen"] += 1
            try:
                # 3) filters
                if sub.created_utc  < cutoff_ts:
                    stats["skipped_old"] += 1
                    continue
                if getattr(sub, "removed_by_category", None) is not None or sub.author is None:
                    stats["skipped_removed"] += 1
                    continue
                author_str = str(sub.author) if sub.author else None
                if skip_bots and author_str and "bot" in author_str.lower():
                    stats["skipped_bots"] += 1
                    continue
                if not include_nsfw and getattr(sub, "over_18", False):
                    stats["skipped_nsfw"] += 1
                    continue
                text_for_lang = (sub.title or "") + " " + (sub.selftext or "")
                if english_only and not is_englishish(text_for_lang):
                    stats["skipped_lang"] += 1
                    continue

                # 4) normalize one document
                doc = {
                    "_id": sub.id,                             # for idempotent upserts
                    "post_id": sub.id,                         # optional alias
                    "subreddit": str(sub.subreddit),
                    "title": sub.title or "",
                    "selftext": sub.selftext or "",
                    "author": author_str,
                    "score": int(sub.score or 0),
                    "upvote_ratio": float(sub.upvote_ratio or 0.0),
                    "num_comments": int(sub.num_comments or 0),
                    "permalink": f"https://reddit.com{sub.permalink}" if sub.permalink else "",
                    "created_utc": int(sub.created_utc or 0),
                    "ingested_at": ts_now(),
                    "listing": listing,
                    "time_filter": time_filter if listing == "top" else None,
                }

                if sample_left > 0:
                    logger.debug("Sample post: %s", doc["title"])
                    sample_left -= 1
                # 5) stream out (generator)
                yield doc
                stats["yielded"] += 1

                # 6) gentle pacing (optional; PRAW self-throttles anyway)
                if stats["seen"] % 50 == 0:
                    time.sleep(0.2)

            except Exception:
                # full traceback helps you debug rare payload issues
                logger.exception("Failed to normalize submission id=%s", getattr(sub, "id", "?"))

        logger.info(
            "Finished r/%s | seen=%d yielded=%d skipped(old=%d, removed=%d, bots=%d, nsfw=%d, lang=%d)",
            subs,
            stats["seen"], stats["yielded"],
            stats["skipped_old"], stats["skipped_removed"], stats["skipped_bots"],
            stats["skipped_nsfw"], stats["skipped_lang"]
        )