import openai
from openai import OpenAI
import os

# Read diff
with open("diff.txt", "r") as file:
    diff = file.read()

# Query ChatGPT
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

try:
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert software engineer performing a code review on a Django project. Provide concise, actionable feedback."},
            {"role": "user", "content": f"Provide concise, actionable feedback in Markdown format, paying special attention to Django convention, security, and code efficiency, and in each case mentioning the file name and line number for the suggestion. Here's the pull request diff:\n{diff}"}
        ],
        model="gpt-4o"
    )

    feedback = chat_completion.choices[0].message.content
    print(feedback)

except openai.RateLimitError:
    print("Quota Exceeded")
    feedback = "***Quota Exceeded***\nNo AI review available."

# Remove the leading code fence if present
if feedback.startswith("```markdown"):
    feedback = feedback[len("```markdown"):]
elif feedback.startswith("```"):
    feedback = feedback[len("```"):]

# Remove the trailing code fence if present
feedback_stripped = feedback.rstrip()
if feedback_stripped.endswith("```"):
    feedback = feedback[:len(feedback) - 3]


with open("feedback.md", "w") as file:
    file.write(f"## AI Code Review Feedback\n{feedback}")
