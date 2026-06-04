import os
import time
from datetime import datetime

print("🚗 BOT LEBONCOIN - VERSION SIMPLE")
print("=" * 60)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if api_key:
    print(f"✅ Clé API trouvée!")
else:
    print("❌ Clé API non trouvée")

print("=" * 60)

iteration = 0
while True:
    iteration += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{iteration}] {timestamp} - Bot en marche!")
    time.sleep(60)
