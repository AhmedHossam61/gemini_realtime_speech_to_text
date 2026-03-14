import os
import threading
import time
import wave
from queue import Queue

from .config import AppConfig
from .console import BLUE, RED, RESET_COLOR
from .gemini_client import transcribe_chunk


def save_audio_as_wav(config: AppConfig, frames: list[bytes], filename: str) -> None:
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(config.channels)
        wf.setsampwidth(2)
        wf.setframerate(config.sample_rate)
        wf.writeframes(b"".join(frames))


def process_audio(
    config: AppConfig,
    audio_queue: Queue,
    should_stop: threading.Event,
) -> None:
    accumulated_transcription = ""
    chunk_file = "temp_chunk.wav"
    chunk_counter = 0

    try:
        while not should_stop.is_set() or not audio_queue.empty():
            if audio_queue.empty():
                time.sleep(0.1)
                continue

            frames = audio_queue.get()
            chunk_counter += 1

            save_audio_as_wav(config, frames, chunk_file)
            translation = transcribe_chunk(config, chunk_file)

            if translation and translation.strip():
                print(f"{translation}{RESET_COLOR}")
                accumulated_transcription += translation + " "
            else:
                print(
                    f"{RED}No transcription returned for chunk {chunk_counter}. "
                    f"Try lowering SILENCE_RMS_THRESHOLD or checking input device.{RESET_COLOR}"
                )

            try:
                os.remove(chunk_file)
            except OSError:
                pass

    except Exception as exc:
        print(f"{RED}Error in processing: {exc}{RESET_COLOR}")

    finally:
        with open(config.output_file, "w", encoding="utf-8") as f:
            f.write(accumulated_transcription)
        print(f"{BLUE}Translation saved to {config.output_file}{RESET_COLOR}")
