import os
requests_import = __import__('requests')

# Carregar as Secrets do GitHub Actions
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# URL do seu painel no Render
PANEL_URL = "https://painel-voos.onrender.com/api/bot/rotas"

def buscar_todos_os_clientes():
    try:
        print(f"A carregar rotas de: {PANEL_URL}")
        response = requests_import.get(PANEL_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao buscar lista de rotas: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Falha de conexão com o painel web: {e}")
    return []

def enviar_telegram(chat_id, mensagem):
    if not chat_id:
        print("Aviso: Chat ID do Telegram não definido para este cliente.")
        return
        
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    body = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        response = requests_import.post(url_telegram, json=body)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso para o Telegram!")
        else:
            print(f"Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"Falha de conexão com o Telegram: {e}")

def verificar_voos_todos():
    print("A carregar rotas do painel web...")
    rotas_cadastradas = buscar_todos_os_clientes()
    
    if not rotas_cadastradas:
        print("Aviso: Nenhuma rota encontrada ou painel inacessível.")
        return

    print(f"Total de rotas a processar: {len(rotas_cadastradas)}")

    URL = "https://google-flights-scraper.p.rapidapi.com/api/flights/one-way"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "google-flights-scraper.p.rapidapi.com"
    }

    for rota in rotas_cadastradas:
        username = rota.get("username", "Desconhecido")
        origin = rota.get("origem", "GRU")
        destination = rota.get("destino", "MCZ")
        chat_id = rota.get("telegram_chat_id")
        
        raw_date = rota.get("data_voo")
        departure_date = raw_date.split("T")[0] if raw_date else "2026-12-31"
        max_stops = "nonstop"

        print(f"\n--- Processando rota de {username}: ({origin} -> {destination} em {departure_date}) ---")

        if not chat_id:
            print(f"Pulando {username}: Chat ID do Telegram não configurado para este cliente.")
            continue

        params = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "adults": 1,
            "cabin_class": "economy",
            "max_stops": max_stops,
            "currency": "BRL",
            "sort_by": "cheapest"
        }

        try:
            response = requests_import.get(URL, headers=headers, params=params)
            print(f"Status da API para {username}: {response.status_code}")
            
            if response.status_code == 200:
                dados = response.json()
                voos = dados.get("flights", [])
                
                if voos:
                    melhor_voo = voos[0]
                    preco = melhor_voo.get("price", "Sob consulta")
                    moeda = melhor_voo.get("currency", "BRL")
                    companhia = melhor_voo.get("airline_name", "Não informada")
                    
                    link_google_flights = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}+on+{departure_date}"
                    tipo_str = "Voo Direto ✈️" if max_stops == "nonstop" else "Com ou sem escala"
                    
                    mensagem = f"✈️ *Alerta de Voo para {username}*\n\n" \
                               f"📍 Rota: {origin} ➡️ {destination}\n" \
                               f"📅 Data: {departure_date}\n" \
                               f"🏢 Companhia: {companhia}\n" \
                               f"🔄 Tipo: {tipo_str}\n" \
                               f"💰 Menor Preço: {moeda} {preco}\n\n" \
                               f"🔗 [Ver Voo no Google Flights]({link_google_flights})"
                    
                    enviar_telegram(chat_id, mensagem)
                else:
                    print(f"Nenhum voo encontrado para {username}.")
            else:
                print(f"Erro na API para {username}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Erro na requisição para {username}: {e}")

if __name__ == "__main__":
    verificar_voos_todos()
