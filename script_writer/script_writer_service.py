"""Core service for generating and validating ABCDs-compliant ad scripts."""

from __future__ import annotations

import json
import logging
from typing import Optional

from configuration import Configuration
from gcp_api_services.gemini_api_service import get_gemini_api_service
from models import LLMParameters
from script_writer.script_models import (
    GeneratedScript,
    ScriptBrief,
    ScriptScene,
    ScriptValidationResult,
    SCRIPT_GENERATION_RESPONSE_SCHEMA,
    SCRIPT_VALIDATION_RESPONSE_SCHEMA,
)
from script_writer.script_prompt_generator import script_prompt_generator


logger = logging.getLogger(__name__)


class ScriptWriterService:
    """Generates ad scripts using LLMs and validates them against ABCDs."""

    def generate_script(
        self,
        config: Configuration,
        brief: ScriptBrief,
    ) -> GeneratedScript:
        """Generate an ad script from a creative brief.

        Args:
            config: Application configuration (project ID, LLM params, etc.).
            brief: The creative brief describing brand, audience, and goals.

        Returns:
            A GeneratedScript with scenes, concept, and improvement suggestions.
        """
        logger.info("Generating script for brand=%s product=%s", brief.brand_name, brief.product_name)

        prompt_config = script_prompt_generator.get_script_generation_prompt(brief)

        # Build LLM params — text-only modality (no video input)
        llm_params = LLMParameters()
        llm_params.model_name = config.llm_params.model_name
        llm_params.location = config.llm_params.location
        llm_params.generation_config = {
            **config.llm_params.generation_config,
            "response_schema": SCRIPT_GENERATION_RESPONSE_SCHEMA,
        }
        llm_params.set_modality({"type": "text"})

        raw = get_gemini_api_service(config).execute_gemini_with_genai(
            prompt_config, llm_params
        )

        return self._parse_generation_response(raw)

    def validate_script(
        self,
        config: Configuration,
        script: GeneratedScript,
    ) -> list[ScriptValidationResult]:
        """Validate a generated script against ABCDs features.

        Args:
            config: Application configuration.
            script: The script to validate.

        Returns:
            A list of ScriptValidationResult, one per ABCDs feature.
        """
        logger.info("Validating script '%s' against ABCDs", script.title)

        script_text = self._script_to_text(script)
        prompt_config = script_prompt_generator.get_script_validation_prompt(script_text)

        llm_params = LLMParameters()
        llm_params.model_name = config.llm_params.model_name
        llm_params.location = config.llm_params.location
        llm_params.generation_config = {
            **config.llm_params.generation_config,
            "response_schema": SCRIPT_VALIDATION_RESPONSE_SCHEMA,
        }
        llm_params.set_modality({"type": "text"})

        raw = get_gemini_api_service(config).execute_gemini_with_genai(
            prompt_config, llm_params
        )

        return self._parse_validation_response(raw)

    def generate_and_validate(
        self,
        config: Configuration,
        brief: ScriptBrief,
    ) -> tuple[GeneratedScript, list[ScriptValidationResult]]:
        """Generate a script and immediately validate it against ABCDs.

        Returns:
            Tuple of (GeneratedScript, list of ScriptValidationResult).
        """
        script = self.generate_script(config, brief)
        validations = self.validate_script(config, script)

        # Attach ABCD score summary to the script
        total = len(validations)
        passed = sum(1 for v in validations if v.addressed)
        script.abcd_score_summary = {
            "total_features": total,
            "features_addressed": passed,
            "score_pct": round((passed / total) * 100, 1) if total else 0,
            "by_category": self._score_by_category(validations),
        }

        return script, validations

    # ---- internal helpers ----

    @staticmethod
    def _parse_generation_response(raw) -> GeneratedScript:
        """Convert the LLM JSON response into a GeneratedScript."""
        if isinstance(raw, str):
            raw = json.loads(raw)

        if not raw:
            logger.warning("Empty response from LLM during script generation")
            return GeneratedScript(title="", concept="")

        scenes = [
            ScriptScene(
                scene_number=s.get("scene_number", i + 1),
                start_time=s.get("start_time", "0:00"),
                end_time=s.get("end_time", "0:00"),
                visual_description=s.get("visual_description", ""),
                voiceover=s.get("voiceover", ""),
                on_screen_text=s.get("on_screen_text", ""),
                audio_direction=s.get("audio_direction", ""),
                abcd_features_addressed=s.get("abcd_features_addressed", []),
            )
            for i, s in enumerate(raw.get("scenes", []))
        ]

        return GeneratedScript(
            title=raw.get("title", ""),
            concept=raw.get("concept", ""),
            scenes=scenes,
            total_duration_seconds=raw.get("total_duration_seconds", 0),
            improvement_suggestions=raw.get("improvement_suggestions", []),
        )

    @staticmethod
    def _parse_validation_response(raw) -> list[ScriptValidationResult]:
        """Convert the LLM JSON response into ScriptValidationResult list."""
        if isinstance(raw, str):
            raw = json.loads(raw)

        if not raw:
            logger.warning("Empty response from LLM during script validation")
            return []

        return [
            ScriptValidationResult(
                feature_id=v.get("feature_id", ""),
                feature_name=v.get("feature_name", ""),
                sub_category=v.get("sub_category", ""),
                addressed=v.get("addressed", False),
                confidence=v.get("confidence", 0.0),
                explanation=v.get("explanation", ""),
                scene_references=v.get("scene_references", []),
                suggestion=v.get("suggestion", ""),
            )
            for v in raw
        ]

    @staticmethod
    def _script_to_text(script: GeneratedScript) -> str:
        """Render a GeneratedScript into a human-readable text block."""
        lines = [
            f"# {script.title}",
            f"Concept: {script.concept}",
            f"Duration: {script.total_duration_seconds}s",
            "",
        ]
        for scene in script.scenes:
            lines.append(f"## Scene {scene.scene_number} [{scene.start_time} - {scene.end_time}]")
            lines.append(f"Visual: {scene.visual_description}")
            lines.append(f"Voiceover: {scene.voiceover}")
            lines.append(f"On-Screen Text: {scene.on_screen_text}")
            lines.append(f"Audio/SFX: {scene.audio_direction}")
            if scene.abcd_features_addressed:
                lines.append(f"ABCDs: {', '.join(scene.abcd_features_addressed)}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _score_by_category(validations: list[ScriptValidationResult]) -> dict:
        """Aggregate validation scores by ABCD sub-category."""
        categories: dict[str, dict] = {}
        for v in validations:
            cat = v.sub_category.upper() if v.sub_category else "OTHER"
            if cat not in categories:
                categories[cat] = {"total": 0, "addressed": 0}
            categories[cat]["total"] += 1
            if v.addressed:
                categories[cat]["addressed"] += 1

        return {
            cat: {
                **counts,
                "score_pct": round((counts["addressed"] / counts["total"]) * 100, 1)
                if counts["total"]
                else 0,
            }
            for cat, counts in categories.items()
        }


script_writer_service = ScriptWriterService()
