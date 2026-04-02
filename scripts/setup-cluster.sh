#!/bin/bash
set -e

REPO_URL="https://github.com/yffi4/devops2-lab9.git"
ARGOCD_NODEPORT=30443
KUBECONFIG_PATH="/etc/kubernetes/admin.conf"

export KUBECONFIG=$KUBECONFIG_PATH

echo "[1/8] Checking cluster..."
kubectl get nodes
echo "Done."

echo "[2/8] Removing control-plane taint..."
kubectl taint nodes --all node-role.kubernetes.io/control-plane- 2>/dev/null || true
echo "Done."

echo "[3/8] Installing ArgoCD..."
kubectl create namespace argocd 2>/dev/null || true
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --server-side --force-conflicts
echo "Waiting for ArgoCD pods..."
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s
echo "Done."

echo "[4/8] Exposing ArgoCD UI on NodePort ${ARGOCD_NODEPORT}..."
kubectl -n argocd patch svc argocd-server --type='json' -p="[
  {\"op\":\"replace\",\"path\":\"/spec/type\",\"value\":\"NodePort\"},
  {\"op\":\"replace\",\"path\":\"/spec/ports/0/nodePort\",\"value\":${ARGOCD_NODEPORT}}
]"
echo "Done."

echo "[5/8] Installing ArgoCD CLI..."
if ! command -v argocd &> /dev/null; then
    curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    chmod +x /usr/local/bin/argocd
fi
echo "Done."

echo "[6/8] Getting ArgoCD password..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "Done."

echo "[7/8] Logging into ArgoCD..."
argocd login localhost:${ARGOCD_NODEPORT} --username admin --password "${ARGOCD_PASSWORD}" --insecure
echo "Done."

echo "[8/8] Applying App of Apps..."
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-of-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: ${REPO_URL}
    targetRevision: main
    path: argocd/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
echo "Done."

echo "Waiting for sync..."
sleep 30
argocd app list

echo ""
echo "Setup complete."
echo "ArgoCD UI: https://localhost:${ARGOCD_NODEPORT}"
echo "Login: admin / ${ARGOCD_PASSWORD}"
echo ""
echo "Check status: argocd app list"
