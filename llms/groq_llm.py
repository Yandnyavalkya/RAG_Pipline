
from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE


class GroqLLM:

    def __init__(self):

        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is missing. Check your .env file."
            )

        if not LLM_MODEL:
            raise ValueError(
                "LLM_MODEL is missing. Set your working Groq model in .env."
            )

        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = LLM_MODEL

    def generate(self, system_prompt, user_prompt):

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content

        if not answer:
            raise RuntimeError("Groq returned an empty response.")

        return answer.strip()
