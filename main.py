import os
import time
import json
from datetime import datetime

try:
    from anthropic import Anthropic
    import requests
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    exit(1)

print("🚗 BOT LEBONCOIN LANCÉ!")
print("=" * 60)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ Clé API non trouvée!")
    exit(1)

print("✅ Clé API trouvée!")
client = Anthropic(api_key=api_key)
print("=" * 60)

processed = set()

def scrape_cars():
    """Récupère les annonces voitures"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        params = {
            'category': '2',
            'region_id': '0',
            'price_min': '15000',
            'price_max': '25000',
            'limit': '20',
            'sort': 'date'
        }
        resp = requests.get("https://api.leboncoin.fr/finder/search", 
                           params=params, headers=headers, timeout=10)
        data = resp.json()
        ads = data.get('ads', [])
        print(f"✅ {len(ads)} annonces trouvées")
        return ads
    except Exception as e:
        print(f"❌ Erreur scraping: {e}")
        return []

def analyze_car(listing):
    """Analyse une voiture avec Claude"""
    try:
        title = listing.get('title', 'N/A')
        price = listing.get('price', 'N/A')
        
        prompt = f"""Analyse cette annonce voiture:
- Titre: {title}
- Prix: {price}€

Est-ce une bonne affaire (15k-25k€)? Score 0-100.
Réponds UNIQUEMENT en JSON:
{{"score": <nombre>, "raison": "<courte raison>"}}"""

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('```')[1].replace('json', '').strip()
        
        return json.loads(text)
    except:
        return {"score": 0, "raison": "Erreur"}

def main_loop():
    """Boucle principale"""
    iteration = 0
    while True:
        iteration += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{iteration}] {timestamp}")
        
        listings = scrape_cars()
        
        for listing in listings:
            lid = listing.get('id')
            if lid in processed:
                continue
            processed.add(lid)
            
            title = listing.get('title', 'N/A')[:50]
            price = listing.get('price', 'N/A')
            print(f"  🔍 Analyse: {title}... ({price}€)")
            
            analysis = analyze_car(listing)
            score = analysis.get('score', 0)
            
            if score >= 80:
                print(f"  ⭐ BONNE AFFAIRE! Score: {score}/100")
            elif score >= 70:
                print(f"  📌 Intéressant. Score: {score}/100")
        
        print(f"⏳ Prochain scan dans 15 min...")
        time.sleep(900)

if __name__ == "__main__":
    main_loop()
