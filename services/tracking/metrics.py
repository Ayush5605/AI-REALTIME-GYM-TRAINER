import streamlit as st
from services.config.workout_config import METRICS_FIELDS

def sync_metrics_update(context):
    if not context or not hasattr(context,"state") or not context.state.playing:
        return

    processor=getattr(context,"video_processor",None)

    if not processor:
        return
    exercise=st.session_state.get("exercise_type")

    if not exercise:
        return

    processor.set_exercise(exercise)
    latest_metrics=processor.get_latest_metrics()

    if not latest_metrics:
        return


    reps=latest_metrics.get("reps")
    st.session_state.reps=reps

    # `METRICS_FIELDS` is keyed by the selected exercise name, not by the
    # literal string "exercise".  Using the literal meant this was always
    # `None`, so the function returned before copying any live metrics.
    fields = METRICS_FIELDS.get(exercise)

    if not fields:
        return

    for key,default in fields.items():
        st.session_state[key]=latest_metrics.get(key,default)
