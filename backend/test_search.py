import requests

response = requests.post(
    "http://127.0.0.1:8000/api/v1/documents/search",
    json={"query": "what is binary search"}
)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())