import requests

from agent.dockdns_config import DockDNSConfig


def send_telegram(dock_dn_config: DockDNSConfig, message: str):
    if dock_dn_config.notifications_enabled and dock_dn_config.telegram_token and dock_dn_config.telegram_chat_id:
        url = f"https://api.telegram.org/bot{dock_dn_config.telegram_token}/sendMessage"
        try:
            requests.post(url, data={"chat_id": dock_dn_config.telegram_chat_id, "text": message})
        except Exception as e:
            print(f"[WARN] Telegram failed: {e}", exc_info=True)
