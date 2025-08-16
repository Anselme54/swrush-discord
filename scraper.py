import os
import requests
from bs4 import BeautifulSoup

# URL de la page des annonces
BASE_URL = "https://withhive.com"
GAME_URL = f"{BASE_URL}/notice/game/1952"

# Webhook Discord depuis les variables d'environnement
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("La variable d'environnement DISCORD_WEBHOOK_URL est manquante.")

# Récupérer la page principale
response = requests.get(GAME_URL)
soup = BeautifulSoup(response.text, 'html.parser')

# Trouver toutes les annonces
annonces = soup.find_all('a', href=True)

for annonce in annonces:
    href = annonce['href']
    if href.startswith('/notice/1952/'):
        full_link = BASE_URL + href
        titre = annonce.get_text(strip=True)

        # Essayer de récupérer l'image associée à l'annonce
        # Cherche le premier <img> précédent le lien
        img_tag = annonce.find_previous('img')
        image_url = BASE_URL + img_tag['src'] if img_tag and img_tag.get('src', '').startswith('/') else img_tag['src'] if img_tag else None

        # Préparer le payload pour Discord
        embed = {
            "title": titre,
            "url": full_link,
        }
        if image_url:
            embed["thumbnail"] = {"url": image_url}

        data = {
            "embeds": [embed]
        }

        # Envoyer sur Discord via webhook
        resp = requests.post(WEBHOOK_URL, json=data)
        if resp.status_code != 204 and resp.status_code != 200:
            print(f"Erreur lors de l'envoi de l'annonce {titre}: {resp.status_code} - {resp.text}")
