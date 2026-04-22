from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Debug Operator", version="1.0.0")


@app.post("/sync")
async def sync(request: Request):
    body = await request.json()
    parent = body.get("object", {})

    pod_name = parent.get("metadata", {}).get("name", "")
    pod_namespace = parent.get("metadata", {}).get("namespace", "default")
    annotations = parent.get("metadata", {}).get("annotations", {})
    labels = parent.get("metadata", {}).get("labels", {})

    desired = []

    if annotations.get("debug") == "true":
        # Ищем первый containerPort
        containers = parent.get("spec", {}).get("containers", [])
        port = 80
        for c in containers:
            ports = c.get("ports", [])
            if ports:
                port = ports[0].get("containerPort", 80)
                break

        desired.append({
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"debug-{pod_name}",
                "namespace": pod_namespace,
                "labels": {
                    "created-by": "debug-operator",
                    "debug-pod": pod_name
                }
            },
            "spec": {
                "type": "NodePort",
                "selector": labels,
                "ports": [{
                    "port": port,
                    "targetPort": port,
                    "protocol": "TCP"
                }]
            }
        })

    return JSONResponse({"attachments": desired})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080)
