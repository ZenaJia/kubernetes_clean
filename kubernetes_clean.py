#!/usr/bin/env python3
"""
Clean up Kubernetes pods in bad states
"""

import sys
from typing import List, Dict
from kubernetes import client, config


def get_k8s_client():
    """Load kubeconfig and return API client"""
    config.load_kube_config()
    return client.CoreV1Api()


def should_delete_pod(pod) -> bool:
    """Check if pod should be deleted based on its state"""
    status = pod.status

    # Check for Evicted
    if status.reason == 'Evicted':
        return True

    # Check for Completed (Succeeded phase)
    if status.phase == 'Succeeded':
        return True

    # Check for Failed/Error
    if status.phase == 'Failed':
        return True

    # Check container statuses for OOMKilled
    if status.container_statuses:
        for container in status.container_statuses:
            if container.state.terminated:
                reason = container.state.terminated.reason
                if reason == 'OOMKilled':
                    return True

    return False


def get_pod_state(pod) -> str:
    """Determine pod state for output"""
    status = pod.status

    if status.reason == 'Evicted':
        return 'Evicted'

    if status.phase == 'Succeeded':
        return 'Completed'

    if status.phase == 'Failed':
        return 'Error'

    # Check for OOMKilled
    if status.container_statuses:
        for container in status.container_statuses:
            if container.state.terminated:
                if container.state.terminated.reason == 'OOMKilled':
                    return 'OOMKilled'

    return 'Unknown'


def clean_pods(namespaces: List[str]) -> List[Dict[str, str]]:
    """
    Delete pods in bad states from given namespaces

    Args:
        namespaces: List of namespace names

    Returns:
        List of deleted pods with name, namespace, and state
    """
    v1 = get_k8s_client()

    deleted_pods = []

    for namespace in namespaces:
        try:
            # Get all pods in this namespace
            pods = v1.list_namespaced_pod(namespace)

            for pod in pods.items:
                if should_delete_pod(pod):
                    pod_name = pod.metadata.name
                    pod_state = get_pod_state(pod)

                    try:
                        # Delete the pod
                        v1.delete_namespaced_pod(
                            name=pod_name,
                            namespace=namespace
                        )

                        deleted_pods.append({
                            'name': pod_name,
                            'namespace': namespace,
                            'state': pod_state
                        })

                        print(f"Deleted: {namespace}/{pod_name} ({pod_state})")

                    except client.exceptions.ApiException as e:
                        print(f"Error deleting {namespace}/{pod_name}: {e}", file=sys.stderr)

        except client.exceptions.ApiException as e:
            print(f"Error listing pods in namespace {namespace}: {e}", file=sys.stderr)

    return deleted_pods


def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python kubernetes_clean.py <namespace1> <namespace2> ...")
        sys.exit(1)

    namespaces = sys.argv[1:]
    deleted_pods = clean_pods(namespaces)

    print(f"\nTotal deleted: {len(deleted_pods)} pods")


if __name__ == '__main__':
    main()
