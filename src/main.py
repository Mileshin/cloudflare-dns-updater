import os
import json
import sys
import logging
from kubernetes import client, config, watch
from cloudflare import CloudFlare

# Set logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
## Cloudflare info
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_ZONE_ID = os.getenv('CLOUDFLARE_ZONE_ID')
DOMAIN_SUFFIX = os.getenv('DOMAIN_SUFFIX', 'gigaspace.live')
## Path for store state
STATE_FILE = os.getenv('STATE_FILE', '/data/state.json')

# Initialize Cloudflare API client
cf = CloudFlare(token=CLOUDFLARE_API_TOKEN)

def check_file_access():
    if not os.path.exists(STATE_FILE):
        raise FileNotFoundError(f"State file '{STATE_FILE}' not found.")
    if not os.access(STATE_FILE, os.R_OK | os.W_OK):
        raise PermissionError(f"No read/write access to the state file '{STATE_FILE}'.")

# Load the current state from the state file
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading state from {STATE_FILE}: {e}", exc_info=True)
            return set()
    return set()

# Save the current state to the state file
def save_state(ips):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(list(ips), f)
        logging.info(f"State successfully saved to {STATE_FILE}")
    except IOError as e:
        logging.error(f"Error saving state to {STATE_FILE}: {e}", exc_info=True)


# Add DNS record
def add_dns_record(node_id):
    record_name = f"{node_id.replace('.', '-')}.{DOMAIN_SUFFIX}"
    record_data = {
        'type': 'A',
        'name': record_name,
        'content': node_id,
        'ttl': 120,
        'proxied': False
    }
    try:
        existing_records = cf.zones.dns_records.get(CLOUDFLARE_ZONE_ID, params={'name': record_name, 'type': 'A'})
        if existing_records:
            logging.warning(f"DNS record {record_name} already exists with IP: {existing_records[0]['content']}")
            # Update existsng record
            record_id = existing_records[0]['id']
            cf.zones.dns_records.put(CLOUDFLARE_ZONE_ID, record_id, data=record_data)
            logging.info(f"DNS record updated: {record_name} -> {node_id}")
        else:
            # Add new record
            cf.zones.dns_records.post(CLOUDFLARE_ZONE_ID, data=record_data)
            logging.info(f"DNS record added: {record_name} -> {node_id}")    
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        logging.error(f"Error adding/updating DNS record: {e}", exc_info=True)

# Delete DNS record
def delete_dns_record(node_id):
    record_name = f"{node_id.replace('.', '-')}.{DOMAIN_SUFFIX}"
    try:
        dns_records = cf.zones.dns_records.get(CLOUDFLARE_ZONE_ID, params={'name': record_name})
        
        # Check that records exists
        if not dns_records:
            logging.warning(f"No DNS records found for: {record_name}")
            return
        
        # Delete records
        for record in dns_records:
            cf.zones.dns_records.delete(CLOUDFLARE_ZONE_ID, record['id'])
            logging.info(f"DNS record deleted: {record_name}")
            
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        logging.error(f"Error deleting DNS record: {e}", exc_info=True)


def get_node_external_ips():
    try:
        config.load_incluster_config()  
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        
        external_ips = []
        for node in nodes.items:

            for address in node.status.addresses:
                if address.type == "ExternalIP":
                    external_ips.append((node.metadata.name, address.address))  
                    logging.info(f"Node ID: {node.metadata.name}, External IP: {address.address}")

        if not external_ips:
            logging.warning("No external IPs found for any nodes.")
        
        return external_ips

    except Exception as e:
        logging.error(f"Error fetching node external IPs: {e}", exc_info=True)
        return []


def main():
    try:
        check_file_access()
        state = load_state()

        save_state(state)  
    except (FileNotFoundError, PermissionError) as e:
        logging.critical(e, exc_info=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
    #start_leader_election()