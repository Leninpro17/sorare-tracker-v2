# config.py - Configurazione ufficiale Sorare Tracker (Stagione 2026/2027)

LEAGUES = {
    "laliga": {
        "name": "LaLiga EA Sports",
        "country": "Spain",
        "competition_slug": "laliga-es",       # Slug ufficiale validato
        "seed_club_slug": "real-madrid-madrid" # Slug ufficiale del club seed
    },
    "belgium": {
        "name": "Jupiler Pro League",
        "country": "Belgium",
        "competition_slug": "jupiler-pro-league", # Slug ufficiale validato
        "seed_club_slug": "club-brugge-brugge"     # Slug ufficiale del club seed
    },
    "france": {
        "name": "Ligue 1",
        "country": "France",
        "competition_slug": "ligue-1-fr",        # Slug ufficiale validato
        "seed_club_slug": "paris-saint-germain-paris" # Slug ufficiale del club seed
    },
    "scotland": {
        "name": "Scottish Premiership",
        "country": "Scotland",
        "competition_slug": "premiership-gb-sct", # Slug ufficiale validato
        "seed_club_slug": "celtic-glasgow"       # Slug ufficiale del club seed
    },
    "croatia": {
        "name": "HNL",
        "country": "Croatia",
        "competition_slug": "1-hnl",             # Slug ufficiale validato
        "seed_club_slug": "dinamo-zagreb-zagreb" # Slug ufficiale del club seed
    },
    "korea": {
        "name": "K league 1",
        "country": "South Korea",
        "competition_slug": "k-league-1",        # Mantenuto come riferimento standard
        "seed_club_slug": "ulsan-ulsan"
    }

    # Esempi futuri, da attivare/modificare quando serviranno
    # "germany2": {
    #     "name": "2. Bundesliga",
    #     "country": "Germany",
    #     "competition_slug": "2-bundesliga",
    #     "seed_club_slug": "paderborn-paderborn"
    # },
    # "france2": {
    #     "name": "Ligue 2",
    #     "country": "France",
    #     "competition_slug": "ligue-2",
    #     "seed_club_slug": "troyes-troyes"
    # }
}


PRICE_CONVERSION = {
    # Valori manuali modificabili.
    # Servono solo per confrontare i floor in una valuta unica.
    "USD_TO_EUR": 0.92,
    "ETH_TO_EUR": 3000
}


def get_data_dir(league_key, season_start_year):
    return f"data/{league_key}/{season_start_year}"


def get_club_list_file(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/club_list.json"


def get_player_data_file(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/player_data.json"


def get_player_metrics_file(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/player_metrics_latest.json"


def get_player_prices_file(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/player_prices_latest.json"


def get_gw_projection_file(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/gw_projection_latest.json"


def get_buy_signals_file(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/buy_signals_latest.json"


def get_reports_dir(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/reports"


def get_snapshots_dir(league_key, season_start_year):
    return f"{get_data_dir(league_key, season_start_year)}/snapshots"
