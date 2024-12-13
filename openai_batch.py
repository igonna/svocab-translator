from openai import OpenAI
client = OpenAI()
 
num_stories = 10
prompts = ["Once upon a time,"] * num_stories
 
try:
    # batched example, with 10 story completions per request
    response = client.batches.create(
        model="gpt-4o-mini",
        prompt=prompts,
        max_tokens=20,
    )
    
    # match completions to prompts by index
    stories = [""] * len(prompts)
    for choice in response.choices:
        stories[choice.index] = prompts[choice.index] + choice.text
    
    # print stories
    for story in stories:
        print(story)
except Exception as e:
    print(e)