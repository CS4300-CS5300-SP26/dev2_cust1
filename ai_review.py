import os
import sys
 
import openai
from openai import OpenAI
 
# ── Validate API key before doing anything ────────────────────────────────────
 
api_key = os.getenv("OPENAI_API_KEY", "").strip()
 
if not api_key:
    print("ERROR: OPENAI_API_KEY environment variable is not set.")
    print("Go to your GitHub repo → Settings → Secrets and variables → Actions")
    print("and add a secret named OPENAI_API_KEY with your key from platform.openai.com")
    feedback = "## AI Code Review Feedback\n***Configuration Error***\n`OPENAI_API_KEY` secret is missing. No AI review available."
    with open("feedback.md", "w") as file:
        file.write(feedback)
    sys.exit(0)
 
# ── Read diff ─────────────────────────────────────────────────────────────────
 
try:
    with open("diff.txt", "r") as file:
        diff = file.read().strip()
except FileNotFoundError:
    print("ERROR: diff.txt not found.")
    sys.exit(1)
 
if not diff:
    print("No changes detected in diff — skipping AI review.")
    with open("feedback.md", "w") as file:
        file.write("## AI Code Review Feedback\nNo file changes detected in this PR.")
    sys.exit(0)
 
# ── Query OpenAI Responses API ────────────────────────────────────────────────
 
client = OpenAI(api_key=api_key)
 
try:
    response = client.responses.create(
        model="gpt-5.1-codex-mini",
        instructions=(
            "You are an expert software engineer performing a code review "
            "on a Django project. Provide concise, actionable feedback."
        ),
        input=(
            "Provide concise, actionable feedback in Markdown format, "
            "paying special attention to Django convention, security, and "
            "code efficiency, and in each case mentioning the file name "
            "and line number for the suggestion. "
            f"Here's the pull request diff:\n{diff}"
        ),
    )
    feedback = response.output_text
    print("Review generated successfully.")
 
except openai.AuthenticationError:
    print("ERROR: Invalid OpenAI API key.")
    print("Check that your OPENAI_API_KEY secret is correct at platform.openai.com/api-keys")
    feedback = "***Authentication Error***\nThe OpenAI API key is invalid. No AI review available."
 
except openai.RateLimitError:
    print("ERROR: OpenAI quota exceeded.")
    feedback = "***Quota Exceeded***\nOpenAI rate limit reached. No AI review available."
 
except openai.APIConnectionError as e:
    print(f"ERROR: Could not connect to OpenAI API: {e}")
    feedback = "***Connection Error***\nCould not reach the OpenAI API. No AI review available."
 
except openai.OpenAIError as e:
    print(f"ERROR: Unexpected OpenAI error: {e}")
    feedback = f"***OpenAI Error***\n`{e}`\nNo AI review available."
 
# ── Strip code fences if the model wrapped its response in them ───────────────
 
if feedback.startswith("```markdown"):
    feedback = feedback[len("```markdown"):]
elif feedback.startswith("```"):
    feedback = feedback[len("```"):]
 
feedback_stripped = feedback.rstrip()
if feedback_stripped.endswith("```"):
    feedback = feedback_stripped[:-3]
 
# ── Write feedback file ───────────────────────────────────────────────────────
 
with open("feedback.md", "w") as file:
    file.write(f"## AI Code Review Feedback\n{feedback}")
 
print("feedback.md written successfully.")