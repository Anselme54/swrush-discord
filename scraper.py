import os
import requests
from bs4 import BeautifulSoup
import discord

# Webhook Discord depuis les variables d'environnement
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("La variable d'environnement DISCORD_WEBHOOK_URL est manquante.")

# URL de la page des annonces
BASE_URL = "https://withhive.com"
GAME_URL = f"{BASE_URL}/notice/game/1952"

# Récupérer la page principale
response = requests.get(GAME_URL)
soup = BeautifulSoup(response.text, 'html.parser')

# Trouver toutes les annonces
annonces = soup.find_all('a', href=True)

# Préparer le webhook Discord (version 2.x)
webhook = discord.SyncWebhook.from_url(WEBHOOK_URL)

for annonce in annonces:
    href = annonce['href']
    if href.startswith('/notice/1952/'):
        full_link = BASE_URL + href
        titre = annonce.get_text(strip=True)

        # Récupérer l'image associée
        img_tag = annonce.find_previous('img')
        image_url = None
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = BASE_URL + src if src.startswith('/') else src

        # Créer l'embed Discord
        embed = discord.Embed(title=titre, url=full_link)
        if image_url:
            embed.set_thumbnail(url=image_url)

        # Envoyer l'embed sur Discord
        webhook.send(embed=embed)
