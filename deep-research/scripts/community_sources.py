#!/usr/bin/env python3
"""Read-only adapters for RedditAPI, GetXAPI, and TinyFish.

The adapters normalize discovery data into a small provider-neutral envelope.
Credentials are read from the environment or managed by the TinyFish CLI and
are never included in output.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


SCHEMA_VERSION = "1.0"
REDDIT_BASE_URL = "https://api.redditapis.com"
GETX_BASE_URL = "https://api.getxapi.com"
REDDIT_KEY_ENV = "REDDITAPIS_KEY"
GETX_KEY_ENV = "GETXAPI_KEY"
TINYFISH_SEARCH_LIMIT = 30
TINYFISH_FETCH_URL_LIMIT = 150
RATE_WINDOW_SECONDS = 60


class ProviderError(RuntimeError):
    """A safe provider error that never contains credentials."""

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status: int | None = None,
        retry_after: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status = status
        self.retry_after = retry_after

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "provider": self.provider,
            "message": str(self),
        }
        if self.status is not None:
            result["status"] = self.status
        if self.retry_after:
            result["retry_after"] = self.retry_after
        return result


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def iso_from_epoch(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
    except (TypeError, ValueError, OSError):
        return None


def normalize_datetime(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return iso_from_epoch(value)
    text = str(value)
    if text.endswith("Z") or "T" in text:
        return text
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def envelope(
    provider: str,
    operation: str,
    query_context: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    pagination: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "provider": provider,
        "operation": operation,
        "collected_at": utc_now(),
        "query_context": query_context,
        "results": results,
        "pagination": pagination or {},
        "warnings": warnings or [],
    }


def require_key(name: str, provider: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ProviderError(
            provider,
            f"Credential is not configured. Set {name} in the local environment.",
        )
    return value


def get_json(
    provider: str,
    base_url: str,
    path: str,
    params: dict[str, Any],
    key_env: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    key = require_key(key_env, provider)
    clean_params = {key: value for key, value in params.items() if value not in (None, "")}
    url = f"{base_url}{path}"
    if clean_params:
        url = f"{url}?{urlencode(clean_params)}"
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "deep-research-community-sources/1.0",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ProviderError(
            provider,
            f"Provider returned HTTP {exc.code}.",
            status=exc.code,
            retry_after=exc.headers.get("Retry-After"),
        ) from exc
    except URLError as exc:
        raise ProviderError(provider, "Provider request failed.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError(provider, "Provider returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderError(provider, "Provider returned an unexpected response shape.")
    return payload


def reddit_flags(post: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    author = str(post.get("author") or "").lower()
    searchable = f"{post.get('title', '')} {post.get('text', '')}".lower()
    if author in {"automoderator", "modteam"}:
        flags.append("automated")
    if any(term in searchable for term in ("giveaway", "give-away", "розыгрыш")):
        flags.append("giveaway")
    for field, label in (
        ("is_crosspost", "crosspost"),
        ("stickied", "stickied"),
        ("locked", "locked"),
        ("over_18", "nsfw"),
    ):
        if post.get(field):
            flags.append(label)
    return flags


def normalize_reddit_post(
    post: dict[str, Any], position: int, rank_kind: str
) -> dict[str, Any]:
    published_at = normalize_datetime(post.get("created")) or iso_from_epoch(
        post.get("created_utc")
    )
    source_url = post.get("url")
    if not source_url and post.get("permalink"):
        source_url = f"https://www.reddit.com{post['permalink']}"
    return {
        "platform": "reddit",
        "source_kind": "post",
        "source_id": post.get("id"),
        "source_url": source_url,
        "author": post.get("author"),
        "community": post.get("subreddit"),
        "title": post.get("title"),
        "text": post.get("text") or "",
        "published_at": published_at,
        "metrics": {
            "score": post.get("upvotes"),
            "comments": post.get("comments"),
            "upvote_ratio": post.get("upvote_ratio"),
        },
        "provider_position": position,
        "provider_rank_kind": rank_kind,
        "classification_flags": reddit_flags(post),
    }


def normalize_reddit_posts(
    payload: dict[str, Any], operation: str, query_context: dict[str, Any]
) -> dict[str, Any]:
    posts = payload.get("posts")
    if not isinstance(posts, list):
        posts = []
    rank_kind = str(query_context.get("sort") or "provider_order")
    results = [
        normalize_reddit_post(post, position, rank_kind)
        for position, post in enumerate(posts, start=1)
        if isinstance(post, dict)
    ]
    warnings = [
        "Engagement is contextual metadata, not proof of truth or population prevalence.",
        "Review automated, giveaway, stickied, and crosspost flags before trend synthesis.",
    ]
    status = payload.get("listing_status")
    if status in {"truncated", "unknown"}:
        warnings.append(f"Reddit listing coverage is partial: {status}.")
    return envelope(
        "redditapi",
        operation,
        query_context,
        results,
        pagination={
            "next_cursor": payload.get("after"),
            "listing_status": status,
            "exhausted_reason": payload.get("exhausted_reason"),
        },
        warnings=warnings,
    )


def iter_reddit_nodes(nodes: Any, depth: int = 0):
    if not isinstance(nodes, list):
        return
    for node in nodes:
        if not isinstance(node, dict):
            continue
        kind = node.get("kind")
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        yield kind, data, depth
        replies = data.get("replies")
        if isinstance(replies, dict):
            children = replies.get("data", {}).get("children", [])
            yield from iter_reddit_nodes(children, depth + 1)
        elif isinstance(replies, list):
            yield from iter_reddit_nodes(replies, depth + 1)


def normalize_reddit_comments(
    payload: dict[str, Any], post_id: str
) -> dict[str, Any]:
    comments: list[dict[str, Any]] = []
    hidden_count = 0
    for kind, data, depth in iter_reddit_nodes(payload.get("comments", [])):
        if kind == "more":
            hidden_count += int(data.get("count") or len(data.get("children") or []))
            continue
        if kind != "t1":
            continue
        comment_id = data.get("id")
        comments.append(
            {
                "platform": "reddit",
                "source_kind": "comment",
                "source_id": comment_id,
                "source_url": (
                    f"https://www.reddit.com/comments/{post_id}/comment/{comment_id}/"
                    if comment_id
                    else None
                ),
                "author": data.get("author"),
                "community": data.get("subreddit"),
                "text": data.get("body") or "",
                "published_at": iso_from_epoch(data.get("created_utc")),
                "metrics": {"score": data.get("score", data.get("ups"))},
                "thread": {
                    "post_id": post_id,
                    "parent_id": data.get("parent_id"),
                    "depth": depth,
                },
            }
        )
    warnings = [
        "Comment trees are convenience samples; score and repetition do not establish prevalence."
    ]
    if hidden_count:
        warnings.append(f"The response contains placeholders for at least {hidden_count} comments.")
    if payload.get("listing_status") in {"truncated", "unknown"}:
        warnings.append("The provider does not establish that the comment tree is complete.")
    return envelope(
        "redditapi",
        "comments",
        {"post_id": post_id},
        comments,
        pagination={
            "listing_status": payload.get("listing_status"),
            "hidden_comment_count": hidden_count,
        },
        warnings=warnings,
    )


def normalize_x_tweet(
    tweet: dict[str, Any], position: int, product: str
) -> dict[str, Any]:
    author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
    return {
        "platform": "x",
        "source_kind": "post",
        "source_id": tweet.get("id"),
        "source_url": tweet.get("url") or tweet.get("twitterUrl"),
        "author": {
            "id": author.get("id"),
            "username": author.get("userName"),
            "name": author.get("name"),
            "verified": bool(author.get("isVerified") or author.get("isBlueVerified")),
            "followers": author.get("followers"),
        },
        "text": tweet.get("text") or "",
        "published_at": normalize_datetime(tweet.get("createdAt")),
        "language": tweet.get("lang"),
        "metrics": {
            "likes": tweet.get("likeCount"),
            "replies": tweet.get("replyCount"),
            "reposts": tweet.get("retweetCount"),
            "quotes": tweet.get("quoteCount"),
            "views": tweet.get("viewCount"),
            "bookmarks": tweet.get("bookmarkCount"),
        },
        "provider_position": position,
        "provider_rank_kind": product.lower(),
        "classification_flags": ["reply"] if tweet.get("isReply") else [],
    }


def normalize_x_search(
    payload: dict[str, Any], query: str, product: str, cursor: str | None = None
) -> dict[str, Any]:
    tweets = payload.get("tweets")
    if not isinstance(tweets, list):
        tweets = []
    results = [
        normalize_x_tweet(tweet, position, product)
        for position, tweet in enumerate(tweets, start=1)
        if isinstance(tweet, dict)
    ]
    warnings = [
        "Top is provider relevance order, not a guaranteed engagement ranking.",
        "Engagement values are observations at collection time and are not proof of truth or prevalence.",
        "GetXAPI is a third-party service, not the official X API.",
    ]
    return envelope(
        "getxapi",
        "advanced_search",
        {"query": query, "product": product, "cursor": cursor},
        results,
        pagination={
            "has_more": payload.get("has_more"),
            "next_cursor": payload.get("next_cursor"),
        },
        warnings=warnings,
    )


def default_cache_dir() -> Path:
    configured = os.environ.get("DEEP_RESEARCH_CACHE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "deep-research"


def reserve_rate_capacity(
    bucket: str,
    units: int,
    limit: int,
    *,
    cache_dir: Path | None = None,
    now: float | None = None,
) -> None:
    """Reserve units in a local sliding-window limiter without waiting."""

    if units < 1 or units > limit:
        raise ProviderError("tinyfish", "Requested unit count exceeds the local rate limit.")
    timestamp = time.time() if now is None else now
    directory = cache_dir or default_cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    state_path = directory / f"{bucket}-rate.json"
    lock_path = directory / f"{bucket}-rate.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            try:
                raw = json.loads(state_path.read_text(encoding="utf-8"))
                events = [float(value) for value in raw if float(value) > timestamp - RATE_WINDOW_SECONDS]
            except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
                events = []
            if len(events) + units > limit:
                retry_after = max(1, int(RATE_WINDOW_SECONDS - (timestamp - min(events)) + 1))
                raise ProviderError(
                    "tinyfish",
                    "Local TinyFish rate limit reached; retry later.",
                    status=429,
                    retry_after=str(retry_after),
                )
            events.extend([timestamp] * units)
            state_path.write_text(json.dumps(events), encoding="utf-8")
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def run_tinyfish(arguments: list[str], operation: str) -> dict[str, Any]:
    executable = shutil.which("tinyfish")
    if not executable:
        raise ProviderError("tinyfish", "TinyFish CLI is not installed or is not on PATH.")
    try:
        result = subprocess.run(
            [executable, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProviderError("tinyfish", f"TinyFish {operation} timed out.") from exc
    if result.returncode != 0:
        raise ProviderError("tinyfish", f"TinyFish {operation} failed.")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProviderError("tinyfish", "TinyFish returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderError("tinyfish", "TinyFish returned an unexpected response shape.")
    return payload


def normalize_tinyfish_search(
    payload: dict[str, Any],
    query: str,
    page: int,
    *,
    location: str | None = None,
    language: str | None = None,
    include_domains: str | None = None,
    exclude_domains: str | None = None,
) -> dict[str, Any]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raw_results = []
    results = []
    for fallback_position, item in enumerate(raw_results, start=1):
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "platform": "web",
                "source_kind": "search_result",
                "source_url": item.get("url"),
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "site_name": item.get("site_name"),
                "published_at": normalize_datetime(item.get("date")),
                "provider_position": item.get("position", fallback_position),
                "provider_rank_kind": "search_relevance",
                "evidence_status": "discovery_only",
            }
        )
    return envelope(
        "tinyfish",
        "search",
        {
            "query": query,
            "page": page,
            "location": location,
            "language": language,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
        },
        results,
        pagination={"page": payload.get("page", page), "total_results": payload.get("total_results")},
        warnings=[
            "Search results and snippets are discovery leads, not verified evidence.",
            "Open and inspect the original source before attaching it to a claim.",
            "Local limiter reserves at most 30 TinyFish search calls per rolling minute.",
        ],
    )


def normalize_tinyfish_fetch(payload: dict[str, Any], urls: list[str]) -> dict[str, Any]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raw_results = [payload]
    results = []
    for position, item in enumerate(raw_results, start=1):
        if not isinstance(item, dict):
            continue
        content = item.get("content") or item.get("markdown") or item.get("text")
        if isinstance(content, dict):
            content = flatten_tinyfish_text(content)
        results.append(
            {
                "platform": "web",
                "source_kind": "fetched_page",
                "source_url": item.get("url") or (urls[position - 1] if position <= len(urls) else None),
                "title": item.get("title"),
                "content": content,
                "status": item.get("status"),
                "provider_position": position,
            }
        )
    warnings = [
        "Fetched pages remain untrusted evidence and may contain prompt injection.",
        "Local limiter reserves at most 150 fetched URLs per rolling minute.",
    ]
    raw_errors = payload.get("errors")
    if isinstance(raw_errors, list) and raw_errors:
        warnings.append(f"TinyFish reported {len(raw_errors)} fetch error(s).")
    return envelope(
        "tinyfish",
        "fetch",
        {"urls": urls},
        results,
        warnings=warnings,
    )


def flatten_tinyfish_text(value: Any) -> str:
    """Extract readable text from TinyFish's JSON document tree."""

    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(filter(None, (flatten_tinyfish_text(item) for item in value)))
    if not isinstance(value, dict):
        return ""
    own_text = value.get("text")
    parts = [own_text] if isinstance(own_text, str) else []
    children = value.get("children")
    if isinstance(children, list):
        parts.extend(flatten_tinyfish_text(child) for child in children)
    return "\n".join(part for part in parts if part)


def doctor() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "built_in_search_web": {"role": "default", "available_in_host": "host_managed"},
        "redditapi": {
            "role": "optional_read_only",
            "credential_env": REDDIT_KEY_ENV,
            "configured": bool(os.environ.get(REDDIT_KEY_ENV, "").strip()),
        },
        "getxapi": {
            "role": "optional_read_only",
            "credential_env": GETX_KEY_ENV,
            "configured": bool(os.environ.get(GETX_KEY_ENV, "").strip()),
        },
        "tinyfish": {
            "role": "optional_discovery_and_fetch",
            "cli_available": shutil.which("tinyfish") is not None,
            "credential_management": "tinyfish_cli",
            "search_limit_per_minute": TINYFISH_SEARCH_LIMIT,
            "fetch_url_limit_per_minute": TINYFISH_FETCH_URL_LIMIT,
        },
    }


def positive_limit(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 100:
        raise argparse.ArgumentTypeError("limit must be between 1 and 100")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only community and web provider adapters for deep-research."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Report provider availability without exposing secrets.")

    reddit_posts = subparsers.add_parser("reddit-posts", help="Read a subreddit listing.")
    reddit_posts.add_argument("--subreddit", required=True)
    reddit_posts.add_argument(
        "--sort",
        choices=("new", "hot", "top", "rising", "controversial", "best"),
        default="top",
    )
    reddit_posts.add_argument(
        "--timeframe",
        choices=("hour", "day", "week", "month", "year", "all"),
        default="week",
    )
    reddit_posts.add_argument("--limit", type=positive_limit, default=25)
    reddit_posts.add_argument("--after")

    reddit_search = subparsers.add_parser("reddit-search", help="Search Reddit posts.")
    reddit_search.add_argument("--query", required=True)
    reddit_search.add_argument("--subreddit")
    reddit_search.add_argument(
        "--sort", choices=("relevance", "new", "hot", "top", "comments"), default="relevance"
    )
    reddit_search.add_argument(
        "--timeframe",
        choices=("hour", "day", "week", "month", "year", "all"),
        default="week",
    )
    reddit_search.add_argument("--limit", type=positive_limit, default=25)
    reddit_search.add_argument("--after")

    reddit_comments = subparsers.add_parser(
        "reddit-comments", help="Read a Reddit post and its comment tree."
    )
    reddit_comments.add_argument("--post-id", required=True)

    x_search = subparsers.add_parser("x-search", help="Search X posts through GetXAPI.")
    x_search.add_argument("--query", required=True)
    x_search.add_argument("--product", choices=("Latest", "Top"), default="Latest")
    x_search.add_argument("--cursor")

    tinyfish_search = subparsers.add_parser(
        "tinyfish-search", help="Search the web through the installed TinyFish CLI."
    )
    tinyfish_search.add_argument("--query", required=True)
    tinyfish_search.add_argument("--location")
    tinyfish_search.add_argument("--language")
    tinyfish_search.add_argument("--include-domains")
    tinyfish_search.add_argument("--exclude-domains")
    tinyfish_search.add_argument("--page", type=int, default=0)

    tinyfish_fetch = subparsers.add_parser(
        "tinyfish-fetch", help="Fetch clean page content through the installed TinyFish CLI."
    )
    tinyfish_fetch.add_argument("--url", action="append", required=True, dest="urls")
    return parser


def execute(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "doctor":
        return doctor()
    if args.command == "reddit-posts":
        context = {
            "subreddit": args.subreddit.removeprefix("r/"),
            "sort": args.sort,
            "timeframe": args.timeframe,
            "limit": args.limit,
            "cursor": args.after,
        }
        payload = get_json(
            "redditapi",
            REDDIT_BASE_URL,
            "/api/reddit/posts",
            {
                "subreddit": context["subreddit"],
                "sort": args.sort,
                "t": args.timeframe,
                "limit": args.limit,
                "after": args.after,
            },
            REDDIT_KEY_ENV,
        )
        return normalize_reddit_posts(payload, "posts", context)
    if args.command == "reddit-search":
        context = {
            "query": args.query,
            "subreddit": args.subreddit.removeprefix("r/") if args.subreddit else None,
            "sort": args.sort,
            "timeframe": args.timeframe,
            "limit": args.limit,
            "cursor": args.after,
        }
        payload = get_json(
            "redditapi",
            REDDIT_BASE_URL,
            "/api/reddit/search",
            {
                "q": args.query,
                "subreddit": context["subreddit"],
                "sort": args.sort,
                "t": args.timeframe,
                "limit": args.limit,
                "after": args.after,
            },
            REDDIT_KEY_ENV,
        )
        return normalize_reddit_posts(payload, "search", context)
    if args.command == "reddit-comments":
        post_id = args.post_id.removeprefix("t3_")
        if not post_id.isalnum() or not 1 <= len(post_id) <= 16:
            raise ProviderError("redditapi", "Post id must contain 1-16 letters or digits.")
        payload = get_json(
            "redditapi",
            REDDIT_BASE_URL,
            f"/api/reddit/post/{post_id}/comments",
            {},
            REDDIT_KEY_ENV,
        )
        return normalize_reddit_comments(payload, post_id)
    if args.command == "x-search":
        payload = get_json(
            "getxapi",
            GETX_BASE_URL,
            "/twitter/tweet/advanced_search",
            {"q": args.query, "product": args.product, "cursor": args.cursor},
            GETX_KEY_ENV,
        )
        return normalize_x_search(payload, args.query, args.product, args.cursor)
    if args.command == "tinyfish-search":
        reserve_rate_capacity("tinyfish-search", 1, TINYFISH_SEARCH_LIMIT)
        command = ["search", "query", args.query]
        for option, value in (
            ("--location", args.location),
            ("--language", args.language),
            ("--include-domains", args.include_domains),
            ("--exclude-domains", args.exclude_domains),
        ):
            if value:
                command.extend([option, value])
        command.extend(["--page", str(args.page)])
        payload = run_tinyfish(command, "search")
        return normalize_tinyfish_search(
            payload,
            args.query,
            args.page,
            location=args.location,
            language=args.language,
            include_domains=args.include_domains,
            exclude_domains=args.exclude_domains,
        )
    if args.command == "tinyfish-fetch":
        reserve_rate_capacity(
            "tinyfish-fetch", len(args.urls), TINYFISH_FETCH_URL_LIMIT
        )
        payload = run_tinyfish(
            ["fetch", "content", "get", *args.urls, "--format", "json"], "fetch"
        )
        return normalize_tinyfish_fetch(payload, args.urls)
    raise ProviderError("adapter", "Unknown command.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = execute(args)
    except ProviderError as exc:
        print(json.dumps({"ok": False, "error": exc.as_dict()}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "data": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
