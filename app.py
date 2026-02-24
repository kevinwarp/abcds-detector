#!/usr/bin/env python3

###########################################################################
#
#  Copyright 2024 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

"""Flask web server for ABCDs Detector on Cloud Run"""

import os
import json
import traceback
from flask import Flask, request, jsonify

from generate_video_annotations.generate_video_annotations import (
    generate_video_annotations,
)
from trim_videos.trim_videos import trim_videos

from input_parameters import (
    BUCKET_NAME,
    VIDEO_SIZE_LIMIT_MB,
    brand_name,
    brand_variations,
    branded_products,
    branded_products_categories,
    branded_call_to_actions,
    use_llms,
    use_annotations,
)

from helpers.helpers import (
    bucket,
    get_file_name_from_gcs_url,
    download_video_annotations,
)

from features.a_quick_pacing import detect_quick_pacing
from features.a_dynamic_start import detect_dynamic_start
from features.a_supers import detect_supers, detect_supers_with_audio
from features.b_brand_visuals import detect_brand_visuals
from features.b_brand_mention_speech import detect_brand_mention_speech
from features.b_product_visuals import detect_product_visuals
from features.b_product_mention_text import detect_product_mention_text
from features.b_product_mention_speech import detect_product_mention_speech
from features.c_visible_face import detect_visible_face
from features.c_presence_of_people import detect_presence_of_people
from features.d_audio_speech_early import detect_audio_speech_early
from features.c_overall_pacing import detect_overall_pacing
from features.d_call_to_action import (
    detect_call_to_action_speech,
    detect_call_to_action_text,
)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "abcds-detector"})


@app.route("/assess", methods=["POST"])
def assess_videos():
    """Run ABCD assessment for all brand videos in GCS.

    Returns JSON with assessment results for each video.
    """
    try:
        if use_annotations:
            generate_video_annotations(brand_name)

        trim_videos(brand_name)

        assessments = _execute_abcd_assessment()

        if len(assessments.get("video_assessments")) == 0:
            return jsonify({"message": "No videos found to assess."}), 404

        return jsonify(assessments)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def _execute_abcd_assessment():
    """Execute ABCD Assessment for all brand videos in GCS"""

    assessments = {"brand_name": brand_name, "video_assessments": []}

    brand_videos_folder = f"{brand_name}/videos"
    blobs = bucket.list_blobs(prefix=brand_videos_folder)

    for video in blobs:
        if video.name == f"{brand_videos_folder}/" or "1st_5_secs" in video.name:
            continue

        video_name, video_name_with_format = get_file_name_from_gcs_url(video.name)
        if not video_name or not video_name_with_format:
            continue

        video_metadata = bucket.get_blob(video.name)
        size_mb = video_metadata.size / 1e6
        if use_llms and size_mb > VIDEO_SIZE_LIMIT_MB:
            continue

        label_annotation_results = {}
        face_annotation_results = {}
        people_annotation_results = {}
        shot_annotation_results = {}
        text_annotation_results = {}
        logo_annotation_results = {}
        speech_annotation_results = {}

        if use_annotations:
            (
                label_annotation_results,
                face_annotation_results,
                people_annotation_results,
                shot_annotation_results,
                text_annotation_results,
                logo_annotation_results,
                speech_annotation_results,
            ) = download_video_annotations(brand_name, video_name)

        video_uri = f"gs://{BUCKET_NAME}/{video.name}"

        quick_pacing, quick_pacing_1st_5_secs = detect_quick_pacing(
            shot_annotation_results, video_uri
        )
        dynamic_start = detect_dynamic_start(shot_annotation_results, video_uri)
        supers = detect_supers(text_annotation_results, video_uri)
        supers_with_audio = detect_supers_with_audio(
            text_annotation_results, speech_annotation_results, video_uri
        )
        (
            brand_visuals,
            brand_visuals_1st_5_secs,
            brand_visuals_logo_big_1st_5_secs,
        ) = detect_brand_visuals(
            text_annotation_results,
            logo_annotation_results,
            video_uri,
            brand_name,
            brand_variations,
        )
        (
            brand_mention_speech,
            brand_mention_speech_1st_5_secs,
        ) = detect_brand_mention_speech(
            speech_annotation_results, video_uri, brand_name, brand_variations
        )
        product_visuals, product_visuals_1st_5_secs = detect_product_visuals(
            label_annotation_results,
            video_uri,
            branded_products,
            branded_products_categories,
        )
        (
            product_mention_text,
            product_mention_text_1st_5_secs,
        ) = detect_product_mention_text(
            text_annotation_results,
            video_uri,
            branded_products,
            branded_products_categories,
        )
        (
            product_mention_speech,
            product_mention_speech_1st_5_secs,
        ) = detect_product_mention_speech(
            speech_annotation_results,
            video_uri,
            branded_products,
            branded_products_categories,
        )
        visible_face_1st_5_secs, visible_face_close_up = detect_visible_face(
            face_annotation_results, video_uri
        )
        presence_of_people, presence_of_people_1st_5_secs = detect_presence_of_people(
            people_annotation_results, video_uri
        )
        audio_speech_early = detect_audio_speech_early(
            speech_annotation_results, video_uri
        )
        overall_pacing = detect_overall_pacing(shot_annotation_results, video_uri)
        call_to_action_speech = detect_call_to_action_speech(
            speech_annotation_results, video_uri, branded_call_to_actions
        )
        call_to_action_text = detect_call_to_action_text(
            text_annotation_results, video_uri, branded_call_to_actions
        )

        features = [
            {"feature_description": "Quick Pacing", "feature_evaluation": quick_pacing},
            {"feature_description": "Quick Pacing (First 5 seconds)", "feature_evaluation": quick_pacing_1st_5_secs},
            {"feature_description": "Dynamic Start", "feature_evaluation": dynamic_start},
            {"feature_description": "Supers", "feature_evaluation": supers},
            {"feature_description": "Supers with Audio", "feature_evaluation": supers_with_audio},
            {"feature_description": "Brand Visuals", "feature_evaluation": brand_visuals},
            {"feature_description": "Brand Visuals (First 5 seconds)", "feature_evaluation": brand_visuals_1st_5_secs},
            {"feature_description": "Brand Mention (Speech)", "feature_evaluation": brand_mention_speech},
            {"feature_description": "Brand Mention (Speech) (First 5 seconds)", "feature_evaluation": brand_mention_speech_1st_5_secs},
            {"feature_description": "Product Visuals", "feature_evaluation": product_visuals},
            {"feature_description": "Product Visuals (First 5 seconds)", "feature_evaluation": product_visuals_1st_5_secs},
            {"feature_description": "Product Mention (Text)", "feature_evaluation": product_mention_text},
            {"feature_description": "Product Mention (Text) (First 5 seconds)", "feature_evaluation": product_mention_text_1st_5_secs},
            {"feature_description": "Product Mention (Speech)", "feature_evaluation": product_mention_speech},
            {"feature_description": "Product Mention (Speech) (First 5 seconds)", "feature_evaluation": product_mention_speech_1st_5_secs},
            {"feature_description": "Visible Face (First 5 seconds)", "feature_evaluation": visible_face_1st_5_secs},
            {"feature_description": "Visible Face (Close Up)", "feature_evaluation": visible_face_close_up},
            {"feature_description": "Presence of People", "feature_evaluation": presence_of_people},
            {"feature_description": "Presence of People (First 5 seconds)", "feature_evaluation": presence_of_people_1st_5_secs},
            {"feature_description": "Overall Pacing", "feature_evaluation": overall_pacing},
            {"feature_description": "Audio Speech Early", "feature_evaluation": audio_speech_early},
            {"feature_description": "Call To Action (Text)", "feature_evaluation": call_to_action_text},
            {"feature_description": "Call To Action (Speech)", "feature_evaluation": call_to_action_speech},
        ]

        total_features = len(features)
        passed_features_count = sum(1 for f in features if f.get("feature_evaluation"))
        score = (passed_features_count * 100) / total_features

        if score >= 80:
            result_label = "Excellent"
        elif score >= 65:
            result_label = "Might Improve"
        else:
            result_label = "Needs Review"

        assessments.get("video_assessments").append(
            {
                "video_name": video_name_with_format,
                "video_location": video_uri,
                "features": features,
                "passed_features_count": passed_features_count,
                "total_features": total_features,
                "score": round(score, 2),
                "result": result_label,
            }
        )

    return assessments


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
