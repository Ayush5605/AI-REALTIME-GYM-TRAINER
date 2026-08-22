import time
import streamlit as st


class VoicePipeline:
    FORM_CORRECTION_COOLDOWN_SECONDS = 6
    MID_SET_FEEDBACK_INTERVAL_SECONDS = 12

    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0
        self.last_error = None

    def _find_form_issue(self, exercise, metrics):

        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)

            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."

            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."

            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")

            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."

            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")

            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."

            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")

            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        return None

    def process_event(self, event, exercise, metrics):

        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        is_priority_event = event in [
            "workout_started",
            "set_completed",
            "workout_completed",
            "mid_set_check_in",
        ]

        if not is_priority_event:
            cooldown = (
                self.FORM_CORRECTION_COOLDOWN_SECONDS
                if issue
                else self.MID_SET_FEEDBACK_INTERVAL_SECONDS
            )
            if now - self.last_spoken_at < cooldown:
                return None

        try:
            text = self.llm.give_feedback(event, exercise, metrics, issue)
        except Exception as error:
            self.last_error = self._service_error("Groq", error)
            return None

        try:
            voice = self.tts.speak(text)
        except Exception as error:
            self.last_error = self._service_error("text-to-speech", error)
            return None

        if not voice:
            self.last_error = "Voice coaching returned no audio. Please try again."
            return None

        self.last_spoken_at = now
        self.last_error = None

        return voice, text

    @staticmethod
    def _service_error(service, error):
        """Return a useful UI message without exposing credentials or tracebacks."""
        status_code = getattr(error, "status_code", None)

        if status_code == 401:
            return f"{service} rejected the configured API key."
        if status_code == 404:
            return f"The configured {service} model or service is unavailable."
        if status_code == 429:
            return f"{service} rate limit reached. Please wait a moment and try again."

        return f"{service} could not generate audio. Check your internet connection and try again."


# IMPORTANT:
# This is outside the VoicePipeline class
def autoplay_audio(audio_bytes):

    if not audio_bytes:
        return

    st.markdown(
        """
        <style>
        [data-testid='stAudio'] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.audio(
        audio_bytes,
        format="audio/mp3",
        autoplay=True
    )
