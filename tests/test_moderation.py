import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app", "schemas"))

from moderation_schemas import ModerationResult


def test_allow_result_is_accepted():
    result = ModerationResult(
        decision="ALLOW",
        reason="Receipt detected."
    )

    assert result.decision == "ALLOW"
    assert result.reason == "Receipt detected."


def test_block_result_is_accepted():
    result = ModerationResult(
        decision="BLOCK",
        reason="Unsafe content detected."
    )

    assert result.decision == "BLOCK"
    assert result.reason == "Unsafe content detected."


def test_human_review_result_is_accepted():
    result = ModerationResult(
        decision="HUMAN_REVIEW",
        reason="Image is blurry."
    )

    assert result.decision == "HUMAN_REVIEW"


def test_invalid_decision_is_rejected():
    with pytest.raises(Exception):
        ModerationResult(
            decision="APPROVE",
            reason="Invalid decision"
        )


def test_moderation_round_trips_through_json():
    original = ModerationResult(
        decision="ALLOW",
        reason="Receipt detected."
    )

    json_string = original.model_dump_json()
    reconstructed = ModerationResult.model_validate_json(json_string)

    assert reconstructed == original