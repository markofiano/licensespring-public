import socket, time, json, requests, os, base64, threading
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from flask import Response

ETCD_HOST = 'etcd-0.etcd-cluster-headless'
ETCD_PORT = 2379

app = Flask(__name__)
metrics = PrometheusMetrics(app)
SERVICE_ID = socket.gethostname()
SERVICE_HOST = os.environ.get("SERVICE_HOST", socket.gethostbyname(socket.gethostname()))
SERVICE_PORT = 5000

def base64_encode(s): return base64.b64encode(s.encode()).decode()

def register_to_etcd():
    url = f"http://{ETCD_HOST}:{ETCD_PORT}/v3/kv/put"
    metadata = {"ip": SERVICE_HOST, "port": SERVICE_PORT, "timestamp": int(time.time())}
    data = {"key": base64_encode(f"ping/{SERVICE_ID}"), "value": base64_encode(json.dumps(metadata))}
    try:
        requests.post(url, json=data, timeout=3)
    except Exception as e:
        print(f"Failed to register: {e}")

def periodic_register():
    while True:
        register_to_etcd()
        time.sleep(30)

@app.route('/ping')
def ping():
    start = time.time()
    response = {"msg": f"pong from {SERVICE_HOST} in {int((time.time() - start) * 1000)}ms"}
    return jsonify(response)

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    threading.Thread(target=periodic_register, daemon=True).start()
    register_to_etcd()
    app.run(host='0.0.0.0', port=SERVICE_PORT)
