import argparse

from flask import Flask
from metricrule.agent import WSGIMetricsMiddleware 

app = Flask('MetricRuleDemoApp')

@app.route('/predict', methods=['POST'])
def predict():
    return '{"status": "ok"}'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('agent_config_path', 
        help='Absolute path to textproto config file for MetricRule agent')
    args = parser.parse_args()

    app.wsgi_app = WSGIMetricsMiddleware(app.wsgi_app, args.agent_config_path)
    app.run('127.0.0.1', '8551', debug=True)