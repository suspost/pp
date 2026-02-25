# json.py
# JSON examples

import json

# Python dictionary
person = {
    "name": "Alice",
    "age": 20,
    "city": "Almaty"
}

# Convert Python to JSON string
json_string = json.dumps(person)
print("JSON String:", json_string)

# Convert JSON string back to Python
python_data = json.loads(json_string)
print("Python Data:", python_data)

# Write JSON to file
with open("sample-data.json", "w") as f:
    json.dump(person, f)

# Read JSON from file
with open("sample-data.json", "r") as f:
    data = json.load(f)
    print("Read from file:", data)
