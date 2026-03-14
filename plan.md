# Plan: Fix Silence Hallucination Issue

## The Main Problem

**The RMS silence detection is too coarse — it measures average energy across the entire 3-second chunk.**

This means:
- A 3s chunk with 2.8s of silence + 0.2s of a cough/breath/click can produce an RMS above 300, passing the threshold.
- That near-silent audio gets sent to Gemini, which hallucinates entire sentences from noise.
- `gemini-3.0-flash` is especially aggressive — it tries harder to produce output even from garbage audio.
- During conversation pauses or at the end, borderline chunks leak through and generate phantom text.

Secondary issues:
- No **minimum speech duration** check — a chunk needs real sustained speech, not a single noise spike.
- No **output sanity check** — if 3s of audio produces 200 words, something is wrong.
- During **shutdown**, queued borderline chunks still get processed and generate hallucinated output.
- The `load_config` fallback still says `gemini-2.5-flash` but the dataclass says `gemini-3.0-flash` (mismatch).

---

## Fix Plan

### Fix 1 — Voice Activity Detection (VAD) with per-frame energy analysis
**File: `audio.py`**

Instead of computing a single RMS over the full chunk, split the chunk into small frames (~20ms each) and count how many frames exceed the silence threshold. Only send the chunk to the queue if enough frames have speech energy (e.g., at least 30% of frames).

This prevents single noise spikes from triggering a false positive.

- [ ] Implement per-frame energy analysis in `record_audio()`
- [ ] Add `min_speech_ratio` config (default 0.3 = 30% of frames must have speech)

### Fix 2 — Double-check RMS on the WAV bytes before sending to Gemini
**File: `pipeline.py`**

Add a secondary RMS check in `process_audio()` right before calling `transcribe_chunk()`. This is a safety net in case a borderline chunk slipped past audio.py.

- [ ] Add RMS re-check in `process_audio()` before submitting to executor

### Fix 3 — Output length sanity check
**File: `gemini_client.py`**

If 3 seconds of audio produces an unreasonable amount of text (e.g., >50 words for a 3s chunk), it's almost certainly hallucinated. Discard it.

- [ ] Add word-count cap relative to chunk duration (e.g., max ~15 words/sec)
- [ ] Log discarded outputs when `debug_audio=True`

### Fix 4 — Drain queue on shutdown instead of processing
**File: `pipeline.py`**

When `should_stop` is set, don't process remaining queued chunks — they're likely silence/noise from the tail end. Just drain and discard them.

- [ ] On `should_stop`, cancel pending futures and drain the queue

### Fix 5 — Align model fallback in `load_config`
**File: `config.py`**

- [ ] Change `load_config` fallback from `gemini-2.5-flash` to `gemini-3.0-flash`

---

## Expected Impact

| Fix | Effect |
|-----|--------|
| Fix 1 (VAD) | **Primary fix** — eliminates 90%+ of false positives from noise spikes |
| Fix 2 (double-check) | Safety net for edge cases |
| Fix 3 (output cap) | Catches hallucinations that slip through |
| Fix 4 (shutdown drain) | Stops phantom text at end of conversation |
| Fix 5 (config align) | Prevents wrong model being loaded from env |
