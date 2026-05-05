import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def extract_servers_from_event(event_url):
    """Extrae TODOS los servidores de la página del evento"""
    try:
        response = requests.get(event_url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        servers = []
        
        # Buscar en la sección de servidores
        servers_section = soup.find('div', class_='stream-servers')
        if not servers_section:
            servers_section = soup.find('div', class_='servers-list')
        
        if servers_section:
            buttons = servers_section.find_all('button', class_='server-btn')
        else:
            buttons = soup.find_all('button', class_='server-btn')
        
        for btn in buttons:
            data_src = btn.get('data-src')
            name = btn.get_text(strip=True)
            
            # Filtrar URLs basura
            if data_src and data_src.startswith('http'):
                if not any(bad in data_src.lower() for bad in ['sharethis.com', 'doubleclick.net']):
                    servers.append({
                        'channel': name,
                        'link': data_src
                    })
        
        return servers
    except Exception as e:
        print(f"   Error: {e}")
        return []

def parse_datetime(datetime_str):
    """Convierte fecha al formato '2026-05-01 18:20 UTC'"""
    try:
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        parts = datetime_str.replace(',', '').split()
        month = months.get(parts[1], 1)
        day = int(parts[2])
        year = int(parts[3])
        time_str = parts[4]
        ampm = parts[5]
        
        hour, minute = map(int, time_str.split(':'))
        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0
        
        # Asumiendo ET, convertir a UTC sumando 4 horas
        hour += 4
        if hour >= 24:
            hour -= 24
            day += 1
        
        return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC"
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M UTC")

def clean_title(title):
    """Limpia el título para que sea más legible"""
    # Eliminar información extra si es necesario
    return title.strip()

def main():
    print("🚀 Leyendo eventos desde all_events.json...")
    
    with open('all_events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    print(f"📋 Eventos encontrados: {len(events)}")
    
    clean_events = []
    eventos_sin_servidores = 0
    
    for idx, event in enumerate(events, 1):
        event_url = event.get('event_url')
        title = event.get('title', 'Sin título')
        league = event.get('league', '')
        datetime_str = event.get('datetime', '')
        
        if not event_url:
            print(f"⚠️ [{idx}/{len(events)}] {title} - Sin URL")
            continue
        
        print(f"\n📺 [{idx}/{len(events)}] {title}")
        
        # Extraer servidores
        servers = extract_servers_from_event(event_url)
        
        if not servers:
            eventos_sin_servidores += 1
            print(f"   ⚠️ No se encontraron servidores")
            continue
        
        # Convertir fecha
        time_utc = parse_datetime(datetime_str)
        title_limpio = clean_title(title)
        
        # Crear un evento por cada servidor (como en el ejemplo)
        for server in servers:
            clean_events.append({
                "title": title_limpio,
                "category": league,
                "time": time_utc,
                "channel": server['channel'],
                "link": server['link']
            })
        
        print(f"   ✅ {len(servers)} servidores encontrados")
    
    # Guardar el JSON limpio
    with open('events_clean.json', 'w', encoding='utf-8') as f:
        json.dump(clean_events, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN")
    print(f"{'='*60}")
    print(f"📋 Eventos procesados: {len(events)}")
    print(f"🗑️ Eventos sin servidores: {eventos_sin_servidores}")
    print(f"✅ Entradas en JSON final: {len(clean_events)}")
    print(f"💾 Archivo guardado: events_clean.json")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()