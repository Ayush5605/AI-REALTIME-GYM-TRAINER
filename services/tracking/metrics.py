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


    # Each detector supplies a cumulative live rep count. Derive the set
    # progress from that count instead of leaving the sidebar values at their
    # session defaults.
    reps = max(0, int(latest_metrics.get("reps", 0) or 0))
    reps_per_set = max(0, int(st.session_state.get("reps_per_set", 0) or 0))
    target_sets = max(0, int(st.session_state.get("target_sets", 0) or 0))

    st.session_state.reps = reps

    if reps_per_set:
        st.session_state.current_set_reps = reps % reps_per_set
        st.session_state.sets_completed = min(
            reps // reps_per_set,
            target_sets,
        )
        st.session_state.workout_complete = (
            target_sets > 0
            and reps >= reps_per_set * target_sets
        )
    else:
        st.session_state.current_set_reps = 0
        st.session_state.sets_completed = 0
        st.session_state.workout_complete = False

    fields = METRICS_FIELDS.get(exercise)

    if not fields:
        return

    for key,default in fields.items():
        st.session_state[key]=latest_metrics.get(key,default)
