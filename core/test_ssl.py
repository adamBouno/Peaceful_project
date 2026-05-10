import requests
r = requests.get("https://api.djelia.cloud/v2/translate/", verify=False)
print(r.status_code, r.text)