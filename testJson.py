from config import Config
import json
completion = Config.client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "Return a JSON object with task_achievement, coherence, vocabulary, grammar."},
        {"role": "user", "content": "Test"}
    ],
    temperature=0.0,
    max_tokens=200
)
print(json.loads(completion.choices[0].message.content))