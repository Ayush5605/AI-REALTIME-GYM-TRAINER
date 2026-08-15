import streamlit as st

from services.auth.login_wall import render_login_wall
from services.state.session_default import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS


def main():

    st.set_page_config(
        page_icon="🏋️",
        page_title="AI Realtime GYM Trainer",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    # Initialize session state
    initial_session_defaults()

    # Login wall
    if not render_login_wall():
        return

    workout_started = st.session_state.get("workout_started", False)

    with st.sidebar:

        st.title("🏋️ GymVision")

        if st.session_state.get("username"):
            st.caption(
                f"Logged in as: {st.session_state.username}"
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
                "Start Session",
                width="stretch",
                key="start_session_button"
            )

            if start_session_button:

                st.session_state["workout_started"] = True

                st.rerun()

        else:

            exercise = st.session_state.get("plan_exercise")
            sets = st.session_state.get("plan_sets")
            reps = st.session_state.get("plan_reps")

            st.info(
                f"**{exercise}** — {sets} Sets / {reps} Reps"
            )

            end_session_button = st.button(
                "End Session",
                key="end_session_button",
                width="stretch"
            )

            if end_session_button:

                st.session_state["workout_started"] = False

                st.rerun()

        # Progress
        if workout_started:

            st.divider()

            total_reps = st.session_state.get("reps", 0)
            current_set_reps = st.session_state.get(
                "current_set_reps", 0
            )
            sets_completed = st.session_state.get(
                "sets_completed", 0
            )

            reps_per_set = st.session_state.get(
                "plan_reps", 0
            )

            target_sets = st.session_state.get(
                "plan_sets", 0
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

            st.divider()

           


if __name__ == "__main__":
    main()