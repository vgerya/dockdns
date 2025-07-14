import threading

import docker
import os
import time
import requests
from jinja2 import Template

HOST_LABEL = os.environ.get("HOST_LABEL", "unknown-host")
TRAEFIK_OUTPUT_DIR = os.environ.get("TRAEFIK_OUTPUT_DIR", "/mnt/traefik-dynamic")
TRAEFIK_TEMPLATE_PATH = os.environ.get("TRAEFIK_TEMPLATE_PATH", "templates/traefik_router.tmpl")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception as e:
            print(f"[WARN] Telegram failed: {e}")

def yaml_path(hostname, container):
    return f"{TRAEFIK_OUTPUT_DIR}/{hostname}_{container.id[:12]}.yaml"

def render_traefik_config(hostname, ip, port, container):
    with open(TRAEFIK_TEMPLATE_PATH) as f:
        template = Template(f.read())
    rendered = template.render(hostname=hostname, ip=ip, port=port)
    output_path = yaml_path(hostname, container)
    if DRY_RUN:
        print(f"[DRY RUN] Would write {output_path}:{rendered}")
    else:
        with open(output_path, "w") as f:
            f.write(rendered)
        print(f"[TRAEFIK] Wrote config to {output_path}")
        send_telegram(f"[Traefik] \U0001F195 Added route: {hostname} → {ip}:{port}")

def delete_traefik_config(container):
    hostname = container.labels.get("dns.home.box")
    if not hostname:
        return
    path = yaml_path(hostname, container)
    if os.path.exists(path):
        if DRY_RUN:
            print(f"[DRY RUN] Would delete {path}")
        else:
            os.remove(path)
            print(f"[TRAEFIK] Removed config: {path}")
            send_telegram(f"[Traefik] ❌ Removed route: {hostname}")

def process_container(container):
    labels = container.labels
    hostname = labels.get("dockdns.target.hostname")
    port = labels.get("dns.target.port")

    # TODO form  hostname
    hostname = f"{hostname:{container.name}}.{HOST_LABEL}"

    if not hostname or not port:
        return

    ip = None
    try:
        ip = container.attrs["NetworkSettings"]["IPAddress"]
        if not ip and container.attrs["HostConfig"]["NetworkMode"] == "host":
            ip = os.popen("hostname -I").read().split()[0]
    except Exception as e:
        print(f"[WARN] Can't get IP for {hostname}: {e}")
        return

    print(f"[INFO] Register {hostname} → {ip}:{port}")
    render_traefik_config(hostname, ip, port, container)

def init_existing_containers(client):
    print("[INIT] Checking existing containers...")
    for container in client.containers.list(filters={"status": "running"}):
        labels = container.labels
        if "dns.home.box" in labels and "dns.target_port" in labels:
            process_container(container)

def watch_docker_events():
    client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
    init_existing_containers(client)
    print("[START] Agent watching Docker events...")
    while True:
        try:
            for event in client.events(decode=True):
                if event.get("Type") == "container":
                    action = event.get("Action")
                    container = client.containers.get(event["id"])
                    if action == "start":
                        process_container(container)
                    elif action in ["die", "stop", "destroy"]:
                        delete_traefik_config(container)
        except Exception as e:
            print(f"[ERROR] Main loop failed: {e}")
            time.sleep(5)


def start_docker_watcher():
    thread = threading.Thread(target=watch_docker_events, daemon=True)
    thread.start()