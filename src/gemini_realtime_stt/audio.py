import threading
from queue import Queue

import numpy as np
import pyaudio

from .config import AppConfig
from .console import BLUE, RED, RESET_COLOR


FORMAT = pyaudio.paInt16


def get_input_devices() -> str:
    p = pyaudio.PyAudio()
    info = "\nAvailable input devices:\n"

    try:
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            max_input_channels = int(dev_info.get("maxInputChannels", 0))
            if max_input_channels > 0:
                info += f"Device {i}: {dev_info.get('name')}\n"
    finally:
        p.terminate()

    return info


def record_audio(
    config: AppConfig,
    audio_queue: Queue,
    should_stop: threading.Event,
    device_index: int | None = None,
) -> None:
    p = pyaudio.PyAudio()

    try:
        kwargs = {
            "format": FORMAT,
            "channels": config.channels,
            "rate": config.sample_rate,
            "input": True,
            "frames_per_buffer": config.frames_per_buffer,
        }

        if device_index is not None:
            kwargs["input_device_index"] = device_index

        stream = p.open(**kwargs)

        print(f"{BLUE}Recording started. Press Ctrl+C to stop.{RESET_COLOR}")
        print(
            f"{BLUE}Listening for {config.record_seconds} seconds per chunk...{RESET_COLOR}"
        )

        # Discard a short warm-up window to reduce startup noise.
        warmup_iterations = int(config.sample_rate / config.frames_per_buffer * 0.5)
        for _ in range(warmup_iterations):
            stream.read(config.frames_per_buffer, exception_on_overflow=False)

        while not should_stop.is_set():
            frames = []
            iterations = int(config.sample_rate / config.frames_per_buffer * config.record_seconds)

            for _ in range(iterations):
                if should_stop.is_set():
                    break
                data = stream.read(config.frames_per_buffer, exception_on_overflow=False)
                frames.append(data)

            if frames and not should_stop.is_set():
                audio_data = np.frombuffer(b"".join(frames), dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))

                if config.debug_audio:
                    print(
                        f"{BLUE}Chunk RMS={rms:.2f} (threshold={config.silence_rms_threshold:.2f}){RESET_COLOR}"
                    )

                if rms > config.silence_rms_threshold:
                    audio_queue.put(frames)
                else:
                    print(f"{BLUE}Silence detected (RMS: {rms:.2f}), skipping...{RESET_COLOR}")

    except Exception as exc:
        print(f"{RED}Error in recording: {exc}{RESET_COLOR}")

    finally:
        if "stream" in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        print(f"{BLUE}Recording stopped.{RESET_COLOR}")
