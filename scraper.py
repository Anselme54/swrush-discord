import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import discord

# Discord webhook depuis secret
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("La variable d'environnement DISCORD_WEBHOOK_URL est manquante.")

# URL des annonces
BASE_URL = "https://withhive.com"
GAME_URL = f"{BASE_URL}/notice/game/1952"

# Configurer Selenium en mode headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.get(GAME_URL)

# Attendre que JavaScript charge le contenu
time.sleep(5)  # Ajuste si besoin selon la vitesse de chargement

html = driver.page_source
driver.quit()

# Parser le HTML
soup = BeautifulSoup(html, 'html.parser')

# Trouver les annonces
annonces = soup.find_all('a', href=True)
webhook = discord.SyncWebhook.from_url(WEBHOOK_URL)

for annonce in annonces:
    href = annonce['href']
    if href.startswith('/notice/1952/'):
        full_link = BASE_URL + href
        titre = annonce.get_text(strip=True) or "Nouvelle annonce"

        # Trouver l'image associée (si présente)
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

        # Envoyer l'embed
        webhook.send(embed=embed)
