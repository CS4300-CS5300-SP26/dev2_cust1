import os
 
import openai
from openai import OpenAI
 
# ── Read diff ─────────────────────────────────────────────────────────────────
 
with open("diff.txt", "r") as file:
    diff = file.read()
 
# ── Query ChatGPT ─────────────────────────────────────────────────────────────
 
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)
 
try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert software engineer performing a code review "
                    "on a Django project. Provide concise, actionable feedback."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Provide concise, actionable feedback in Markdown format, "
                    "paying special attention to Django convention, security, and "
                    "code efficiency, and in each case mentioning the file name "
                    "and line number for the suggestion. "
                    f"Here's the pull request diff:\n{diff}"
                ),
            },
        ],
        model="gpt-5.1-codex-mini",
    )
    feedback = chat_completion.choices[0].message.content
    print(feedback)
 
except openai.RateLimitError:
    print("Quota Exceeded")
    feedback = "***Quota Exceeded***\nNo AI review available."
 
# ── Strip code fences if the model wrapped its response in them ───────────────
 
if feedback.startswith("```markdown"):
    feedback = feedback[len("```markdown"):]
elif feedback.startswith("```"):
    feedback = feedback[len("```"):]
 
feedback_stripped = feedback.rstrip()
if feedback_stripped.endswith("```"):
    feedback = feedback[: len(feedback_stripped) - 3]
 
# ── Write feedback file ───────────────────────────────────────────────────────
 
with open("feedback.md", "w") as file:
    file.write(f"## AI Code Review Feedback\n{feedback}")