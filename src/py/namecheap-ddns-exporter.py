import argparse
import socket
import requests
import yaml
import time
import xml.etree.ElementTree as ET

import metrics_utility

last_ip=""

def updateDDNS(config):
    global last_ip
    domain=config['domain']
    password=config['password']
    host=config['host']
    ip_source=config['ip_source']
    if ip_source == "local":
        ip=socket.gethostbyname(socket.gethostname())
    else:
        ip=requests.get(ip_source).text.strip()

    labels = {
        'type': "skip",
        'status': "none",
    }

    try:
        if ip != last_ip:
            print(f"[UPDATE] IP address changed: {last_ip} -> {ip}")
            print(f"[UPDATE] Updating DDNS for {host}.{domain}...")
            # Note: host and domain must match exact case as shown in Namecheap account
            # Match documentation order: host, domain, password, ip
            url = "https://dynamicdns.park-your-domain.com/update?host={}&domain={}&password={}&ip={}".format(host,domain,password,ip)
            print(f"[UPDATE] Calling API: https://dynamicdns.park-your-domain.com/update?host={host}&domain={domain}&password=***&ip={ip}")
            response = requests.get(url)
            status_code = response.status_code
            # Handle UTF-16 encoding as specified in XML response
            response_text = response.text.strip()
            labels['type']="update"
            labels['status']=str(status_code)
            print(f"[UPDATE] DDNS update response: HTTP {status_code}")
            print(f"[UPDATE] Response body: {response_text}")
            if status_code == 200:
                # Parse XML response to check for success
                try:
                    # Handle UTF-16 encoding if present
                    if response_text.startswith('<?xml'):
                        root = ET.fromstring(response_text)
                    else:
                        # Try to decode if needed
                        root = ET.fromstring(response_text)
                    
                    err_count = root.find('ErrCount')
                    done = root.find('Done')
                    errors = root.find('errors')
                    response_ip = root.find('IP')
                    
                    err_count_val = int(err_count.text) if err_count is not None and err_count.text else -1
                    done_val = done.text.lower() == 'true' if done is not None and done.text else False
                    returned_ip = response_ip.text if response_ip is not None and response_ip.text else None
                    
                    if err_count_val == 0 and done_val:
                        print(f"[UPDATE] API reported success - ErrCount: {err_count_val}, Done: {done_val}")
                        if returned_ip:
                            print(f"[UPDATE] API returned IP: {returned_ip}")
                        # Verify DNS update by resolving the hostname
                        try:
                            fqdn = f"{host}.{domain}" if host != "@" else domain
                            resolved_ip = socket.gethostbyname(fqdn)
                            print(f"[UPDATE] DNS verification: {fqdn} resolves to {resolved_ip}")
                            if resolved_ip == ip:
                                print(f"[UPDATE] ✓ Successfully updated A record - DNS verified: {fqdn} -> {ip}")
                            else:
                                print(f"[UPDATE] ⚠ Warning: DNS shows {resolved_ip} but expected {ip}. Update may be propagating or failed.")
                        except socket.gaierror as dns_err:
                            print(f"[UPDATE] ⚠ Warning: Could not verify DNS update: {dns_err}")
                    else:
                        error_msgs = []
                        if errors is not None and len(errors) > 0:
                            for error in errors:
                                error_msgs.append(error.text if error.text else str(error))
                        print(f"[UPDATE] ✗ Update failed - ErrCount: {err_count_val}, Done: {done_val}")
                        if error_msgs:
                            print(f"[UPDATE] Errors: {', '.join(error_msgs)}")
                except ET.ParseError as e:
                    print(f"[UPDATE] ✗ Warning: Failed to parse XML response: {e}")
                    print(f"[UPDATE] Raw response: {response_text}")
            else:
                print(f"[UPDATE] ✗ Warning: Unexpected status code {status_code}")
        else:
            print(f"[SKIP] IP address unchanged ({ip}), skipping DDNS update")

        last_ip = ip
    except Exception as e:
        # in case we get an error capture in totals and print it
        labels['type']="error"
        print(e)
        # then treat this as a "pass" so we can then export the metric
        pass

    metrics_utility.inc("ddns_setup_total",labels)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Keep Namecheap DDNS up to date.")
    parser.add_argument("--port", type=int, help="port to expose metrics on")
    parser.add_argument("--config", type=str, help="configuraiton file")
    
    args = parser.parse_args()
    
    # Start up the server to expose the metrics.
    metrics_utility.metrics(args.port)

    while True:
        config = {}
        with open(args.config, 'r') as f:
            config =  yaml.safe_load(f)
        updateDDNS(config)
        time.sleep(config['refresh_delay_seconds'])