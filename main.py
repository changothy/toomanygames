import requests, json
import locale
import configparser

locale.setlocale(locale.LC_ALL, '')

config = configparser.ConfigParser()
config.read("config.txt")
STEAM_API_KEY = config.get("API", "API_key")
STEAM_ID = config.get("API", "steamid")

### Too many games ###

api_request_getgamelist = "https://api.steampowered.com/ISteamApps/GetAppList/v2/?"  ## Retrieves all games in the Steam DB
api_request_getusergames = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + STEAM_API_KEY + "&steamid=" + STEAM_ID + "&include_played_free_games=1&include_appinfo=1&format=json"  ## Retrieves games owned by a user
api_request_getpricelist = "https://store.steampowered.com/api/appdetails?filters=price_overview&appids="  ## Retrieves price information on games (takes a CSV list of appids)
#  http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid=320&key=STEAM_API_KEY&steamid=STEAM_ID

## Print text explaning what this is all about ##
print("You have too many games. Let's show some stats.")

## Confirm accounts ##
print("(Make sure you update accounts.json to connect to services that apply to you.)")

## Takes a request URL and calls an API. Returns response
def get_response(request_url):
    #print("Attempting API call: " + request_url)
    response = requests.get(request_url)
    return response

## Return a dict of the data in the playerservice response
def get_response_json_dict(response):
    json_dict = response.json()
    return json_dict

## Take a list and split it into a list of several sublists, in blocks of n entries
## The API can't handle high numbers of appids - this method helps split the list into blocks to spread over multiple API calls
def split_list(list, n):
    for i in range(0, len(list), n):
        yield list[i:i+n]


response = get_response(api_request_getusergames)
#print(response.status_code)
#print(response.json())
user_data = get_response_json_dict(response).get("response")

## Print results ##
## Count games
game_count = user_data.get("game_count")
print("You have", game_count, "games (including free games).")

## Calculate total account value
owned_games_list = user_data.get("games")
owned_games_appids_list = list(split_list([owned_games_appids['appid'] for owned_games_appids in owned_games_list], 500))
owned_games_pricelist_dict = {}

for lst in owned_games_appids_list:
    owned_games_appids_str = ",".join(str(i) for i in lst)
    response = get_response(api_request_getpricelist + owned_games_appids_str)
    if owned_games_pricelist_dict:
        owned_games_pricelist_dict.update(get_response_json_dict(response))
    else:
        owned_games_pricelist_dict = get_response_json_dict(response)

total_value = 0

## Get final value (read: after discounts) of each owned game and sum the total
for key, value in owned_games_pricelist_dict.items():
    #total_value = total_value + game["data"["final"]]
    #if (game.get("price_overview")):
    #print("checking " + key)
    if value.get("success") == True and len(value.get("data")) != 0:
        #print(value.get("data", {}).get("price_overview", {}).get("final"))
        total_value = total_value + value.get("data", {}).get("price_overview", {}).get("final")
    

    #print(owned_games_pricelist_dict[game]["data"]["price_overview"])

## Value is in cents, convert to dollars
total_value = total_value / 100

print("Total market value of Steam Library (including current discounts): " + locale.currency(total_value, grouping = True))


## Highlight games that have been played for less than an hour
less_played_games_list = []
total_played_hours = 0 ## Also get total played hours while we're at it
for dict_entry in user_data.get("games"):
    total_played_hours = total_played_hours + dict_entry.get("playtime_forever")
    if dict_entry.get("playtime_forever") < 60:
        less_played_games_list.append(dict_entry.get("appid"))

#print(less_played_games_list)
print("You have", len(less_played_games_list), "games with a play time of less than an hour.")
print("You've played a total of", round(total_played_hours/60), "hours in your Steam library.")

## Show 10 most played games, with hours as a percentage of game time
games_list_playtime_sorted = sorted(user_data.get("games"), key=lambda d: d["playtime_forever"], reverse=True)
most_played_games_list = games_list_playtime_sorted[0:10]
print("Your 10 most played games are:")
count = 0
most_played_games_hours = 0
for count, item in enumerate(most_played_games_list, start=1):
    print(count, item["name"], "—", round(item["playtime_forever"]/60), "hours")
    most_played_games_hours = most_played_games_hours + item["playtime_forever"]

print("These games represent", str(round((most_played_games_hours/total_played_hours)*100, 2)) + "%", "of your total play time.")

# generate web page?