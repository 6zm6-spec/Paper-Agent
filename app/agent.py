from openai import OpenAI


class Agent:
    def __init__(self, name: str, system_prompt: str, client: OpenAI, model: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = client
        self.model = model

    def run(self, user_input: str) -> str:
        print(f"--- {self.name} 正在运行... ---")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content.strip()