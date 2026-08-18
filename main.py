import streamlit as st
import os
import textwrap

from streamlit_webrtc import ( webrtc_streamer,WebRtcMode)

from services.auth.login_wall import render_login_wall
from services.state.session_default import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import (load_css,inject_local_font,inject_webrtc_styles)
from services.persistence.exercise_repository import init_db
from services.vision.exercise_video_processor import VideoProcessorClass
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

            st.selectbox(
                "Exercise",
                options=EXERCISE_OPTIONS,
                key="plan_exercise"
            )

            st.number_input(
                "Sets",
                min_value=0,
                max_value=50,
                key="plan_sets",
                step=1
            )

            st.number_input(
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

                st.session_state[
                    "workout_started"
                ] = True

                # Reset workout counters
                st.session_state["reps"] = 0
                st.session_state["current_set_reps"] = 0
                st.session_state["sets_completed"] = 0

                st.rerun()


        else:

            exercise = st.session_state.get(
                "plan_exercise"
            )

            sets = st.session_state.get(
                "plan_sets"
            )

            reps = st.session_state.get(
                "plan_reps"
            )

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

                st.session_state[
                    "workout_started"
                ] = False

                st.rerun()

        # =====================================================
        # PROGRESS
        # =====================================================

        if workout_started:

            st.divider()

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

            reps_per_set = st.session_state.get(
                "plan_reps",
                0
            )

            target_sets = st.session_state.get(
                "plan_sets",
                0
            )

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
                "plan_exercise"
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

        context = webrtc_streamer(
            key="exercise-analysis",

            mode=WebRtcMode.SENDRECV,

            video_processor_factory=VideoProcessorClass,

            rtc_configuration={
                "iceServers": [
                    {
                        "urls": [
                            "stun:stun1.google.com:19302"
                        ]
                    }
                ]
            },

            media_stream_constraints={
                "video": True,
                "audio": False
            },

            async_processing=True
        )

        inject_webrtc_styles()

       
        if context.video_processor:

            selected_exercise = st.session_state.get(
                "plan_exercise",
                "Squats"
            )

            context.video_processor.set_exercise(
                selected_exercise
            )

          

            metrics = (
                context.video_processor
                .get_latest_metrics()
            )

            if metrics:

                # Store metrics in Streamlit session state
                for key, value in metrics.items():

                    st.session_state[key] = value


        st.markdown("### Workout History")




if __name__ == "__main__":
    main()