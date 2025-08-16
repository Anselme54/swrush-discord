import os, re, json, time
from pathlib import Path
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup

GAME_ID = 1952
BASE = "https://withhive.com"
HOME = f"{BASE}/?language=en"
NOTICE_RE = re.compile(rf"/notice/{GAME_ID}/(\d+)$")
STATE_FILE = Path("state.json")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

def get_webhook() -> str:
    wh = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not wh:
        raise SystemExit("Missing env DISCORD_WEBHOOK_URL")
    return wh

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_id": 0}

def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def fetch(url: str) -> Optional[requests.Response]:
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if r.status_code == 200:
            return r
        return None
    except requests.RequestException:
        return None

def find_ids_on_homepage() -> List[int]:
    resp = fetch(HOME)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    ids = []
    for a in soup.find_all("a", href=True):
        m = NOTICE_RE.search(a["href"])
        if m:
            try:
                ids.append(int(m.group(1)))
            except ValueError:
                pass
    return sorted(set(ids))

def probe_notice(post_id: int) -> Optional[Tuple[int, str, str]]:
    """
    Check if a notice exists for given ID.
    Returns (id, title, url) if found, else None.
    """
    url = f"{BASE}/notice/{GAME_ID}/{post_id}"
    resp = fetch(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")

    # Titre le plus fiable possible
    title = None
    if soup.title and soup.title.text.strip():
        title = soup.title.text.strip()
    # Nettoyage éventuel du suffixe du site
    if title:
        title = re.sub(r"\s*-\s*Global Gaming Services\s*$", "", title).strip()

    # fallback très simple : première balise h1 si dispo
    if not title:
        h1 = soup.find(["h1","h2"])
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)

    if not title:
        return None

    return (post_id, title, url)

def post_to_discord(webhook: str, title: str, url: str) -> bool:
    payload = {
        "content": f"🆕 **{title}**\n{url}",
        "allowed_mentions": {"parse": []}
    }
    try:
        r = requests.post(webhook, json=payload, timeout=20,
                          headers={"User-Agent": USER_AGENT})
        return 200 <= r.status_code < 300
    except requests.RequestException:
        return False

def main():
    webhook = get_webhook()
    state = load_state()
    last_id = int(state.get("last_id", 0))

    # Initialisation du pointeur si inconnu : essaye de déduire un ID récent depuis la home
    if last_id == 0:
        home_ids = find_ids_on_homepage()
        if home_ids:
            last_id = max(home_ids)
        else:
            # Valeur de secours raisonnable (on scannera vers l'avant)
            last_id = 82000

    # Scanner une petite fenêtre d’IDs futurs (ajuste si tu veux ratisser plus large)
    window = 50
    candidates = range(last_id + 1, last_id + 1 + window)

    found = []
    for i in candidates:
        info = probe_notice(i)
        if info:
            found.append(info)
        # petite courtoisie pour le serveur (évite de spammer)
        time.sleep(0.25)

    if not found:
        print("No new notices.")
        return

    # Publie dans l’ordre croissant
    found.sort(key=lambda t: t[0])
    for post_id, title, url in found:
        ok = post_to_discord(webhook, title, url)
        print(f"POST {post_id} -> {'OK' if ok else 'FAIL'} : {title}")
        if ok:
            state["last_id"] = max(int(state.get("last_id", 0)), post_id)

    save_state(state)

if __name__ == "__main__":
    main()
