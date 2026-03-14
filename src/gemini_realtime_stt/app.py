import threading
import time
from queue import Queue
from typing import Optional

from .audio import record_audio
from .config import load_config
from .gemini_client import configure_gemini
from .pipeline import process_audio


def run() -> None:
    config = load_config()
    configure_gemini(config.google_api_key)

    should_stop = threading.Event()
    audio_queue: Queue = Queue()

    record_thread: Optional[threading.Thread] = None
    process_thread: Optional[threading.Thread] = None

    try:
        record_thread = threading.Thread(
            target=record_audio,
            args=(config, audio_queue, should_stop),
        )
        process_thread = threading.Thread(
            target=process_audio,
            args=(config, audio_queue, should_stop),
        )

        record_thread.start()
        process_thread.start()

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        should_stop.set()

        if record_thread is not None:
            record_thread.join()
        if process_thread is not None:
            process_thread.join()
