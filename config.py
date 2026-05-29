LEAGUES = {
    "belgium": {
        "name": "Jupiler Pro League",
        "country": "Belgium",
        "seed_club_slug": "genk-genk"
    },
    "korea": {
        "name": "K league 1",
        "country": "south korea",
        "seed_club_slug": "ulsan-ulsan"
    }

    # Esempi futuri, da attivare/modificare quando serviranno
    # "croatia": {
    #     "name": "HNL",
    #     "country": "Croatia",
    #     "seed_club_slug": "rijeka-rijeka"
    # },
    #
    # "germany2": {
    #     "name": "2. Bundesliga",
    #     "country": "Germany",
    #     "seed_club_slug": "paderborn-paderborn"
    # },
    #
    # "france2": {
    #     "name": "Ligue 2",
    #     "country": "France",
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
