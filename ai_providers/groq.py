import json
from groq import Groq

def call_groq(input: str, is_json_response: bool = False):
    client = Groq()
    if is_json_response:
        input += ' Remember your answer must be in valid JSON format'

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[
          {
            "role": "user",
            "content": input
          }
        ],
        temperature=0.3,
        max_completion_tokens=2000,
        top_p=1,
        stop=None,
        stream=False
    )

    response = completion.choices[0].message.content
    if is_json_response:
        response = response.replace('```', '')
        return json.loads(response)

    print('Calling Groq....')
    return response
