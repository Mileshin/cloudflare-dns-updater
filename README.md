# Kubernetes Cluster Node DNS Synchronization with Cloudflare

This project was created to provide network access to Kubernetes cluster nodes using domain names. The core idea is to monitor the appearance or disappearance of nodes during scaling operations in the cluster and automatically update DNS records in Cloudflare, adding or removing entries as needed.

## Project Overview

When scaling Kubernetes clusters, it’s essential to maintain consistent access to the nodes. This project aims to automate the DNS management process by tracking changes in the cluster and updating the associated domain records in Cloudflare.

### Features:
- Monitor Kubernetes cluster nodes.
- Automatically add DNS records to Cloudflare when new nodes appear.
- Remove DNS records when nodes are terminated or removed.

## Current Status

At this point, I have decided to pause this approach in favor of a different solution. The project is incomplete, but I hope to return to it and finish it in the future.