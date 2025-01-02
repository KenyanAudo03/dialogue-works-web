import http.client
import json

conn = http.client.HTTPSConnection("qdqe8q.api.infobip.com")
payload = json.dumps({
    "messages": [
        {
            "destinations": [{"to":"254703853259"}],
            "from": "Dialogue Works",
            "text": "Congratulations on sending your first message. Your OTP is 4565."
        }
    ]
})
headers = {
    'Authorization': 'App b4da9464100fee4d4999bf9bf10c9276-d32c243e-e1b2-4d73-9978-807d7ce24c2e',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
conn.request("POST", "/sms/2/text/advanced", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))