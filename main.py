import sys
import os

# Ensure project root is in sys.path for Streamlit Cloud deployment
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import textwrap
import time
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline,autoplay_audio

from streamlit_webrtc import ( webrtc_streamer,WebRtcMode)

from services.auth.login_wall import render_login_wall
from services.state.session_default import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import (load_css,inject_local_font,inject_webrtc_styles)
from services.persistence.exercise_repository import (
    add_exercise,
    get_users_exercises,
    init_db,
)
from services.vision.exercise_video_processor import  VideoProcessorClass
from services.tracking.metrics import sync_metrics_update


# Streamlit does not load a project's .env file automatically.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

VOICE_PIPELINE_VERSION = 2


def render_workout_history():
    """Show the signed-in user's saved workout totals."""
    user_id = st.session_state.get("user_id")
    if user_id is None:
        return

    records = get_users_exercises(user_id)
    st.subheader("Workout History")

    if not records:
        st.caption("No completed workouts yet.")
        return

    history = pd.DataFrame(
        [
            {
                "Exercise": record["exercise_name"],
                "Sets": record["sets"],
                "Reps": record["reps"],
                "Duration (sec)": record["time"],
                "Date": record["created_at"],
            }
            for record in records
        ]
    )
    st.dataframe(history, hide_index=True, width="stretch")


def main():


    st.set_page_config(
        page_icon="🏋️",
        page_title="AI Realtime GYM Trainer",
        initial_sidebar_state="expanded",
        layout="centered"
    )


    load_css(
        os.path.join(
            os.getcwd(),
            "static",
            "style.css"
        )
    )

    inject_local_font(
        os.path.join(
            os.getcwd(),
            "static",
            "AdobeClean.otf"
        ),
        "AdobeClean"
    )

   

    init_db()

   

    initial_session_defaults()

    if st.session_state.get("voice_pipeline_version") != VOICE_PIPELINE_VERSION:
        api_key = os.environ.get("GROQ_API_KEY", "")

        if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]

        if not api_key:
            st.session_state.voice_pipeline = None
            st.session_state.voice_error = (
                "Voice coaching is unavailable because GROQ_API_KEY is not configured."
            )
        else:
            try:
                groq_client = Groq(api_key=api_key)
                llm_coach = LLMCoach(groq_client)
                tts = TextToSpeech()
                st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
                st.session_state.voice_error = None
            except Exception:
                st.session_state.voice_pipeline = None
                st.session_state.voice_error = "Voice coaching could not be initialized."

        st.session_state.voice_pipeline_version = VOICE_PIPELINE_VERSION





    if not render_login_wall():
        return

   

    workout_started = st.session_state.get(
        "workout_started",
        False
    )

   

    with st.sidebar:

        st.title("🏋️ GymVision")

        if st.session_state.get("username"):

            st.caption(
                f"Logged in as: "
                f"{st.session_state.username}"
            )

        st.divider()

        st.subheader("Workout Plan")

      

        if not workout_started:

            plan_exercise=st.selectbox(
                "Exercise",
                options=EXERCISE_OPTIONS,
                key="plan_exercise"
            )

            plan_sets=st.number_input(
                "Sets",
                min_value=0,
                max_value=50,
                key="plan_sets",
                step=1
            )

            plan_reps=st.number_input(
                "Reps",
                min_value=0,
                max_value=50,
                key="plan_reps",
                step=1
            )

            st.markdown("")

            start_session_button = st.button(
                "Start Workout",
                width="stretch",
                key="start_session_button"
            )

            if start_session_button:
                st.session_state.exercise_type=plan_exercise
                st.session_state.target_sets=int(plan_sets)
                st.session_state.reps_per_set=int(plan_reps)
                

                st.session_state.workout_started = True

                # Reset workout counters
                st.session_state.reps = 0
                st.session_state.current_set_reps = 0
                st.session_state.sets_completed = 0
                st.session_state.workout_complete = False
                st.session_state.set_cycle_started_at=time.time()
                st.session_state.last_saved_sets_completed= 0
                st.session_state.last_mid_set_feedback_marker = None

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result
                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete=False

                st.rerun()


        else:

         
          
            exercise = st.session_state.get(
                "exercise_type",
                st.session_state.get("plan_exercise")
            )

            sets = st.session_state.get("target_sets", 0)
            reps = st.session_state.get("reps_per_set", 0)

            st.info(
                f"**{exercise}** — "
                f"{sets} Sets / {reps} Reps"
            )

            end_session_button = st.button(
                "End Workout",
                key="end_session_button",
                width="stretch"
            )

            if end_session_button:

                started_at = st.session_state.get(
                    "set_cycle_started_at",
                    time.time(),
                )
                add_exercise(
                    user_id=st.session_state["user_id"],
                    exercise_name=exercise,
                    reps=int(st.session_state.get("reps", 0)),
                    sets=int(st.session_state.get("sets_completed", 0)),
                    time=max(0, int(time.time() - started_at)),
                )

                st.session_state.workout_started= False
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        # =====================================================
        # PROGRESS
        # =====================================================

        if workout_started:

            st.divider()
            exercise=st.session_state.get("exercise_type")

            total_reps = st.session_state.get(
                "reps",
                0
            )

            current_set_reps = st.session_state.get(
                "current_set_reps",
                0
            )

            sets_completed = st.session_state.get(
                "sets_completed",
                0
            )

            reps_per_set = st.session_state.get("reps_per_set", 0)
            target_sets = st.session_state.get("target_sets", 0)

            st.subheader("Progress")

            st.metric(
                "Total Reps",
                total_reps
            )

            st.metric(
                "Current Set Reps",
                f"{current_set_reps}/{reps_per_set}"
            )

            st.metric(
                "Sets Completed",
                f"{sets_completed}/{target_sets}"
            )

            # =================================================
            # EXERCISE METRICS
            # =================================================

            st.divider()

            exercise = st.session_state.get(
                "exercise_type",
                st.session_state.get("plan_exercise")
            )

            if exercise == "Squats":

                st.subheader("Squat Metrics")

                st.metric(
                    "Knee Angle",
                    f"{st.session_state.get('knee_angle', 0)}°"
                )

                st.metric(
                    "Back Angle",
                    f"{st.session_state.get('back_angle', 0)}°"
                )

                st.metric(
                    "Depth Status",
                    st.session_state.get(
                        "depth_status",
                        "Unknown"
                    )
                )

            elif exercise == "Push-ups":

                st.subheader("Push-up Metrics")

                st.metric(
                    "Elbow Angle",
                    f"{st.session_state.get('elbow_angle', 0)}°"
                )

                st.metric(
                    "Body Alignment",
                    st.session_state.get(
                        "body_alignment",
                        "Unknown"
                    )
                )

                st.metric(
                    "Hip Position",
                    st.session_state.get(
                        "hip_status",
                        "Unknown"
                    )
                )

            elif exercise == "Biceps Curls (Dumbbell)":

                st.subheader("Curl Metrics")

                st.metric(
                    "Elbow Angle",
                    f"{st.session_state.get('elbow_angle', 0)}°"
                )

                st.metric(
                    "Shoulder Stability",
                    st.session_state.get(
                        "shoulder_status",
                        "Unknown"
                    )
                )

                st.metric(
                    "Swing Detection",
                    st.session_state.get(
                        "swing_status",
                        "Unknown"
                    )
                )

            elif exercise == "Shoulder Press":

                st.subheader("Shoulder Press Metrics")

                st.metric(
                    "Elbow Angle",
                    f"{st.session_state.get('elbow_angle', 0)}°"
                )

                st.metric(
                    "Arm Extension",
                    st.session_state.get(
                        "extension_status",
                        "Unknown"
                    )
                )

                st.metric(
                    "Back Arch",
                    st.session_state.get(
                        "back_arch_status",
                        "Unknown"
                    )
                )

            elif exercise == "Lunges":

                st.subheader("Lunge Metrics")

                st.metric(
                    "Front Knee Angle",
                    f"{st.session_state.get('front_knee_angle', 0)}°"
                )

                st.metric(
                    "Torso Angle",
                    f"{st.session_state.get('torso_angle', 0)}°"
                )

                st.metric(
                    "Balance Status",
                    st.session_state.get(
                        "balance_status",
                        "Unknown"
                    )
                )

    
    st.title("GYM-VISION")

    st.markdown(
        "### Real-time pose detection with proactive AI voice coaching"
    )

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    voice_pipeline = st.session_state.get("voice_pipeline")
    voice_error = st.session_state.get("voice_error")
    if voice_pipeline and voice_pipeline.last_error:
        voice_error = voice_pipeline.last_error

    if voice_error:
        st.warning(f"🔇 {voice_error}")

   

    if not workout_started:

        st.markdown(
            textwrap.dedent("""
                <div style="
                    border: 10px dashed #444;
                    border-radius: 0px;
                    padding: 48px 32px;
                    text-align: center;
                    color: #888;
                    margin-top: 32px;
                    margin-bottom: 32px;
                ">
                    <h2 style="color:#ccc; margin-bottom:8px;">
                        👈 Set your workout plan
                    </h2>
                    <p style="font-size:1.05rem;">
                        Choose your exercise, sets and reps in the sidebar,<br>
                        then click <strong>Start Workout</strong> to activate the camera and AI coach.
                    </p>
                </div>
            """).strip(),
            unsafe_allow_html=True
        )

    

    else:

        ice_servers = [
            {
                "urls": [
                    "stun:stun.l.google.com:19302",
                    "stun:stun1.google.com:19302",
                    "stun:stun2.google.com:19302",
                ]
            }
        ]

        # Add custom TURN server ONLY if valid credentials exist in env/secrets
        turn_server = os.getenv("TURN_SERVER") or (st.secrets.get("TURN_SERVER", "") if hasattr(st, "secrets") else "")
        turn_username = os.getenv("TURN_USERNAME") or (st.secrets.get("TURN_USERNAME", "") if hasattr(st, "secrets") else "")
        turn_credential = os.getenv("TURN_CREDENTIAL") or (st.secrets.get("TURN_CREDENTIAL", "") if hasattr(st, "secrets") else "")

        if turn_server and turn_username and turn_credential:
            ice_servers.append({
                "urls": [turn_server],
                "username": turn_username,
                "credential": turn_credential,
            })

        context = webrtc_streamer(
            key="exercise-analysis",

            mode=WebRtcMode.SENDRECV,

            video_processor_factory=VideoProcessorClass,

            rtc_configuration={
                "iceServers": ice_servers
            },

            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480},
                },
                "audio": False
            },

            async_processing=True
        )
       
        if context.video_processor:
            context.video_processor.set_exercise(
                st.session_state.get("exercise_type", "Squats")
            )
            sync_metrics_update(context)
            time.sleep(0.5)
            st.rerun()

        inject_webrtc_styles()
    st.divider()
    render_workout_history()


if __name__ == "__main__":
    main()
