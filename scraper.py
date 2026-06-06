from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import json
from datetime import datetime

BASE = "https://istreameast.cx"
MAIN_URL = BASE

def get_all_events(page):
    """Obtiene TODOS los eventos de la página principal"""
    print("Cargando pagina principal...")
    try:
        page.goto(MAIN_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
    except Exception as e:
        print(f"Error cargando página principal: {e}")
        return []
    
    events_data = page.evaluate("""
    () => {
        let events = [];
        const container = document.querySelector('#todays-events-list');
        if (!container) return events;
        
        const cards = container.querySelectorAll('.event-card');
        
        cards.forEach(card => {
            const onclick = card.getAttribute('onclick') || '';
            let link = '';
            if (onclick.includes("window.location.href")) {
                link = onclick.split("'")[1];
            }
            
            const eventInfo = card.querySelector('.event-info');
            if (!eventInfo) return;
            
            const titleElem = eventInfo.querySelector('.event-title');
            const datetimeElem = eventInfo.querySelector('.event-datetime');
            const leagueElem = eventInfo.querySelector('.event-league');
            
            let title = titleElem ? titleElem.innerText.trim() : '';
            let datetime = datetimeElem ? datetimeElem.innerText.trim() : '';
            let league = '';
            let status = '';
            
            if (leagueElem) {
                league = leagueElem.childNodes[0]?.textContent?.trim() || '';
                const statusSpan = leagueElem.querySelector('.event-status');
                if (statusSpan) {
                    status = statusSpan.innerText.trim();
                }
            }
            
            if (title && link) {
                events.push({
                    title: title,
                    datetime: datetime,
                    league: league,
                    status: status,
                    event_url: window.location.origin + link
                });
            }
        });
        
        return events;
    }
    """)
    
    return events_data

def save_to_json(events, filename="all_events.json"):
    """Guarda los eventos en el formato que espera el segundo script"""
    output = {
        'scraping_date': datetime.now().isoformat(),
        'total_events': len(events),
        'events': events
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return filename

def main():
    with sync_playwright() as p:
        # 🔥 CONFIGURACIÓN ANTI-DETECCIÓN 🔥
        browser = p.chromium.launch(
            headless=True,  # Seguimos con headless=False (menos detectable)
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--start-maximized',
            ]
        )
        
        page = browser.new_page()
        
        # 🔥 OCULTAR webdriver 🔥
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
        """)
        
        # 🔥 USER AGENT REAL 🔥
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        events = get_all_events(page)
        
        print(f"\n📋 Eventos encontrados en la página principal: {len(events)}")
        
        # Filtrar eventos no terminados
        events_to_save = [e for e in events if e['status'] != 'Finished']
        
        finished_count = len(events) - len(events_to_save)
        print(f"   Eventos guardados (no Finished): {len(events_to_save)}")
        print(f"   Eventos excluidos (Finished): {finished_count}")
        
        if not events_to_save:
            print("No hay eventos para guardar")
            browser.close()
            return
        
        print(f"\nEventos guardados:")
        for i, e in enumerate(events_to_save, 1):
            print(f"   {i}. {e['title']} - {e['league']} - {e['status']}")
            print(f"      URL: {e['event_url']}")
        
        json_file = save_to_json(events_to_save)
        
        print(f"\n{'='*60}")
        print(" RESUMEN FINAL")
        print(f"{'='*60}")
        print(f" Eventos guardados: {len(events_to_save)}")
        print(f" Archivo: {json_file}")
        print(f"{'='*60}")
        
        browser.close()

if __name__ == "__main__":
    main()
