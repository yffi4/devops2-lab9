from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import os

app = FastAPI(title="Pod Team Validator", version="1.0.0")


@app.post("/validate")
async def validate(request: Request):
    body = await request.json()
    uid = body["request"]["uid"]
    obj = body["request"]["object"]
    kind = obj.get("kind", "")
    labels = obj.get("metadata", {}).get("labels", {})

    if kind == "Pod" and "team" not in labels:
        return JSONResponse({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": uid,
                "allowed": False,
                "status": {
                    "code": 403,
                    "message": "Pod must have label 'team'. Example: --labels='team=backend'"
                }
            }
        })

    return JSONResponse({
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": True
        }
    })


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    cert = "/certs/cert.pem"
    key = "/certs/key.pem"
    if os.path.exists(cert):
        uvicorn.run("app:app", host="0.0.0.0", port=8443,
                     ssl_certfile=cert, ssl_keyfile=key)
    else:
        uvicorn.run("app:app", host="0.0.0.0", port=8443)
