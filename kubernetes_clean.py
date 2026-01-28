#!/usr/bin/env python3
"""
Clean up Kubernetes pods in bad states
"""

import sys
from typing import List, Dict
from kubernetes import client, config


def clean_pods(namespaces: List[str]) -> List[Dict[str, str]]:
    """
    Delete pods in bad states from given namespaces

    Args:
        namespaces: List of namespace names

    Returns:
        List of deleted pods with name, namespace, and state
    """
    # Load kubeconfig
    config.load_kube_config()
    v1 = client.CoreV1Api()

    deleted_pods = []

    for namespace in namespaces:
        # Get all pods in this namespace
        pods = v1.list_namespaced_pod(namespace)

        for pod in pods.items:
            pod_name = pod.metadata.name
            status = pod.status

            # Check if pod should be deleted
            should_delete = False
            pod_state = None

            # Check for Evicted
            if status.reason == 'Evicted':
                should_delete = True
                pod_state = 'Evicted'

            # Check for Completed (Succeeded phase)
            elif status.phase == 'Succeeded':
                should_delete = True
                pod_state = 'Completed'

            # Check for Failed/Error
            elif status.phase == 'Failed':
                should_delete = True
                pod_state = 'Error'

            # Check container statuses for OOMKilled
            elif status.container_statuses:
                for container in status.container_statuses:
                    if container.state.terminated:
                        reason = container.state.terminated.reason
                        if reason == 'OOMKilled':
                            should_delete = True
                            pod_state = 'OOMKilled'
                            break

            # Delete if needed
            if should_delete:
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
