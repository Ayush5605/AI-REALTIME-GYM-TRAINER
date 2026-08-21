from services.config.workout_config import PROMPT

class LLMCoach:
    def __init__(self,groq_client):
        self.client=groq_client
        self.hitory=[]
        self.system_prompt=PROMPT

    def give_feedback(self,event,issue):