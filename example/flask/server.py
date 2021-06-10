import argparse

from flask import Flask
from metricrule.agent import WSGIMetricsMiddleware, WSGIApplication
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask('MetricRuleDemoApp')


@app.route('/predict', methods=['POST'])
def predict():
    return '{"predictions": [[0.495]]}'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('agent_config_path',
                        help='Absolute path to textproto config file for MetricRule agent')
    args = parser.parse_args()

    app.wsgi_app = WSGIMetricsMiddleware(app.wsgi_app, args.agent_config_path)
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': WSGIApplication.make()
    })
    app.run('127.0.0.1', '9001', debug=True)
