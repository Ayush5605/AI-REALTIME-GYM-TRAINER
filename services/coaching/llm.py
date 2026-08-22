import os

from services.config.workout_config import PROMPT


# This is a fast, current Groq production model. It can be overridden without
# editing code by setting GROQ_MODEL in .env or Streamlit secrets.
DEFAULT_MODEL = "openai/gpt-oss-20b"

class LLMCoach:
    def __init__(self,groq_client):
        self.client=groq_client
        self.history=[]
        self.system_prompt=PROMPT
        self.model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

    def give_feedback(self, event, exercise, metrics, issue):

        prompt = f"Event: {event}\nExercise: {exercise}"

        if issue:
            prompt += f"\nForm issue: {issue}"

        if metrics:
            metric_summary = ", ".join(
                f"{name.replace('_', ' ')}: {value}"
                for name, value in metrics.items()
                if name != "reps"
            )
            if metric_summary:
                prompt += f"\nCurrent metrics: {metric_summary}"

        messages=[
            {
                "role":"system","content":self.system_prompt
            },
            *self.history[-10:],
            {
                "role":"user",
                "content":prompt
            }
        ]


        response=self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
            max_tokens=120,
        )

        text=response.choices[0].message.content.strip()

        self.history.append({
            "role":"assistant",
            "content":text
            })
        return text
