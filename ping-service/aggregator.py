import base64, json, requests

ETCD_HOST = 'etcd-0.etcd-cluster-headless'
ETCD_PORT = 2379

def base64_encode(s): return base64.b64encode(s.encode()).decode()
def base64_decode(s): return base64.b64decode(s).decode()

def fetch_services():
    url = f"http://{ETCD_HOST}:{ETCD_PORT}/v3/kv/range"
    data = {"key": base64_encode("ping/"), "range_end": base64_encode("ping0")}
    try:
        resp = requests.post(url, json=data, timeout=3)
        return [json.loads(base64_decode(i["value"])) for i in resp.json().get("kvs", [])]
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

def ping_services(services):
    for s in services:
        try:
            r = requests.get(f"http://{s['ip']}:{s['port']}/ping", timeout=2)
            print(r.json())
        except Exception as e:
            print(f"Failed to ping {s['ip']}:{s['port']} -> {e}")

if __name__ == "__main__":
    ping_services(fetch_services())
