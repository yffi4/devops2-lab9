from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Namespace Roles Operator", version="1.0.0")

SYSTEM_NS = [
    "kube-system", "kube-public", "kube-node-lease", "default",
    "argocd", "longhorn-system", "argo-rollouts", "traefik", "metacontroller"
]


@app.post("/sync")
async def sync(request: Request):
    body = await request.json()
    parent = body.get("object", {})
    ns_name = parent.get("metadata", {}).get("name", "")

    if ns_name in SYSTEM_NS:
        return JSONResponse({"attachments": []})

    desired = []

    # view — только чтение
    desired.append({
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": {
            "name": f"{ns_name}-view",
            "namespace": ns_name,
            "labels": {"created-by": "namespace-operator", "role-type": "view"}
        },
        "rules": [{
            "apiGroups": ["", "apps", "batch"],
            "resources": ["pods", "services", "deployments", "configmaps", "jobs"],
            "verbs": ["get", "list", "watch"]
        }]
    })

    # edit — чтение + запись
    desired.append({
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": {
            "name": f"{ns_name}-edit",
            "namespace": ns_name,
            "labels": {"created-by": "namespace-operator", "role-type": "edit"}
        },
        "rules": [{
            "apiGroups": ["", "apps", "batch"],
            "resources": ["pods", "services", "deployments", "configmaps", "secrets", "jobs"],
            "verbs": ["get", "list", "watch", "create", "update", "patch", "delete"]
        }]
    })

    # admin — полный доступ
    desired.append({
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": {
            "name": f"{ns_name}-admin",
            "namespace": ns_name,
            "labels": {"created-by": "namespace-operator", "role-type": "admin"}
        },
        "rules": [{
            "apiGroups": ["*"],
            "resources": ["*"],
            "verbs": ["*"]
        }]
    })

    return JSONResponse({"attachments": desired})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080)
