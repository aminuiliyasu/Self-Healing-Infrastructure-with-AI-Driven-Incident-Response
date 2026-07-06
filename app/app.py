"""Small demo web service instrumented with Prometheus metrics.

It exposes a couple of extra endpoints (/error, /slow) plus an ERROR_MODE
switch so we can inject failures on purpose and watch the engine react.
"""

import os
import random
import time

from flask import Flask, Response, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "status"],
)


def error_mode_on() -> bool:
    return os.environ.get("ERROR_MODE", "0") == "1"


@app.route("/")
def home():
    # With ERROR_MODE=1 roughly half of the normal traffic fails, which is
    # enough to push the error rate over the engine's threshold.
    if error_mode_on() and random.random() < 0.5:
        return "simulated failure (ERROR_MODE=1)", 500
    return render_template("index.html", error_mode=error_mode_on())


@app.route("/health")
def health():
    return "OK", 200


@app.route("/error")
def error():
    return "intentional error for testing", 500


@app.route("/slow")
def slow():
    time.sleep(1)
    return "slow response (1s)", 200


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.before_request
def before_request():
    request.start_time = time.time()


@app.after_request
def after_request(response):
    latency = time.time() - request.start_time
    endpoint = request.path
    method = request.method
    status = str(response.status_code)
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    if response.status_code >= 400:
        ERROR_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
