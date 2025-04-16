from gamelist import game_list
import requests, json

for gameid, gamedata in game_list.items():
    print(gameid, "\n")
    game_json = {}
    url = f"https://dp4p6x0xfi5o9.cloudfront.net/{gamedata['name_in_url_ztk']}/data.json"
    response = requests.get(url)
    if response.status_code == 200:
        songs = response.json()["songs"] 
        for song in songs:
            song_id = song["songId"]
            song_title = song["title"]
            image_url = f"https://dp4p6x0xfi5o9.cloudfront.net/{gamedata['name_in_url_ztk']}/img/cover/" + song["imageName"]
            game_json[song_id] = {"title":song_title, "cover":image_url}

        with open(f"cogs/GameSpecs/covers/{gameid}.json", "w", encoding="utf-8") as f:
            json.dump(game_json, f)
    else:
        print("Erreur :", response.status_code)
    print("\n\n")