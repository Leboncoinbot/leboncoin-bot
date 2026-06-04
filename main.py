import os
import json
import time
import requests
from datetime import datetime
from anthropic import Anthropic

# ===== CONFIGURATION =====
LEBONCOIN_URL = "https://api.leboncoin.fr/finder/search"
CLAUDE_MODEL = "claude-opus-4-6"
SCRAPE_INTERVAL = 900  # 15 minutes
SCORE_THRESHOLD = 80   # Alerte si score >= 80

# Variables globales
processed_listings = set()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ===== FONCTION: SCRAPER LEBONCOIN =====
def scrape_cars():
    """Récupère les annonces voitures de LeBonCoin"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'category': '2',  # Catégorie voitures
            'region_id': '0',  # Toute la France
            'price_min': '15000',
            'price_max': '25000',
            'limit': '50',
            'sort': 'date'
        }
        
        response = requests.get(LEBONCOIN_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        listings = data.get('ads', [])
        
        print(f"✅ {len(listings)} annonces trouvées")
        return listings
    
    except Exception as e:
        print(f"❌ Erreur scraping: {e}")
        return []

# ===== FONCTION: ANALYSER AVEC CLAUDE =====
def analyze_car(listing):
    """Analyse une annonce voiture avec Claude"""
    try:
        prompt = f"""
Analyse cette annonce LeBonCoin voiture 15k-25k€ et évalue si c'est une très bonne affaire.

ANNONCE:
- Titre: {listing.get('title', 'N/A')}
- Prix: {listing.get('price', 'N/A')}€
- Kilométrage: {listing.get('mileage', 'N/A')} km
- Année: {listing.get('year', 'N/A')}
- Marque/Modèle: {listing.get('make_model', 'N/A')}
- Localisation: {listing.get('location', 'N/A')}
- Description: {listing.get('description', 'N/A')[:500]}
- Photos: {listing.get('num_photos', 0)} photo(s)

ÉVALUE ces critères:
1. Prix vs marché (bon deal?)
2. Kilométrage (normal?)
3. État général (bon?)
4. Signaux d'alerte (accident, réparation?)

Réponds UNIQUEMENT en JSON valide (pas d'autres textes):
{{
    "score": <0-100>,
    "prix_verdict": "<bon/correct/cher>",
    "raison_principale": "<pourquoi c'est bon ou mauvais>",
    "drapeaux_rouges": [<liste des problèmes>],
    "conseil": "<acheter/attendre/refuser>"
}}
"""
        
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        # Nettoie le JSON si besoin
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1].replace('json', '').strip()
        
        analysis = json.loads(response_text)
        return analysis
    
    except Exception as e:
        print(f"❌ Erreur analyse Claude: {e}")
        return {"score": 0, "raison_principale": "Erreur analyse"}

# ===== FONCTION: DÉCIDER ACTION =====
def decide_action(listing, analysis):
    """Décide si on envoie une alerte ou un message"""
    score = analysis.get('score', 0)
    
    if score >= 80:
        return {
            'type': 'HIGH_ALERT',
            'message': f"⭐ TRÈS BONNE AFFAIRE! {listing.get('title')} - {listing.get('price')}€ (Score: {score}/100)\n{analysis.get('raison_principale')}"
        }
    elif score >= 70:
        return {
            'type': 'ALERT',
            'message': f"📌 Bonne affaire: {listing.get('title')} - {listing.get('price')}€ (Score: {score}/100)"
        }
    else:
        return {'type': 'SKIP'}

# ===== FONCTION: ENVOYER ALERTE =====
def send_alert(alert_data):
    """Envoie une alerte (console pour l'instant)"""
    if alert_data['type'] == 'SKIP':
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{alert_data['message']}")
    print(f"[{timestamp}]")
    print("=" * 60)

# ===== BOUCLE PRINCIPALE =====
def main_loop():
    """Boucle infinie qui scrape et analyse"""
    print("🚗 BOT LEBONCOIN LANCÉ!")
    print(f"Configuration: {SCORE_THRESHOLD}€ min, alerte tous les {SCRAPE_INTERVAL}s")
    print("=" * 60)
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n[Itération {iteration}] {datetime.now().strftime('%H:%M:%S')}")
        
        # Scraper
        listings = scrape_cars()
        
        # Analyser chaque annonce
        for listing in listings:
            listing_id = listing.get('id', listing.get('list_id'))
            
            # Éviter les doublons
            if listing_id in processed_listings:
                continue
            
            processed_listings.add(listing_id)
            
            # Analyser
            print(f"  🔍 Analyse: {listing.get('title', 'N/A')[:50]}...")
            analysis = analyze_car(listing)
            
            # Décider
            action = decide_action(listing, analysis)
            
            # Agir
            if action['type'] != 'SKIP':
                send_alert(action)
        
        # Attendre avant prochaine itération
        print(f"\n⏳ Prochain scan dans {SCRAPE_INTERVAL}s...")
        time.sleep(SCRAPE_INTERVAL)

# ===== POINT D'ENTRÉE =====
if __name__ == "__main__":
    main_loop()
