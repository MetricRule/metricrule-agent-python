from flask import Flask, request
from metricrule.agent import WSGIMetricsMiddleware 
app = Flask('MetricRuleDemoApp')

app.wsgi_app = WSGIMetricsMiddleware(app.wsgi_app)

@app.route('/predict', methods=['POST'])
def predict():
    return '{"status": "ok"}'

if __name__ == "__main__":
    app.run('127.0.0.1', '8551', debug=True)