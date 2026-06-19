# AXIOM — Phase 4 Implementation Plan
**Date:** 2026-06-19
**Version Target:** v0.4.0
**Branch:** phase-4-voice
**Status:** Ready to execute

---

## Phase 4 Goal

Give AXIOM a voice. Speak to it, it speaks back. Fully local.

This is the Tony Stark moment — the phase where AXIOM stops being something you
type at and becomes something you talk to.

By end of Phase 4:
```bash
# Push-to-talk: hold a hotkey, speak, release
axiom voice

# AXIOM transcribes locally (whisper.cpp), routes the task, runs the agent,
# and speaks the answer back (Voxtral TTS) — all on the Mac, no cloud.
```

---

## Architecture: The Voice Loop

```
[Push-to-talk hotkey held]
        ↓
Microphone captures audio (sounddevice)
        ↓
[hotkey released]
        ↓
whisper.cpp (Metal GPU) → transcribed text      ~1-2 sec
        ↓
AXIOM Task Router (gemma4:e4b)                   <1 sec
        ↓
Agent runs (existing Phase 1-3 agents)           varies
        ↓
Response text → cleaned for speech
        ↓
Voxtral TTS (MLX) → audio                        ~1-2 sec
        ↓
Speaker playback (sounddevice)
        ↓
[ready for next turn]
```

---

## Design Decisions

- **STT engine:** whisper.cpp with Metal (10-12x real-time on M5 Pro, ~100ms)
- **STT model:** large-v3-turbo (95% of large-v3 accuracy, 4-6x faster) —
  important for technical PKI vocabulary where small models make errors
- **TTS engine:** Voxtral TTS (MLX 4-bit) — natural voice, runs faster than playback
- **Trigger:** Push-to-talk (hotkey) for v1 — more reliable than wake word
- **Cost:** ~$3/month in power vs $86+/month for cloud STT. Fully local.
- **Privacy:** Voice never leaves the Mac — critical for an assistant that
  handles customer and PKI context

---

## Pre-Build — Setup

### Step 0.1: Branch
```bash
cd ~/AI-Projects/axiom
git checkout main && git pull origin main
git checkout -b phase-4-voice
```

### Step 0.2: Install whisper.cpp with Metal
```bash
cd ~/AI-Projects
git clone https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
cmake -B build -DWHISPER_METAL=ON -DWHISPER_SDL2=ON
cmake --build build -j --config Release
# Download the turbo model (best accuracy/speed balance)
bash ./models/download-ggml-model.sh large-v3-turbo
cd ~/AI-Projects/axiom
```

Verification:
```bash
~/AI-Projects/whisper.cpp/build/bin/whisper-cli \
  -m ~/AI-Projects/whisper.cpp/models/ggml-large-v3-turbo.bin \
  -f ~/AI-Projects/whisper.cpp/samples/jfk.wav
# Should transcribe the sample audio
```

### Step 0.3: Install Python audio + MLX dependencies
```bash
pip install sounddevice numpy mlx mlx-audio --break-system-packages
# pyaudio alternative if sounddevice has issues:
# brew install portaudio && pip install pyaudio --break-system-packages
```

### Step 0.4: Download Voxtral TTS (MLX)
```bash
# Via huggingface-cli (install if needed: pip install huggingface-hub)
huggingface-cli download mlx-community/Voxtral-TTS-4bit --local-dir ~/AI-Projects/axiom/models/voxtral
```

### Step 0.5: Update requirements.txt
```
sounddevice>=0.4.6
numpy>=1.26.0
mlx>=0.15.0
mlx-audio>=0.1.0
```

### Step 0.6: Grant microphone permission
macOS will prompt for microphone access on first run.
System Settings → Privacy & Security → Microphone → enable Terminal/iTerm.

---

## BLOCK R — Speech to Text

**Task R1: Create src/voice/stt.py**

Claude Code prompt:
```
Create src/voice/stt.py.
Requirements:
- SpeechToText class
- Wraps whisper.cpp via subprocess (the whisper-cli binary)
- Config: path to whisper.cpp binary and model (from config, with sensible defaults
  pointing at ~/AI-Projects/whisper.cpp/)
- record_and_transcribe(max_seconds=30) method:
  - Records from the default microphone using sounddevice until stopped
    (for v1, record a fixed window or until a key release signal)
  - Saves to a temp WAV file (16kHz mono, which whisper expects)
  - Calls whisper-cli on the temp file
  - Parses the transcribed text from output
  - Cleans up the temp file
  - Returns the transcribed string
- transcribe_file(path) method for testing with existing audio
- Handle the case where whisper.cpp binary or model is missing — clear error
  telling the user to run the Step 0.2 setup
```

Verification:
```bash
python3 -c "
from src.voice.stt import SpeechToText
stt = SpeechToText()
print(stt.transcribe_file('$HOME/AI-Projects/whisper.cpp/samples/jfk.wav'))
"
```

---

**Task R2: Create push-to-talk capture in src/voice/recorder.py**

Claude Code prompt:
```
Create src/voice/recorder.py.
Requirements:
- PushToTalkRecorder class
- Uses sounddevice to capture microphone audio
- start() begins recording, stop() ends and returns the audio buffer as a
  16kHz mono numpy array (whisper-compatible)
- A simple console mode: "Press ENTER to start speaking, ENTER again to stop"
  (keyboard hotkey libraries can be flaky with mic permissions; ENTER-to-toggle
  is the reliable v1 approach)
- save_wav(buffer, path) helper to write the WAV for whisper
- Handle microphone-permission errors with a clear message pointing to
  System Settings → Privacy & Security → Microphone
```

Verification:
```bash
python3 -c "
from src.voice.recorder import PushToTalkRecorder
r = PushToTalkRecorder()
buf = r.record_interactive()  # press ENTER, speak, ENTER
r.save_wav(buf, '/tmp/test.wav')
print('saved')
"
```

---

## BLOCK S — Text to Speech

**Task S1: Create src/voice/tts.py**

Claude Code prompt:
```
Create src/voice/tts.py.
Requirements:
- TextToSpeech class
- Uses Voxtral TTS via mlx-audio (the MLX 4-bit model in models/voxtral)
- speak(text) method:
  - Cleans the text for speech first: strip markdown (**bold**, #headers,
    bullet characters), expand common abbreviations sensibly for a PKI context
    (e.g. "OCSP" stays as letters, "e.g." → "for example"), collapse whitespace
  - Generates audio via the Voxtral MLX model
  - Plays it back via sounddevice
  - For long responses, split into sentences and stream playback so AXIOM
    starts speaking before the whole thing is generated
- save_audio(text, path) method for testing
- Handle missing model with a clear setup message
- Config: voice/speed settings in config
```

Verification:
```bash
python3 -c "
from src.voice.tts import TextToSpeech
tts = TextToSpeech()
tts.speak('AXIOM voice interface online. Phase 4 is operational.')
"
```
Should play audio through speakers.

---

**Task S2: Add speech text cleaning to src/voice/text_cleaner.py**

Claude Code prompt:
```
Create src/voice/text_cleaner.py.
Requirements:
- clean_for_speech(text) function
- Removes markdown formatting (bold, italic, headers, bullets, code fences)
- Removes URLs or replaces with "link"
- Keeps technical acronyms readable (PKI, OCSP, CRL, HSM, TLS, ACME stay as-is —
  the TTS will spell them naturally)
- Converts numbered/bulleted lists into spoken form ("First... Second...")
- Trims to a reasonable spoken length; if very long, summarise-for-speech note
  that the full text is available in the UI
- Pure function, easy to unit test
```

Verification:
```bash
python3 -c "
from src.voice.text_cleaner import clean_for_speech
print(clean_for_speech('## Summary\n- **OCSP** is faster\n- See https://example.com'))
"
```

---

## BLOCK T — Voice Loop Integration

**Task T1: Create src/voice/voice_loop.py**

Claude Code prompt:
```
Create src/voice/voice_loop.py.
Requirements:
- VoiceLoop class that ties STT → router → agent → TTS together
- Reuses ALL existing AXIOM components (router, agents, memory, orchestrator)
- run() method — the conversational loop:
  1. Prompt: "Press ENTER to speak to AXIOM (or type 'quit')"
  2. Record via PushToTalkRecorder
  3. Transcribe via SpeechToText
  4. Print the transcription so Carter can confirm it heard correctly
  5. Route + run the appropriate agent (same logic as axiom.py)
  6. Clean response for speech
  7. Speak via TextToSpeech AND print the full text
  8. Log the interaction to memory (mark source as "voice")
  9. Loop
- Spoken responses use a faster/lighter model by default (gemma4:e4b or the
  task's normal model) — Carter can still trigger --mode ensemble by saying
  "deep analysis" or similar, but default voice = fast single model for
  conversational feel
- Graceful exit on "quit" / Ctrl+C
```

Verification:
```bash
python3 -c "
from src.voice.voice_loop import VoiceLoop
# Smoke test imports and init only
vl = VoiceLoop()
print('VoiceLoop initialised OK')
"
```

---

**Task T2: Wire `axiom voice` command into axiom.py**

Claude Code prompt:
```
Update axiom.py to add a 'voice' subcommand:
  python3 axiom.py voice   → launches VoiceLoop.run()
Print the AXIOM banner, confirm whisper.cpp and Voxtral are available
(clear setup message if not), then start the loop.
Keep all existing commands working (single task, benchmark, interactive,
task, research, --mode).
```

Verification:
```bash
python3 axiom.py voice
# Press ENTER, say "what is OCSP stapling", confirm AXIOM speaks the answer
```

---

## BLOCK U — Optional: Voice Cloning (Stretch Goal)

**Task U1: Carter's voice clone (optional, only if time permits)**

Voxtral can clone a voice from ~3 seconds of audio. This is a stretch goal.

Claude Code prompt:
```
Create scripts/clone_voice.py (optional stretch goal).
Requirements:
- Records or accepts a short (5-10 sec) clean sample of Carter's voice
- Uses Voxtral's voice cloning to create a custom voice profile
- Saves the profile to models/voxtral/carter_voice/
- TextToSpeech can then use this profile so AXIOM speaks in Carter's voice
- Document clearly that this is for personal use only
- Add a config flag: voice.use_clone: true/false
```

Verification: Generate a test phrase in the cloned voice, compare to default.

NOTE: Skip this if the core voice loop took the full session. It's a
"wow factor" addition, not core functionality.

---

## BLOCK V — Docs + Git

**Task V1: Update README.md + JOURNAL.md**
- Document the voice interface (`axiom voice`)
- Document the whisper.cpp + Voxtral setup steps (Step 0.2-0.4)
- Note the cost/privacy rationale (local STT ~$3/mo vs $86+ cloud)
- Add a setup prerequisites section for voice (it needs external binaries)
- Update roadmap: Phase 4 complete

**Task V2: Update .gitignore**
```
models/voxtral/
*.wav
/tmp/axiom_audio/
```
(Voice models are large — never commit them)

**Task V3: Commit, merge, tag**
```bash
cd ~/AI-Projects/axiom
git add .
git commit -m "feat: AXIOM v0.4.0 — voice interface

- Speech-to-text via whisper.cpp (Metal, large-v3-turbo)
- Text-to-speech via Voxtral TTS (MLX 4-bit)
- Push-to-talk voice loop reusing all existing agents
- Speech text cleaning for natural spoken output
- Fully local: voice never leaves the Mac (~\$3/mo vs \$86+ cloud)
- Optional voice cloning (stretch)
"
git checkout main && git merge phase-4-voice
git tag v0.4.0
git push origin main --tags
git branch -d phase-4-voice
```

---

## Phase 4 Success Criteria

```bash
# 1. STT works on a sample file
python3 -c "from src.voice.stt import SpeechToText; print(SpeechToText().transcribe_file('$HOME/AI-Projects/whisper.cpp/samples/jfk.wav'))"
# PASS if: returns accurate transcription

# 2. TTS speaks
python3 -c "from src.voice.tts import TextToSpeech; TextToSpeech().speak('AXIOM is online')"
# PASS if: audio plays through speakers

# 3. Text cleaning
python3 -c "from src.voice.text_cleaner import clean_for_speech; print(clean_for_speech('## Test\n- **bold** item'))"
# PASS if: markdown stripped, readable text returned

# 4. Full voice loop — the Tony Stark moment
python3 axiom.py voice
# Say: "what is OCSP stapling and why does it matter"
# PASS if: AXIOM transcribes, answers, AND speaks the answer aloud

# 5. Voice routes to correct agent
python3 axiom.py voice
# Say: "draft a follow-up email to the Singtel team"
# PASS if: routes to EMAIL_DRAFT, drafts in Carter's voice, speaks it

# 6. Regression — all previous phases work
python3 axiom.py "draft an email"          # CLI
python3 axiom.py "analyse RFP" --mode ensemble  # orchestration
python3 server.py                          # web UI
# PASS if: all still function

# 7. GitHub
# PASS if: v0.4.0 tagged and pushed
```

---

## Execution Order

```
0.1 → 0.6                  # Branch + whisper.cpp + Voxtral + audio deps
R1 → R2                    # Speech to text + recorder
S1 → S2                    # Text to speech + cleaner
T1 → T2                    # Voice loop + axiom.py wiring
U1                          # Voice clone (OPTIONAL — skip if short on time)
V1 → V2 → V3               # Docs + gitignore + merge
```

Total tasks: 11 (10 core + 1 optional)
Estimated: 1 focused session, but setup (Block 0) is heavier than usual
because of external binaries (whisper.cpp build + model downloads)

---

## Important Build Notes for Claude Code

- whisper.cpp and Voxtral are EXTERNAL to the Python project — they're binaries
  and model files, installed via Block 0, not pip packages AXIOM ships
- The voice models are large (whisper-turbo ~1.5GB, Voxtral ~2.5GB) — gitignored
- Microphone permission is a macOS system prompt — Carter must grant it manually
- ENTER-to-toggle recording is the reliable v1 trigger; true hotkey/wake-word
  can come in a later iteration (keyboard libs conflict with mic permissions)
- Default voice responses to a FAST model for conversational feel; reserve
  ensemble/debate for when Carter explicitly asks for deep analysis
- Keep the full text printed alongside spoken output — Carter will want to
  read longer technical answers, not just hear them
