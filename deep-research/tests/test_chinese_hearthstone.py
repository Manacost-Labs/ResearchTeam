#!/usr/bin/env python3
"""Offline regression tests for Chinese Hearthstone ingestion."""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/chinese"
MODULE_PATH = ROOT / "scripts/chinese_hearthstone.py"
SPEC = importlib.util.spec_from_file_location("chinese_hearthstone", MODULE_PATH)
assert SPEC and SPEC.loader
chinese_hearthstone = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = chinese_hearthstone
SPEC.loader.exec_module(chinese_hearthstone)


def varint(value: int) -> bytes:
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        result.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(result)


def encode_deck(cards: dict[int, int], hero: int = 7) -> str:
    data = bytearray(b"\0") + varint(1) + varint(2)
    data += varint(1) + varint(hero)
    singles = sorted(key for key, count in cards.items() if count == 1)
    doubles = sorted(key for key, count in cards.items() if count == 2)
    others = sorted((key, count) for key, count in cards.items() if count not in {1, 2})
    data += varint(len(singles))
    for key in singles:
        data += varint(key)
    data += varint(len(doubles))
    for key in doubles:
        data += varint(key)
    data += varint(len(others))
    for key, count in others:
        data += varint(key) + varint(count)
    data += b"\0"
    return base64.b64encode(data).decode("ascii")


class ChineseHearthstoneTest(unittest.TestCase):
    def test_valid_invalid_and_multiple_deckstrings(self) -> None:
        valid = encode_deck({key: 2 for key in range(1000, 1015)})
        text = f"第一套 {valid} 重复 {valid} 无效 AAE-not-a-real-deck-code-123456789"
        decks = chinese_hearthstone.extract_deckstrings(text)
        self.assertEqual(len(decks), 2)
        self.assertTrue(decks[0].valid)
        self.assertEqual(decks[0].cards_total, 30)
        self.assertFalse(decks[1].valid)

    def test_iyingdi_fixture_extracts_cn_statistics_and_meta_classification(
        self,
    ) -> None:
        raw = (FIXTURES / "iyingdi_cn_meta.html").read_text(encoding="utf-8")
        result = chinese_hearthstone.inspect_document(
            raw,
            source_url="https://www.iyingdi.com/tz/post/123?utm_source=test",
            profile=chinese_hearthstone.SOURCE_PROFILES["iyingdi"],
        )
        self.assertTrue(result["validation"]["valid"])
        self.assertEqual(result["statistics"]["region"], "CN")
        self.assertEqual(result["statistics"]["games"], 1280)
        self.assertEqual(result["statistics"]["win_rate"], 55.0)
        self.assertEqual(result["classification"]["label"], "CN_META")
        self.assertEqual(len(result["decks"]), 1)
        self.assertTrue(result["decks"][0]["valid"])
        self.assertNotIn("utm_source", result["source_url"])

    def test_gamersky_repost_preserves_lineage_and_is_not_independent(self) -> None:
        raw = (FIXTURES / "gamersky_repost.html").read_text(encoding="utf-8")
        result = chinese_hearthstone.inspect_document(
            raw,
            source_url="https://ol.gamersky.com/gl/123",
            profile=chinese_hearthstone.SOURCE_PROFILES["gamersky"],
        )
        self.assertEqual(result["classification"]["label"], "WESTERN_REPOST")
        self.assertIn("hsreplay.net", result["deduplication"]["lineage_hint"])

    def test_17173_fixture_keeps_all_twenty_deck_relationships(self) -> None:
        raw = (FIXTURES / "17173_multi_deck.html").read_text(encoding="utf-8")
        result = chinese_hearthstone.inspect_document(
            raw,
            source_url="https://hs.17173.com/news/123",
            profile=chinese_hearthstone.SOURCE_PROFILES["17173"],
        )
        self.assertEqual(len(result["decks"]), 20)
        self.assertTrue(all(deck["valid"] for deck in result["decks"]))
        self.assertEqual(len({deck["fingerprint"] for deck in result["decks"]}), 20)

    def test_deck_similarity_boundaries(self) -> None:
        base = {key: 1 for key in range(1, 31)}
        exact = chinese_hearthstone.compare_decks(base, base)
        near = chinese_hearthstone.compare_decks(
            base, {**{key: 1 for key in range(1, 30)}, 31: 1}
        )
        variant = chinese_hearthstone.compare_decks(
            base, {**{key: 1 for key in range(1, 29)}, 31: 1, 32: 1}
        )
        archetype = chinese_hearthstone.compare_decks(
            base, {**{key: 1 for key in range(1, 27)}, 31: 1, 32: 1, 33: 1, 34: 1}
        )
        self.assertEqual(exact.relation, "EXACT")
        self.assertEqual(near.relation, "NEAR_DUPLICATE")
        self.assertEqual(variant.relation, "VARIANT")
        self.assertEqual(archetype.relation, "ARCHETYPE_VARIANT")
        self.assertEqual(sum(variant.removed.values()), 2)
        self.assertEqual(sum(variant.added.values()), 2)

    def test_cn_original_requires_checked_absence_of_western_match(self) -> None:
        stats = chinese_hearthstone.extract_cn_stats("国服传说排名 88")
        provenance = chinese_hearthstone.extract_provenance("本人构筑，国服传说排名 88")
        unchecked = chinese_hearthstone.classify_cn_deck(
            "本人构筑，国服传说排名 88", stats, provenance
        )
        checked = chinese_hearthstone.classify_cn_deck(
            "本人构筑，国服传说排名 88",
            stats,
            provenance,
            western_match_checked=True,
        )
        self.assertEqual(unchecked.label.value, "CN_META")
        self.assertEqual(checked.label.value, "CN_ORIGINAL")

    def test_cn_variant_records_added_and_removed_cards(self) -> None:
        western = {key: 1 for key in range(1, 31)}
        chinese = {**{key: 1 for key in range(1, 29)}, 31: 1, 32: 1}
        comparison = chinese_hearthstone.compare_decks(western, chinese)
        result = chinese_hearthstone.classify_cn_deck(
            "国服传说构筑",
            chinese_hearthstone.CNStats(region="CN"),
            chinese_hearthstone.Provenance(),
            comparison=comparison,
        )
        self.assertEqual(result.label.value, "CN_VARIANT")
        self.assertEqual(result.comparison["relation"], "VARIANT")

    def test_content_validation_rejects_captcha_spa_403_and_429(self) -> None:
        profile = chinese_hearthstone.SOURCE_PROFILES["iyingdi"]
        captcha = chinese_hearthstone.validate_content(
            "<html>CAPTCHA 安全验证</html>", profile
        )
        spa = chinese_hearthstone.validate_content(
            '<html><body><div id="root"></div></body></html>', profile
        )
        forbidden = chinese_hearthstone.validate_content(
            "forbidden", profile, status_code=403
        )
        limited = chinese_hearthstone.validate_content("busy", profile, status_code=429)
        self.assertEqual(captcha.status.value, "BLOCKED")
        self.assertEqual(spa.status.value, "INCOMPLETE")
        self.assertEqual(forbidden.status.value, "BLOCKED")
        self.assertEqual(limited.status.value, "RATE_LIMITED")

    def test_scrape_do_escalates_only_after_content_failure(self) -> None:
        requests: list[dict[str, list[str]]] = []
        good = (FIXTURES / "iyingdi_cn_meta.html").read_bytes()

        def transport(request, timeout):
            query = parse_qs(urlsplit(request.full_url).query)
            requests.append(query)
            if len(requests) == 1:
                return 200, {"Content-Type": "text/html"}, b'<div id="root"></div>'
            return (
                200,
                {
                    "Content-Type": "text/html; charset=utf-8",
                    "Scrape.do-Resolved-Url": "https://iyingdi.com/post/1",
                    "Scrape.do-Request-Cost": "5",
                },
                good,
            )

        client = chinese_hearthstone.ScrapeDoClient(
            "fixture-token", transport=transport, sleep=lambda _: None
        )
        result = client.fetch(
            "https://iyingdi.com/post/1", chinese_hearthstone.SOURCE_PROFILES["iyingdi"]
        )
        public = json.dumps(result.public_dict(), ensure_ascii=False)
        self.assertEqual(result.status.value, "SUCCESS")
        self.assertEqual(
            [attempt.level for attempt in result.attempts], ["normal", "render"]
        )
        self.assertNotIn("render", requests[0])
        self.assertEqual(requests[1]["render"], ["true"])
        self.assertNotIn("fixture-token", public)

    def test_scrape_do_marks_browser_fallback_after_all_levels(self) -> None:
        def transport(request, timeout):
            return 200, {"Content-Type": "text/html"}, b'<div id="root"></div>'

        result = chinese_hearthstone.ScrapeDoClient(
            "fixture-token", transport=transport, sleep=lambda _: None
        ).fetch(
            "https://taptap.cn/topic/1", chinese_hearthstone.SOURCE_PROFILES["taptap"]
        )
        self.assertTrue(result.browser_fallback_required)
        self.assertEqual(len(result.attempts), 4)
        self.assertEqual(result.status.value, "INCOMPLETE")

    def test_koloda_adapter_normalizes_card_and_uses_bearer_header(self) -> None:
        captured = {}

        def transport(request, timeout):
            captured.update(dict(request.header_items()))
            payload = {
                "data": {
                    "dbf": 315,
                    "card_id": "CS2_029",
                    "name": {"ru": "Огненный шар", "en": "Fireball"},
                    "class": "MAGE",
                    "card_type": {"slug": "SPELL"},
                    "card_set": "LEGACY",
                    "collectible": True,
                    "formats": [{"slug": "wild"}],
                    "updated_at": "2026-08-30 21:07:27",
                }
            }
            return (
                200,
                {"Content-Type": "application/json"},
                json.dumps(payload).encode(),
            )

        database = chinese_hearthstone.KolodaCardDatabase(
            "fixture-khs-token", transport=transport, sleep=lambda _: None
        )
        card = database.get_card(315)
        self.assertEqual(card["name"]["ru"], "Огненный шар")
        self.assertEqual(captured["Authorization"], "Bearer fixture-khs-token")
        self.assertNotIn("fixture-khs-token", json.dumps(card, ensure_ascii=False))

    def test_koloda_adapter_handles_missing_card(self) -> None:
        database = chinese_hearthstone.KolodaCardDatabase(
            transport=lambda request, timeout: (404, {}, b"{}"), sleep=lambda _: None
        )
        self.assertIsNone(database.get_card(99999999))

    def test_scrape_do_does_not_escalate_a_dead_url(self) -> None:
        result = chinese_hearthstone.ScrapeDoClient(
            "fixture-token",
            transport=lambda request, timeout: (
                404,
                {
                    "Scrape.do-Initial-Status-Code": "404",
                    "Scrape.do-Request-Cost": "1",
                },
                b"not found",
            ),
            sleep=lambda _: None,
        ).fetch("https://nga.cn/not-found", chinese_hearthstone.SOURCE_PROFILES["nga"])
        self.assertEqual(result.status.value, "UNSUPPORTED")
        self.assertEqual(len(result.attempts), 1)
        self.assertFalse(result.browser_fallback_required)

    def test_bilibili_payload_preserves_timestamped_guide_evidence(self) -> None:
        payload = json.loads(
            (FIXTURES / "bilibili_video.json").read_text(encoding="utf-8")
        )
        result = chinese_hearthstone.parse_bilibili_payload(
            payload, "https://www.bilibili.com/video/BV1ResearchTeam"
        )
        self.assertEqual(len(result["transcript_segments"]), 3)
        self.assertEqual(len(result["guide_evidence"]), 2)
        self.assertEqual(result["guide_evidence"][0]["timestamp_start"], 12.5)
        self.assertEqual(result["guide_evidence"][1]["category"], "matchup")
        self.assertEqual(len(result["deckstrings"]), 1)

    def test_guide_hunter_builds_localized_queries_for_each_source(self) -> None:
        queries = chinese_hearthstone.build_guide_queries(None, "控制战")
        self.assertEqual(len(queries), 24)
        self.assertTrue(
            any("site:nga.cn" in query and "留牌" in query for query in queries)
        )
        self.assertTrue(
            any("site:bilibili.com" in query and "构筑" in query for query in queries)
        )

    def test_evidence_clustering_counts_lineages_not_reposts(self) -> None:
        first = chinese_hearthstone.make_guide_evidence(
            source_id="one",
            source_url="https://example.cn/1",
            source_type="article",
            text_zh="起手留牌优先保留低费随从",
            lineage_id="original:one",
        )
        repost = chinese_hearthstone.make_guide_evidence(
            source_id="two",
            source_url="https://example.cn/2",
            source_type="article",
            text_zh="起手留牌优先保留低费随从",
            lineage_id="original:one",
        )
        independent = chinese_hearthstone.make_guide_evidence(
            source_id="three",
            source_url="https://example.cn/3",
            source_type="video",
            text_zh="起手留牌优先保留低费随从",
            lineage_id="original:three",
        )
        cluster = chinese_hearthstone.cluster_evidence([first, repost, independent])[0]
        self.assertEqual(cluster["state"], "corroborated")
        self.assertEqual(cluster["independent_lineages"], 2)

    def test_cn_deck_score_uses_configurable_weights(self) -> None:
        score = chinese_hearthstone.cn_deck_score(
            {
                "originality": 1.0,
                "performance": 0.8,
                "evidence": 0.5,
                "freshness": 1.0,
                "guide": 0.5,
            }
        )
        self.assertEqual(score, 80.0)

    def test_dictionary_and_structured_guide_contract_are_available(self) -> None:
        self.assertEqual(chinese_hearthstone.CN_HEARTHSTONE_TERMS["留牌"], "mulligan")
        schema = chinese_hearthstone.empty_guide_schema()
        self.assertIn("always_keep", schema["mulligan"])
        self.assertEqual(schema["matchups"], [])

    def test_doctor_never_emits_credentials(self) -> None:
        with patch.dict(
            os.environ,
            {
                chinese_hearthstone.SCRAPE_DO_TOKEN_ENV: "fixture-scrape-secret",
                chinese_hearthstone.KHS_TOKEN_ENV: "fixture-khs-secret",
            },
            clear=False,
        ):
            result = chinese_hearthstone.doctor()
        rendered = json.dumps(result)
        self.assertTrue(result["scrape_do"]["configured"])
        self.assertTrue(result["koloda_card_database"]["token_configured"])
        self.assertNotIn("fixture-scrape-secret", rendered)
        self.assertNotIn("fixture-khs-secret", rendered)


if __name__ == "__main__":
    unittest.main()
