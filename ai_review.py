import os
import sys
from openai import OpenAI, RateLimitError

# Debug: Check API key
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: API Key present: {bool(api_key)}", file=sys.stderr)
print(f"DEBUG: API Key starts with: {api_key[:20] if api_key else 'None'}...", file=sys.stderr)

if not api_key:
    print("ERROR: OPENAI_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)

try:
    print("DEBUG: Initializing OpenAI client...", file=sys.stderr)
    client = OpenAI(api_key=api_key)
    print("DEBUG: Client initialized successfully", file=sys.stderr)
except Exception as e:
    print(f"ERROR initializing client: {repr(e)}", file=sys.stderr)
    sys.exit(1)

# Check if diff.txt exists
if not os.path.exists("diff.txt"):
    print("WARNING: diff.txt not found", file=sys.stderr)
    diff = "No diff provided"
else:
    with open("diff.txt", "r") as f:
        diff = f.read()
    print(f"DEBUG: Read {len(diff)} bytes from diff.txt", file=sys.stderr)

try:
    print("DEBUG: Calling OpenAI API...", file=sys.stderr)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert software engineer performing a code review on a Django project."},
            {"role": "user", "content": f"Provide concise feedback paying special attention to Django convention, security, and code efficiency, and in each case mentioning the file name and line number for the suggestion. Here's the pull request diff:\n{diff}"}
        ],
        model="gpt-4o"
    )
    print("DEBUG: API call successful", file=sys.stderr)
    review = chat_completion.choices[0].message.content
except RateLimitError as e:
    review = "AI review failed: Rate limit reached."
    print(f"ERROR: Rate limit - {repr(e)}", file=sys.stderr)
except Exception as e:
    review = f"AI review failed with error:\n{repr(e)}"
    print(f"ERROR: {repr(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

with open("review.txt", "w") as f:
    f.write(review)
print("DEBUG: Review written to review.txt", file=sys.stderr)
