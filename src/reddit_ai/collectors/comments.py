import logging
import time
from typing import Iterator, Dict, Any
from ..utils.common import ts_now, is_englishish

logger = logging.getLogger(__name__)

def is_top_level_comment(c) -> bool:
    v = getattr(c, "is_root", None)       # works if your PRAW has it
    if v is not None:
        return bool(v)
    if getattr(c, "depth", None) is not None:
        return c.depth == 0
    pid = (getattr(c, "parent_id", "") or "")
    lid = (getattr(c, "link_id", "") or "")
    return pid.startswith("t3_") or (pid == lid)

def fetch_comments_details(
    reddit,
    post_id: str,
    *,
    sort: str = "new",
    cap: int = 500,            # max to scan from API
    limit: int = 100,          # max to yield
    top_level_only: bool = True,
    skip_bots: bool = True,
    english_only: bool = True,
    debug_samples: int = 3,
) -> Iterator[Dict[str, Any]]:
    """
    Yield comment docs for a given Reddit post.

    Args:
        reddit: Authenticated PRAW Reddit instance.
        post_id: ID of the Reddit post to fetch comments from.
        sort: 'new' | 'top' | 'confidence' | 'old'
        cap: Max comments to *scan* from API.
        limit: Max comments to *yield*.
        top_level_only: Only top-level comments if True, else all levels.
        skip_bots: Skip authors whose username contains 'bot'.
        english_only: Keep only English-like comments via is_englishish(comment.body).
        debug_samples: Number of sample bodies to log.
    """
    if sort == "best":
        sort = "confidence"

    valid_sorts = {"top", "new", "old", "qa", "controversial","confidence","hot"}
    if sort not in valid_sorts:
        logger.error("Failed to access comments of post r/%s | Invalid sort '%s'. Expected one of %s.", post_id, sort, valid_sorts)
        raise ValueError(f"Invalid sort '{sort}'. Expected one of {valid_sorts}.")
    

    stats = dict(seen=0, yielded=0, skipped_removed=0, skipped_bots=0, skipped_lang=0)
    sample_left = debug_samples

    # Fetch submission once
    submission = reddit.submission(id=post_id)
    submission.comment_sort = sort
    if not top_level_only:
        submission.comments.replace_more(limit=0)
    logger.info("Fetching comments for post %s | subreddit=%s | sort=%s | cap=%d | limit=%d | top_level_only=%s | skip_bots=%s | english_only=%s | debug_samples=%d",
            post_id, submission.subreddit.display_name, sort, cap, limit, top_level_only, skip_bots, english_only, debug_samples
    )
    # Build the iterable of comments
    if top_level_only:
        pool = submission.comments[:cap]
    else:
        all_comments = submission.comments.list()
        pool = all_comments[:cap] if cap is not None else all_comments

    for comment in pool:
        if stats["yielded"] >= limit:
            break

        stats["seen"] += 1
        
        try:
            # removed / deleted
            if  comment.author is None:
                stats["skipped_removed"] += 1
                continue
            if str(comment.author).lower() in ["[deleted]", "[removed]"] or comment.body in ["[deleted]", "[removed]"]:
                stats["skipped_removed"] += 1
                continue

            # bot filter
            author_str = str(comment.author)
            low = author_str.lower()
            if skip_bots and ("bot" in low or low == "automoderator"):
                stats["skipped_bots"] += 1
                continue

            # language filter
            body = getattr(comment, "body", "") or ""
            if english_only and not is_englishish(body):
                stats["skipped_lang"] += 1
                continue

            doc = {
                "_id": comment.id,
                "comment_id": comment.id,
                "post_id": post_id,
                "subreddit": submission.subreddit.display_name,
                "author": author_str,
                "body": body,
                "score": int(getattr(comment, "score", 0)),
                "is_top_level": is_top_level_comment(comment),
                "permalink": f"https://reddit.com{comment.permalink}",
                "created_utc": int(getattr(comment, "created_utc", 0)),
                "parent_id": getattr(comment, "parent_id", None),
                "ingested_at": ts_now(),  # ingestion timestamp
                "sort": sort,
            }

            if sample_left > 0:
                sample_left -= 1
                logger.debug("Sample comment: %s", body[:200].replace("\n", " "))

            yield doc
            stats["yielded"] += 1
            
            if stats["seen"] % 50 == 0:
                    time.sleep(0.2)
        except Exception as e:
            logger.exception("Error processing comment in post %s : %s", post_id, e)

    logger.info("Finished post %s (r/%s) | seen=%d yielded=%d skipped(removed=%d, bots=%d, lang=%d)",
            post_id, submission.subreddit.display_name,
            stats["seen"], stats["yielded"],
            stats["skipped_removed"], stats["skipped_bots"], stats["skipped_lang"])
