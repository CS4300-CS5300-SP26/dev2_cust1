 import os
   import time
   from openai import OpenAI, RateLimitError
   
   client = OpenAI(
       api_key=os.getenv("OPENAI_API_KEY"),
       timeout=60.0,  # Add timeout
   )
   
   with open("diff.txt", "r") as f:
       diff = f.read()
   
   max_retries = 3
   retry_count = 0
   
   while retry_count < max_retries:
       try:
           chat_completion = client.chat.completions.create(
               messages=[
                   {"role": "system", "content": "You are an expert software engineer performing a code review on a Django project."},
                   {"role": "user", "content": f"Provide concise feedback paying special attention to Django convention, security, and code efficiency, and in each case 
  mentioning the file name and line number for the suggestion. Here's the pull request diff:\n{diff}"}
               ],
               model="gpt-4o"
           )
           review = chat_completion.choices[0].message.content
           break
       except RateLimitError:
           review = "AI review failed: Rate limit reached."
           break
       except Exception as e:
           retry_count += 1
           if retry_count >= max_retries:
               review = f"AI review failed with error:\n{repr(e)}"
           else:
               print(f"Connection error, retrying... ({retry_count}/{max_retries})")
               time.sleep(5)
   
   with open("review.txt", "w") as f:
       f.write(review)

