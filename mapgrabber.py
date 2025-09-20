#e

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string
import json
config=[]
with open("config.json", mode="r", encoding="utf-8") as read_file:
        config = json.load(read_file)

def reload_config():
    global config
    with open("config.json", mode="r", encoding="utf-8") as read_file:
        config = json.load(read_file)

#response = requests.get("https://www.scrapethissite.com/pages/simple/")
response = requests.get("http://map.townthrive.xyz:2082/tiles/players.json")
print (response.json())
print(response.json().keys())
def get_players():
    players = []
    for player in response.json().get("players", []):
        players.append({
            "name": player.get("name"),
            "x": player.get("x"),
            "y": player.get("y"),
            "z": player.get("z")
        })
    return players
x=0
y=0
z=0
def check_player_presence(bound1=[x,y,z], bound2=[x,y,z]):
    players = get_players()
    present_players = []
    for player in players:
        if (bound1[0] <= player["x"] <= bound2[0] and
            bound1[1] <= player["y"] <= bound2[1] and
            bound1[2] <= player["z"] <= bound2[2]):
            present_players.append(player)
    return present_players
def filter_whitelist(present_players, region_name="spawn"):
    whitelist = config.get("whitelist", [])
    filtered_players = [player for player in present_players if player["name"] not in whitelist]
    return filtered_players
def check_all_regions():
    detectedplayers = []
    for region_name in config.get("regions", {}):
        detectedplayers.append(check_region_presence(region_name))
    return detectedplayers
        
def check_region_presence(region_name="spawn"):
    regions = config.get("regions", {})
    if region_name not in regions:
        return []
    bound1 = regions[region_name]["bound1"]
    bound2 = regions[region_name]["bound2"]
    return check_player_presence(bound1, bound2)

