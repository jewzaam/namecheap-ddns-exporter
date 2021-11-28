# namecheap-ddns-exporter
Simple ddns with namecheap and export metrics for it.

# Setup

## Clone Source

I am running on ec2 and simply clone into the ec2-user's home directory.

```shell
git clone https://github.com/jewzaam/namecheap-ddns-exporter
```

## config.yaml

You can name the file whatever you want, but this document assumes **config.yaml**.

Pick a port and setup [DDNS in namecheap](https://www.namecheap.com/support/knowledgebase/subcategory/11/dynamic-dns/).

```yaml
refresh_delay_seconds: 300
host: <the DDNS host>
domain: <your domain>
password: <your Dynamic DNS Password>
ip_source: <URL to fetch IP address>
```

`refresh_delay_seconds` can be quick if you're 

`ip_source` examples:
- **local** is a special case where no external service is used, just gets the local IP address
- http://169.254.169.254/latest/meta-data/public-ipv4 for AWS specifically
- https://api.ipify.org for generic query

## Linux Service

Install the service by setting up some env vars then copying the systemd template with those vars, start the service, and enable the service.

```shell
export WORKING_DIR=~/namecheap-ddns-exporter
export PORT=8004
export CONFIG=~/namecheap-ddns-exporter/config.yaml

sudo cat $WORKING_DIR/src/systemd/namecheap-ddns.service | envsubst > /etc/systemd/system/namecheap-ddns.service

unset WORKING_DIR
unset PORT
unset CONFIG

sudo systemctl start namecheap-ddns.service
sudo systemctl enable namecheap-ddns.service
```

## Windows Service

There is a simple .bat file included which can be edited to tune config and port.  Make sure the repo, you configuration, and the .bat are not going to be deleted by something (like happened with me with Dropbox!).

As this is likely to provide access to a remote host by name you want it to run at system startup.  Use "Task Scheduler" to set it to run the .bat without a user when network is connected.

# Verify

## DDNS
Check the IP address is updated for the record in Namecheap when it is started and on any IP address change (such as when changing networks).

## Metrics 
Check the metrics are exported on the port you specified.
