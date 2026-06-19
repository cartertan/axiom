import sys
import time


class VoiceLoop:
    """Ties STT → router → agent → TTS into a push-to-talk conversational loop."""

    def __init__(self, config: dict = None, profile=None, memory=None, client=None, router=None):
        from src.voice.recorder import PushToTalkRecorder
        from src.voice.stt import SpeechToText
        from src.voice.tts import TextToSpeech
        from src.voice.text_cleaner import clean_for_speech

        self._recorder = PushToTalkRecorder()
        self._stt = SpeechToText(config)
        self._tts = TextToSpeech(config)
        self._clean = clean_for_speech
        self._config = config or {}

        self._profile = profile
        self._memory = memory
        self._client = client
        self._router = router

    def _get_agent(self, task_type: str):
        from src.agents.email_agent import EmailAgent
        from src.agents.email_sender_agent import EmailSenderAgent
        from src.agents.general_agent import GeneralAgent
        from src.agents.meeting_agent import MeetingAgent
        from src.agents.pki_agent import PKIAgent
        from src.agents.research_agent import ResearchAgent
        from src.agents.rfp_agent import RFPAgent
        from src.rag.retriever import PKIRetriever

        pki = PKIRetriever()
        c, p, m, cl = self._config, self._profile, self._memory, self._client
        if task_type == "EMAIL_SEND":
            return EmailSenderAgent(c, p, m, cl)
        if task_type == "EMAIL_DRAFT":
            return EmailAgent(c, p, m, cl)
        if task_type == "MEETING_SUMMARY":
            return MeetingAgent(c, p, m, cl)
        if task_type == "RFP_ANALYSIS":
            return RFPAgent(c, p, m, cl)
        if task_type == "PKI_QA":
            return PKIAgent(c, p, m, cl, pki)
        if task_type == "RESEARCH":
            return ResearchAgent(c, p, m, cl)
        return GeneralAgent(c, p, m, cl)

    def run(self) -> None:
        """Main conversational loop."""
        print("\nAXIOM Voice Interface — Phase 4")
        print("Press Ctrl+C or type 'quit' to exit.\n")

        while True:
            try:
                prompt = input("\nPress ENTER to speak to AXIOM (or type 'quit'): ").strip().lower()
                if prompt == "quit":
                    print("Goodbye.")
                    break

                audio_buf = self._recorder.record_interactive()
                if len(audio_buf) == 0:
                    print("[AXIOM] No audio captured.")
                    continue

                print("[AXIOM] Transcribing...")
                transcript = self._stt.record_and_transcribe(audio_buf)
                if not transcript.strip():
                    print("[AXIOM] Could not understand audio. Try again.")
                    continue

                print(f"\nYou said: {transcript}\n")

                task_type = self._router.classify(transcript)
                print(f"[AXIOM] Routing to: {task_type}")

                agent = self._get_agent(task_type)
                print("[AXIOM] Thinking...")

                start = time.time()
                response = agent.run(transcript, task_type)
                latency = time.time() - start

                print(f"\n── AXIOM ({task_type}, {latency:.1f}s) ──\n{response}\n{'─' * 48}\n")

                if self._memory:
                    self._memory.store_interaction(
                        task_type,
                        f"[voice] Q: {transcript[:120]} A: {response[:120]}",
                        metadata={"source": "voice"},
                    )

                print("[AXIOM] Speaking...")
                self._tts.speak(response)

            except KeyboardInterrupt:
                print("\nGoodbye.")
                break
            except Exception as e:
                print(f"[AXIOM error] {e}", file=sys.stderr)
