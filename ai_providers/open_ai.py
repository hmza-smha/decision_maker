import json
from openai import OpenAI

def call_openai(input: str, is_json_response: bool = False):
    client = OpenAI()

    if is_json_response:
        input += ' Remember your answer must be in valid JSON format'
        
    response = client.responses.create(
        model="gpt-4.1",
        input=input
    )

    if is_json_response:
        response = response.output_text.replace('```', '')
        return json.loads(response)
    
    return response.output_text    