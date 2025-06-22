import os
import json
from groq import Groq
from pydantic import BaseModel, Field

# Initialize Groq client
client_writing = Groq(api_key="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")

# Load question from JSON file
with open("static/datasets/writing.json", "r") as file:
    data = json.load(file)
    question = data["writing_comprehension"][0]["tasks"][0]

# Load system prompt
try:
    with open("prompt\writing.txt", "r") as file:
        system_prompt = file.read()
except FileNotFoundError:
    print("Error: File 'prompt/writing.txt' not found.")
    exit()

# Sample answer
sample_answer = """The lecture and the reading passage present contrasting views on the viability of hydrogen cars as a replacement for fossil fuel vehicles. The reading argues that hydrogen cars are a promising solution because they emit only water, thus reducing air pollution, utilize abundant hydrogen that can be produced renewably, and offer longer ranges than electric vehicles (EVs). However, it also acknowledges challenges, such as high energy demands for hydrogen production, limited fueling stations, and safety risks due to hydrogen’s flammability.

In contrast, the lecture disputes the reading’s optimistic view by emphasizing the impracticality of hydrogen cars. It asserts that hydrogen production is currently inefficient and relies heavily on fossil fuels, undermining the environmental benefits claimed in the reading. The lecture also highlights that the scarcity of fueling stations—fewer than 100 in the U.S., as noted in the reading—is a more significant barrier than the reading suggests, as building new stations is prohibitively costly and slow. Additionally, the lecture argues that the safety risks of hydrogen’s flammability are far greater than those of EVs, contradicting the reading’s implication that these risks are manageable. Finally, the lecture points out that EVs are already more practical and widely adopted, with better infrastructure and improving range, challenging the reading’s claim of hydrogen cars’ superiority in range.

In summary, while the reading presents hydrogen cars as a viable alternative with some hurdles, the lecture strongly opposes this by highlighting inefficiencies in production, inadequate infrastructure, significant safety concerns, and the comparative advantages of EVs, suggesting that hydrogen cars are not a practical solution at present."""


# Create user prompt
prompt = f"""
Task type: {question["task_type"]}
 
Question (Reading Passage): {question["reading_passage"]}

Instructions: {question["prompt"]}

Answer to Evaluate: {sample_answer}
"""

# Request structured JSON response from the model
writing_completion = client_writing.chat.completions.create(
    model="llama-3.3-70b-versatile",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ],
    temperature=0.0,  # Lower temperature for stricter adherence to JSON format
    max_tokens=200
)

# Extract and validate response
nilai_writing = writing_completion.choices[0].message.content
print(nilai_writing)