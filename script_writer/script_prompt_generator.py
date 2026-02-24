"""Prompt generator for ABCDs-compliant ad script generation and validation."""

from models import PromptConfig
from script_writer.script_models import ScriptBrief, ScriptFormat


# Core ABCDs guidelines injected into every script generation prompt.
ABCDS_GUIDELINES = """
## Google ABCDs of Effective Video Ads

### A - ATTRACT: Hook viewers from the start
- Dynamic Start: The first shot should change within the first 3 seconds.
- Quick Pacing: Include rapid shot changes (aim for 5+ shots in the first 5 seconds).
- Supers: Use text overlays to reinforce the message.
- Supers with Audio: Pair on-screen text with matching spoken audio.

### B - BRAND: Integrate the brand naturally and early
- Brand Visuals: Show the brand name or logo early (ideally within the first 5 seconds) and throughout.
- Brand Mention (Speech): Say the brand name aloud, especially within the first 5 seconds.
- Product Visuals: Show the product or packaging early and prominently.
- Product Mention (Speech): Name the product aloud early in the ad.
- Product Mention (Text): Display the product name as on-screen text.

### C - CONNECT: Build an emotional connection with the audience
- Overall Pacing: Maintain an engaging pace (less than 2 seconds per shot).
- Presence of People: Feature people in the ad, especially within the first 5 seconds.
- Visible Face: Show a close-up of a human face early to create connection.

### D - DIRECT: Drive the viewer to take action
- Audio Early: Include speech in the first 5 seconds to immediately engage.
- Call To Action (Speech): Speak a clear call to action.
- Call To Action (Text): Display a clear call to action as on-screen text.
"""

SHORTS_ADDITIONAL_GUIDELINES = """
## Additional Guidelines for YouTube Shorts / Short-Form Video
- Keep the total duration under 60 seconds.
- Use a vertical (9:16) framing mindset — describe visuals accordingly.
- Lean into trends, quick cuts, and native-feeling content.
- Consider creator-style presentation (personal character, talking to camera).
- Disclose partnerships clearly if applicable.
- Use emojis or text overlays common to the platform.
"""


class ScriptPromptGenerator:
    """Generates prompts for ad script creation and validation."""

    def get_script_generation_prompt(self, brief: ScriptBrief) -> PromptConfig:
        """Build the prompt config for generating an ad script."""

        format_guidelines = ""
        if brief.script_format == ScriptFormat.SHORTS:
            format_guidelines = SHORTS_ADDITIONAL_GUIDELINES

        system_instructions = f"""
You are AdScript AI, a world-class advertising copywriter and creative director
who specialises in producing video ad scripts that follow Google's ABCDs of
Effective Video Ads.

Your task is to generate a complete, production-ready video ad script that
strictly adheres to the ABCDs framework.

{ABCDS_GUIDELINES}
{format_guidelines}

## OUTPUT RULES
- Structure the script as a sequence of numbered scenes.
- Each scene MUST include: visual_description, voiceover, on_screen_text,
  audio_direction, and a list of abcd_features_addressed (use the feature
  sub-category codes: ATTRACT, BRAND, CONNECT, DIRECT).
- Use realistic M:SS timestamps that fit within the requested duration.
- The concept field should be a 1-2 sentence elevator pitch of the creative idea.
- Provide actionable improvement_suggestions noting any ABCDs features that
  could not be fully addressed within the given constraints.
- Do NOT hallucinate brand details. Only use what is provided in the brief.
- Keep voiceover copy concise and speakable within each scene's time window.
"""

        prompt = f"""
## CREATIVE BRIEF

Brand Name: {brief.brand_name}
Product: {brief.product_name}
Product Description: {brief.product_description}
Target Audience: {brief.target_audience}
Key Message: {brief.key_message}
Call To Action: {brief.call_to_action}
Tone: {brief.tone.value}
Format: {brief.script_format.value}
Target Duration: {brief.duration_seconds} seconds
{f'Brand Guidelines: {brief.brand_guidelines}' if brief.brand_guidelines else ''}
{f'Additional Instructions: {brief.additional_instructions}' if brief.additional_instructions else ''}

Generate a complete ad script that maximises ABCDs compliance for this brief.
"""

        return PromptConfig(prompt=prompt, system_instructions=system_instructions)

    def get_script_validation_prompt(self, script_text: str) -> PromptConfig:
        """Build the prompt config for validating a script against ABCDs."""

        system_instructions = f"""
You are ABCDs Compliance Auditor, a meticulous expert who evaluates video ad
scripts against Google's ABCDs framework.

{ABCDS_GUIDELINES}

## YOUR TASK
Evaluate the provided ad script against each of the core ABCDs features listed
below. For every feature, determine whether the script adequately addresses it.

## FEATURES TO EVALUATE
- a_dynamic_start: Does the script open with a shot change within 3 seconds?
- a_quick_pacing: Are there rapid shot changes (5+ in any 5s window)?
- a_supers: Are text overlays specified?
- a_supers_with_audio: Do text overlays match spoken audio?
- b_brand_visuals: Is the brand logo/name shown, especially in the first 5s?
- b_brand_mention_speech: Is the brand name spoken, especially in the first 5s?
- b_product_visuals: Is the product visually present, especially early?
- b_product_mention_speech: Is the product mentioned in speech?
- b_product_mention_text: Is the product shown in on-screen text?
- c_overall_pacing: Is the pacing under 2 seconds per shot?
- c_presence_of_people: Are people featured in the ad?
- c_visible_face: Is a close-up human face shown early?
- d_audio_speech_early: Is there speech in the first 5 seconds?
- d_call_to_action_speech: Is a spoken CTA included?
- d_call_to_action_text: Is a text CTA included?

## OUTPUT RULES
- For each feature, return: addressed (bool), confidence (0.0–1.0),
  explanation, scene_references (scene numbers), and suggestion if not addressed.
- Be strict: only mark as addressed if the script clearly describes that element.
- Do NOT give credit for features that are merely implied but not specified.
"""

        prompt = f"""
Evaluate the following ad script against the ABCDs framework:

{script_text}
"""

        return PromptConfig(prompt=prompt, system_instructions=system_instructions)


script_prompt_generator = ScriptPromptGenerator()
