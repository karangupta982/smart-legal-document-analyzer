from groq import Groq
import os

class GroqService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.client = Groq(api_key=self.api_key)

        self.system_prompt = """You are a legal document assistant. Answer only from provided text. If answer is not found, say 'Not found in document'. Always provide:

1. Direct Answer
2. Simple Explanation
3. Source snippet"""

    def ask_question(self, context: str, question: str) -> str:
        """
        Send question with context to Groq LLM and return response.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Document context: {context}"},
            {"role": "assistant", "content": "Understood. I will answer based only on the provided document context."},
            {"role": "user", "content": question}
        ]

        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",  # Using LLaMA model as specified
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")