"""Data models and response schemas for the Script Writer module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ScriptFormat(Enum):
    """Target video format for the generated script."""

    LONG_FORM = "LONG_FORM"  # Standard YouTube / TV ads (15s-60s+)
    SHORTS = "SHORTS"  # YouTube Shorts / TikTok / Reels (≤60s)


class ScriptTone(Enum):
    """Desired tone of the ad script."""

    PROFESSIONAL = "PROFESSIONAL"
    CASUAL = "CASUAL"
    HUMOROUS = "HUMOROUS"
    EMOTIONAL = "EMOTIONAL"
    URGENT = "URGENT"
    INSPIRATIONAL = "INSPIRATIONAL"


@dataclass
class ScriptScene:
    """A single scene within a generated ad script."""

    scene_number: int
    start_time: str  # M:SS format
    end_time: str  # M:SS format
    visual_description: str
    voiceover: str
    on_screen_text: str
    audio_direction: str  # Music / SFX cues
    abcd_features_addressed: list[str] = field(default_factory=list)


@dataclass
class ScriptBrief:
    """Input brief for script generation."""

    brand_name: str
    product_name: str
    product_description: str
    target_audience: str
    key_message: str
    call_to_action: str
    script_format: ScriptFormat = ScriptFormat.LONG_FORM
    tone: ScriptTone = ScriptTone.PROFESSIONAL
    duration_seconds: int = 30
    additional_instructions: str = ""
    brand_guidelines: str = ""


@dataclass
class GeneratedScript:
    """A complete generated ad script."""

    title: str
    concept: str
    scenes: list[ScriptScene] = field(default_factory=list)
    total_duration_seconds: int = 0
    abcd_score_summary: dict = field(default_factory=dict)
    improvement_suggestions: list[str] = field(default_factory=list)


@dataclass
class ScriptValidationResult:
    """Result of validating a script against ABCDs."""

    feature_id: str
    feature_name: str
    sub_category: str  # ATTRACT / BRAND / CONNECT / DIRECT
    addressed: bool
    confidence: float
    explanation: str
    scene_references: list[int] = field(default_factory=list)
    suggestion: str = ""


# ----- JSON response schemas for Gemini structured output -----

SCRIPT_GENERATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "concept": {"type": "string"},
        "total_duration_seconds": {"type": "integer"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_number": {"type": "integer"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "visual_description": {"type": "string"},
                    "voiceover": {"type": "string"},
                    "on_screen_text": {"type": "string"},
                    "audio_direction": {"type": "string"},
                    "abcd_features_addressed": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "scene_number",
                    "start_time",
                    "end_time",
                    "visual_description",
                    "voiceover",
                    "on_screen_text",
                    "audio_direction",
                    "abcd_features_addressed",
                ],
            },
        },
        "improvement_suggestions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "title",
        "concept",
        "total_duration_seconds",
        "scenes",
        "improvement_suggestions",
    ],
}

SCRIPT_VALIDATION_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "feature_id": {"type": "string"},
            "feature_name": {"type": "string"},
            "sub_category": {"type": "string"},
            "addressed": {"type": "boolean"},
            "confidence": {"type": "number"},
            "explanation": {"type": "string"},
            "scene_references": {
                "type": "array",
                "items": {"type": "integer"},
            },
            "suggestion": {"type": "string"},
        },
        "required": [
            "feature_id",
            "feature_name",
            "sub_category",
            "addressed",
            "confidence",
            "explanation",
            "scene_references",
            "suggestion",
        ],
    },
}
