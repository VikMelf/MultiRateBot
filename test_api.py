# test_api.py — швидка перевірка API exchangerate.host
import requests, json

def test():
    url = "https://api.exchangerate.host/convert"
    params = {"from": "USD", "to": "EUR", "amount": 1}
    print("Request URL:", requests.Request('GET', url, params=params).prepare().url)
    try:
        r = requests.get(url, params=params, timeout=8)
        print("HTTP status:", r.status_code)
        data = r.json()
        print("JSON response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Exception while requesting:", repr(e))

if __name__ == "__main__":
    test()
