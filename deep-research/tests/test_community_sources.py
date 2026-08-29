#!/usr/bin/env python3
"""Offline tests for optional read-only source adapters."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/community_sources.py"
SPEC = importlib.util.spec_from_file_location("community_sources", MODULE_PATH)
assert SPEC and SPEC.loader
community_sources = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(community_sources)


class CommunitySourcesTest(unittest.TestCase):
    def test_reddit_posts_are_normalized_and_risk_flags_are_preserved(self) -> None:
        payload = {
            "posts": [
                {
                    "id": "abc123",
                    "title": "Weekly giveaway",
                    "author": "AutoModerator",
                    "subreddit": "hearthstone",
                    "url": "https://reddit.com/r/hearthstone/comments/abc123/test/",
                    "text": "",
                    "upvotes": 42,
                    "comments": 12,
                    "upvote_ratio": 0.9,
                    "created_utc": 1_700_000_000,
                    "is_crosspost": True,
                    "stickied": True,
                }
            ],
            "after": None,
            "listing_status": "unknown",
        }
        result = community_sources.normalize_reddit_posts(
            payload,
            "posts",
            {"subreddit": "hearthstone", "sort": "top", "timeframe": "week"},
        )
        item = result["results"][0]
        self.assertEqual(item["metrics"]["comments"], 12)
        self.assertEqual(item["provider_rank_kind"], "top")
        self.assertEqual(
            set(item["classification_flags"]),
            {"automated", "giveaway", "crosspost", "stickied"},
        )
        self.assertTrue(any("partial" in warning for warning in result["warnings"]))

    def test_reddit_comment_tree_is_flattened_without_claiming_completeness(self) -> None:
        payload = {
            "comments": [
                {
                    "kind": "t1",
                    "data": {
                        "id": "one",
                        "author": "reader",
                        "body": "First",
                        "score": 10,
                        "created_utc": 1_700_000_000,
                        "parent_id": "t3_post1",
                        "replies": {
                            "data": {
                                "children": [
                                    {
                                        "kind": "t1",
                                        "data": {
                                            "id": "two",
                                            "author": "reader2",
                                            "body": "Reply",
                                            "score": 3,
                                            "parent_id": "t1_one",
                                            "replies": "",
                                        },
                                    }
                                ]
                            }
                        },
                    },
                },
                {"kind": "more", "data": {"count": 7, "children": ["x"]}},
            ],
            "listing_status": "truncated",
        }
        result = community_sources.normalize_reddit_comments(payload, "post1")
        self.assertEqual([item["thread"]["depth"] for item in result["results"]], [0, 1])
        self.assertEqual(result["pagination"]["hidden_comment_count"], 7)
        self.assertTrue(any("complete" in warning for warning in result["warnings"]))

    def test_x_search_preserves_metrics_and_provider_rank_semantics(self) -> None:
        payload = {
            "tweets": [
                {
                    "id": "123",
                    "url": "https://x.com/example/status/123",
                    "text": "Patch discussion",
                    "createdAt": "Sun Jan 25 13:05:46 +0000 2026",
                    "likeCount": 8,
                    "replyCount": 2,
                    "retweetCount": 1,
                    "quoteCount": 0,
                    "viewCount": 100,
                    "author": {"id": "u1", "userName": "example", "followers": 50},
                }
            ],
            "has_more": True,
            "next_cursor": "next",
        }
        result = community_sources.normalize_x_search(payload, "hearthstone", "Top")
        item = result["results"][0]
        self.assertEqual(item["provider_rank_kind"], "top")
        self.assertEqual(item["metrics"]["views"], 100)
        self.assertEqual(result["pagination"]["next_cursor"], "next")
        self.assertTrue(any("not a guaranteed" in warning for warning in result["warnings"]))

    def test_tinyfish_search_is_discovery_only(self) -> None:
        payload = {
            "query": "test",
            "page": 0,
            "total_results": 1,
            "results": [
                {
                    "position": 1,
                    "url": "https://example.com/source",
                    "title": "Source",
                    "snippet": "Candidate evidence",
                    "site_name": "example.com",
                }
            ],
        }
        result = community_sources.normalize_tinyfish_search(payload, "test", 0)
        self.assertEqual(result["results"][0]["evidence_status"], "discovery_only")
        self.assertTrue(any("30" in warning for warning in result["warnings"]))

    def test_tinyfish_fetch_flattens_json_document_tree(self) -> None:
        payload = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Example",
                    "text": {
                        "type": "document",
                        "children": [
                            {"type": "paragraph", "text": "First"},
                            {"type": "paragraph", "text": "Second"},
                        ],
                    },
                }
            ],
            "errors": [],
        }
        result = community_sources.normalize_tinyfish_fetch(payload, ["https://example.com"])
        self.assertEqual(result["results"][0]["content"], "First\nSecond")

    def test_local_tinyfish_rate_limiter_is_fail_fast(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            cache_dir = Path(temp)
            community_sources.reserve_rate_capacity(
                "search", 30, 30, cache_dir=cache_dir, now=1000.0
            )
            with self.assertRaises(community_sources.ProviderError) as raised:
                community_sources.reserve_rate_capacity(
                    "search", 1, 30, cache_dir=cache_dir, now=1000.0
                )
            self.assertEqual(raised.exception.status, 429)
            self.assertIsNotNone(raised.exception.retry_after)

    def test_doctor_reports_presence_without_emitting_secret_values(self) -> None:
        with patch.dict(
            os.environ,
            {
                community_sources.REDDIT_KEY_ENV: "test-reddit-secret",
                community_sources.GETX_KEY_ENV: "test-x-secret",
            },
            clear=False,
        ):
            result = community_sources.doctor()
        rendered = json.dumps(result)
        self.assertTrue(result["redditapi"]["configured"])
        self.assertTrue(result["getxapi"]["configured"])
        self.assertNotIn("test-reddit-secret", rendered)
        self.assertNotIn("test-x-secret", rendered)


if __name__ == "__main__":
    unittest.main()
