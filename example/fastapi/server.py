from fastapi import FastAPI

import argparse
import uvicorn

from metricrule.agent import ASGIMetricsMiddleware, ASGIApplication

app = FastAPI()
v1 = FastAPI()
app.mount('/metrics', ASGIApplication.make())
app.mount('/v1', v1)

@v1.post('/predict')
async def predict():
    return {'predictions': [[0.495]]}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('agent_config_path',
                        help='Absolute path to textproto config file for MetricRule agent')
    args = parser.parse_args()
    
    v1.add_middleware(ASGIMetricsMiddleware, config_path=args.agent_config_path)

    uvicorn.run(app, host="0.0.0.0", port=9001)





