# Kubernetes Pod Cleanup Script

Removes pods in bad states from Kubernetes namespaces.

## What it does

Deletes pods in these states:
- **Evicted** - Pod was evicted due to resource pressure
- **Completed** - Pod finished successfully (Succeeded phase)
- **OOMKilled** - Pod was killed due to out of memory
- **Error** - Pod failed (Failed phase)

## Requirements

```bash
pip install kubernetes
```

## Usage

### Command Line

```bash
python kubernetes_clean.py <namespace1> <namespace2> ...
```

Example:
```bash
python kubernetes_clean.py default kube-system my-app
```

### As a Module

```python
from kubernetes_clean import clean_pods

deleted = clean_pods(["default", "kube-system"])

for pod in deleted:
    print(f"Deleted {pod['namespace']}/{pod['name']} - {pod['state']}")
```

## Output

The script prints each deleted pod:
```
Deleted: default/my-pod-xyz (Evicted)
Deleted: default/job-123 (Completed)

Total deleted: 2 pods
```

## Notes

- Requires a valid kubeconfig file (usually at `~/.kube/config`)
- Needs appropriate RBAC permissions to list and delete pods
