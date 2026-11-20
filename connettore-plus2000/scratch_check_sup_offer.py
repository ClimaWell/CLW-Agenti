import requests
import json

url = "https://fadgdncfhfpwkcbxcntc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhZGdkbmNmaGZwd2tieGNudGMiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc2MDAxMjMxNCwiZXhwIjoyMDc1NTg4MzE0fQ.u11iLpA9b8214G0bXj_qFq_fCq20c4zS4L-wR6u0gno"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Accept": "application/json"
}

resp = requests.get(f"{url}/rest/v1/documents?number=eq.OFF-1136-20261014-092524", headers=headers)
print("DOC:")
print(json.dumps(resp.json(), indent=2))

resp_lines = requests.get(f"{url}/rest/v1/document_lines?document_number=eq.OFF-1136-20261014-092524", headers=headers)
print("\nLINES:")
print(json.dumps(resp_lines.json(), indent=2))
