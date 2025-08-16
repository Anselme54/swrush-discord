import requests
from bs4 import BeautifulSoup
import discord
import os

# Récupérer l'URL du webhook depuis les variables d'environnement
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("La variable d'environnement DISCORD_WEBHOOK_URL est manquante.")

# Créer un client Discord
client = discord.Client()

# URL de la page des annonces
base_url = "https://withhive.com/notice/game/1952"
response = requests.get(base_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Trouver toutes les annonces
annonces = soup.find_all('a', href=True)

# Filtrer les liens des annonces individuelles
for annonce in annonces:
    href = annonce['href']
    if href.startswith('/notice/1952/'):
        full_link = "https://withhive.com" + href
        titre = annonce.get_text(strip=True)

        # Récupérer l'image associée à l'annonce
        img_tag = annonce.find_previous('img')
        image_url = img_tag['src'] if img_tag else None

        # Créer le message à envoyer sur Discord
        embed = discord.Embed(title=titre, url=full_link)
        if image_url:
            embed.set_thumbnail(url=image_url)

        # Envoyer le message sur Discord
        @client.event
        async def on_ready():
            channel = client.get_channel(123456789012345678)  # Remplacer par l'ID de ton canal
            await channel.send(embed=embed)
            await client.close()

# Démarrer le client Discord
client.run(WEBHOOK_URL)
