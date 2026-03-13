 import os
   import time
   from openai import OpenAI, RateLimitError
   
   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   
   with open("diff.txt", "r") as f:
       diff = f.read()
   
   try:
       chat_completion = client.chat.completions.create(
           messages=[
               {"role": "system", "content": "You are an expert software engineer performing a code review on a Django project."},
               {"role": "user", "content": f"Provide concise feedback paying special attention to Django convention, security, and code efficiency, and in each case mentioning 
  the file name and line number for the suggestion. Here's the pull request diff:\n{diff}"}
           ],
           model="gpt-4o"
       )
       review = chat_completion.choices[0].message.content
   except RateLimitError:
       review = "AI review failed: Rate limit reached."
   except Exception as e:
       review = f"AI review failed with error:\n{repr(e)}"
   
   with open("review.txt", "w") as f:
       f.write(review)

