import os
from openai import OpenAI RateLimitError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("diff.txt", "r") as f:
    diff = f.read()

prompt = f"""
You are a senior software engineer reviewing a pull request for a Django project.
Analyze the following code diff and provide feedback about:
- Bugs
- Security issues
- Performance improvements
- Code style

Diff:
{diff}
"""

try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    review_text = response.output_text

except RateLimitError:
    print("Rate limit reached. Waiting 20 seconds before retrying...")
    time.sleep(20)

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        review_text = response.output_text

    except Exception as e:
        review_text = f"AI review failed after retry: {str(e)}"

except Exception as e:
    review_text = f"AI review failed: {str(e)}"


# Write output for GitHub comment
with open("review.txt", "w") as f:
    f.write(review_text)
