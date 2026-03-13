import os
import time
from openai import OpenAI, RateLimitError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("diff.txt", "r") as f:
    diff = f.read()

prompt = f"Review this code diff:\n{diff}"

try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    review = response.output_text

except RateLimitError:
    review = "AI review failed: Rate limit reached."

except Exception as e:
    review = f"AI review failed with error:\n{repr(e)}"

with open("review.txt", "w") as f:
    f.write(review)

