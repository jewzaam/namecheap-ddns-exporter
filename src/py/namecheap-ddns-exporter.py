import argparse
import socket
import requests
import yaml
import time

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
        ip=requests.get(ip_source).content

    labels = {
        'type': "skip",
        'status': "none",
    }

    try:
        if ip != last_ip:
            response = requests.get("https://dynamicdns.park-your-domain.com/update?host={}&domain={}&ip={}&password={}".format(host,domain,ip,password))
            status_code = response.status_code
            labels['type']="update"
            labels['status']=str(status_code)

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