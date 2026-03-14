import os
import time

import google.generativeai as genai

from .config import AppConfig
from .console import RED, RESET_COLOR


def configure_gemini(api_key: str) -> None:
    genai.configure(api_key=api_key)


def transcribe_chunk(config: AppConfig, chunk_file: str) -> str:
    try:
        if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) < 100:
            print(f"{RED}Warning: Audio file empty or too small{RESET_COLOR}")
            return ""

        with open(chunk_file, "rb") as f:
            file_content = f.read()

        model = genai.GenerativeModel(model_name=config.model_name)
        transcription_prompt = (
            "Transcribe the speech in this audio file. "
            "Only return the transcribed text. "
            "If no intelligible speech is detected, return an empty response."
        )

        response = model.generate_content(
            contents=[
                {"text": transcription_prompt},
                {"inline_data": {"mime_type": "audio/wav", "data": file_content}},
            ]
        )
        transcription = (response.text or "").strip()
        normalized = transcription.lower().replace("_", " ")

        if not transcription or "no speech detected" in normalized:
            return ""

        if config.debug_audio:
            print(f"Raw transcription: {transcription}")

        if config.target_language and config.target_language.lower() != "auto":
            if (
                config.source_language != "auto"
                and config.source_language.lower() == config.target_language.lower()
            ):
                return transcription

            if config.source_language == "auto":
                translation_prompt = (
                    f"Translate the following text to {config.target_language}. "
                    f"Return only the translated text:\n\n{transcription}"
                )
            else:
                translation_prompt = (
                    f"Translate this from {config.source_language} to "
                    f"{config.target_language}. Return only the translated text:\n\n"
                    f"{transcription}"
                )

            translation_response = model.generate_content(translation_prompt)
            return translation_response.text.strip()

        return transcription

    except Exception as exc:
        print(f"{RED}Error translating chunk: {exc}{RESET_COLOR}")
        time.sleep(1)
        return ""
