import requests
import csv
import datetime

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

# Función para obtener los datos de la liga (división y LP)
def get_league_data(summoner_id):
    url = f"https://la1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    headers = {"X-Riot-Token": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()  # Devuelve los datos de la liga
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de liga para el summoner {summoner_id}: {e}")
        return None

# Lista de summoner names y tags
summoners = [
    {"name": "Rocoto", "tag": "2817"},
    {"name": "Jaz1725", "tag": "LAN"},
    {"name": "Snixx", "tag": "LAN"}
]

# Obtener el PUUID y datos adicionales para cada summoner
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
                # Obtener los datos de la liga
                summoner_id = summoner_data.get("id", "")
                league_data = get_league_data(summoner_id)
                
                # Obtener la fecha actual de ejecución
                execution_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if league_data:
                    # Extraer los datos de división y LP
                    for league in league_data:
                        results.append({
                            "name": name,
                            "tag": tag,
                            "summoner_id": summoner_data.get("id", ""),
                            "summoner_level": summoner_data.get("summonerLevel", ""),
                            "puuid": puuid,
                            "division": league.get("tier", ""),
                            "rank": league.get("rank", ""),
                            "lp": league.get("leaguePoints", ""),
                            "date_executed": execution_date
                        })
                else:
                    results.append({
                        "name": name,
                        "tag": tag,
                        "summoner_id": summoner_data.get("id", ""),
                        "summoner_level": summoner_data.get("summonerLevel", ""),
                        "puuid": puuid,
                        "division": "No data",
                        "rank": "No data",
                        "lp": "No data",
                        "date_executed": execution_date
                    })
            else:
                results.append({"name": name, "tag": tag, "error": "Error al obtener datos"})
        else:
            results.append({"name": name, "tag": tag, "error": "Error al obtener PUUID"})
    return results

# Guardar los resultados en un archivo CSV
def save_to_csv(data, filename="summoner_data.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["name", "tag", "summoner_id", "summoner_level", "puuid", "division", "rank", "lp", "date_executed", "error"])
        writer.writeheader()  # Escribir los encabezados
        writer.writerows(data)  # Escribir los datos

# Ejecutar y guardar los resultados
if __name__ == "__main__":
    summoner_info = fetch_summoner_info(summoners)
    save_to_csv(summoner_info)
    print(f"Datos guardados en 'summoner_data.csv'")
