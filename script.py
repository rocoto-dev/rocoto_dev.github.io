import requests
import pandas as pd
import os
import matplotlib.pyplot as plt

# Tu API Key de Riot
API_KEY = "RGAPI-0108ce4b-bf84-4e58-a1b6-d917882092b2"

# Función para obtener el PUUID
def get_puuid(summoner_name, tag):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tag}"
    headers = {"X-Riot-Token": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza una excepción si el código de estado no es 200
        data = response.json()
        return data.get("puuid", None)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener PUUID para {summoner_name}#{tag}: {e}")
        return None

# Función para obtener datos adicionales usando el PUUID
def get_summoner_data(puuid):
    url = f"https://la1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()  # Devuelve todos los datos del invocador
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos para el PUUID {puuid}: {e}")
        return None

# Función para obtener datos de división
def get_league_data(summoner_id):
    url = f"https://la1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    headers = {"X-Riot-Token": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de liga para {summoner_id}: {e}")
        return None

# Lista de summoner names y tags
summoners = [
    {"name": "Rocoto", "tag": "2817"},
    {"name": "Jaz1725", "tag": "LAN"},
    {"name": "Snixx", "tag": "LAN"}
]

# Función para leer datos históricos del CSV (si existe)
def read_existing_csv(filename="docs/summoner_data.csv"):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=["name", "tag", "summoner_id", "summoner_level", "puuid", "division", "rank", "lp", "error", "date"])

# Función para convertir las divisiones y LP a un valor numérico
def division_to_numeric(division, rank, lp):
    division_order = {
        "Iron": 0,
        "Bronze": 10,
        "Silver": 20,
        "Gold": 30,
        "Platinum": 40,
        "Emerald": 50,
        "Diamond": 60,
        "Master": 70,
        "GrandMaster": 80,
        "Challenger": 90
    }

    rank_order = {
        "IV": 0,
        "III": 1,
        "II": 2,
        "I": 3
    }
    
    # Asumimos que cada división tiene un LP de 100 para pasar a la siguiente división
    division_value = division_order.get(division, 0)
    rank_value = rank_order.get(rank, 0)
    
    # Cada LP sube el valor del rango de la división, lo que permite un valor numérico en una escala continua
    return division_value + rank_value + (lp / 100)  # LP divide por 100 para que entre en la escala de 0 a 1 dentro de la división

# Obtener el PUUID, datos adicionales y de liga para cada summoner
def fetch_summoner_info(summoners):
    results = []
    for summoner in summoners:
        name = summoner["name"]
        tag = summoner["tag"]
        print(f"Obteniendo PUUID para {name}#{tag}...")
        puuid = get_puuid(name, tag)
        if puuid:
            print(f"Obteniendo datos adicionales para el PUUID {puuid}...")
            summoner_data = get_summoner_data(puuid)
            if summoner_data:
                # Obtener datos de liga
                summoner_id = summoner_data.get("id", "")
                league_data = get_league_data(summoner_id)
                
                # Agregar los datos relevantes al resultado
                division = league_data[0].get("tier", "Unknown") if league_data else "Unknown"
                rank = league_data[0].get("rank", "Unknown") if league_data else "Unknown"
                lp = league_data[0].get("leaguePoints", 0) if league_data else 0
                numeric_value = division_to_numeric(division, rank, lp)
                
                # Usar la fecha actual y unificada como el campo 'date'
                date_today = pd.Timestamp.now().strftime('%Y-%m-%d')  # Solo la fecha (sin hora)
                
                results.append({
                    "name": name,
                    "tag": tag,
                    "summoner_id": summoner_data.get("id", ""),
                    "summoner_level": summoner_data.get("summonerLevel", ""),
                    "puuid": puuid,
                    "division": division,
                    "rank": rank,
                    "lp": lp,
                    "numeric_value": numeric_value,
                    "date": date_today  # Fecha unificada
                })
            else:
                results.append({"name": name, "tag": tag, "error": "Error al obtener datos", "date": pd.Timestamp.now().strftime('%Y-%m-%d')})
        else:
            results.append({"name": name, "tag": tag, "error": "Error al obtener PUUID", "date": pd.Timestamp.now().strftime('%Y-%m-%d')})
    return results

# Guardar los resultados combinados (datos históricos + nuevos) en el mismo archivo CSV
def save_to_csv(data, filename="docs/summoner_data.csv"):
    # Leer los datos existentes
    existing_data = read_existing_csv(filename)
    
    # Convertir los nuevos datos a un DataFrame
    new_data = pd.DataFrame(data)
    
    # Concatenar los datos existentes con los nuevos
    combined_data = pd.concat([existing_data, new_data], ignore_index=True)
    
    # Guardar los datos combinados de nuevo en el archivo CSV
    combined_data.to_csv(filename, index=False)

# Generar un gráfico de líneas y guardarlo como imagen PNG
def generate_graph(data, filename="docs/summoner_graph.png"):
    df = pd.DataFrame(data)
    plt.figure(figsize=(10, 6))
    
    # Convertir la fecha a un formato adecuado para el eje X
    df['date'] = pd.to_datetime(df['date']).dt.date  # Solo la fecha sin la hora
    
    # Graficar
    for summoner_name in df['name'].unique():
        summoner_data = df[df['name'] == summoner_name]
        plt.plot(summoner_data['date'], summoner_data['numeric_value'], label=summoner_name)
    
    plt.title("Progreso de LP y Divisiones de los Invocadores")
    plt.xlabel('Fecha')
    plt.ylabel('Combinación de División y LP')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.savefig(filename)  # Guardar el gráfico como archivo PNG

# Ejecutar y guardar los resultados
if __name__ == "__main__":
    summoner_info = fetch_summoner_info(summoners)
    save_to_csv(summoner_info)  # Guardar los datos combinados en el CSV
    final_data = read_existing_csv()
    generate_graph(final_data)  # Generar el gráfico de líneas y guardarlo como imagen
    print(f"Datos guardados en 'summoner_data.csv' y gráfico en 'summoner_graph.png'")
