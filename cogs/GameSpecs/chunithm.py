import requests, json
from cogs.GameSpecs.gamelist import game_list
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO  

top_amount = game_list["chunithm"]["pb_amount_in_top"]
old_amount = game_list["chunithm"]["pb_amount_in_old"]
new_amount = game_list["chunithm"]["pb_amount_in_new"]

def is_verse_chart(chart):
        versions = chart.get("versions", [])
        return (
            (len(versions) == 2 and "verse" in versions and "verse-omni" in versions) or
            (len(versions) == 4 and all(v in versions for v in ["verse", "verse-omni", "luminousplus-intl", "luminousplus-omni"]))
        )
    
class ChunithmScore:
    def __init__(self, score, songid, songname, diff, internal_level, rating, lamp):
        self.score = score
        self.songid = songid
        self.songname = songname
        self.diff = diff
        self.internal_level = internal_level
        self.rating = rating
        self.lamp = lamp
    
    def __str__(self):
        return f"{self.songname} [{self.diff[:3]} {self.internal_level}] - {self.score} ({self.rating})"

class ChunithmProfile:
    def __init__(self, player, best_old = [], best_new = [], best_naive = []):
        self.player = player
        self.api_url = f"https://kamai.tachi.ac/api/v1/users/{player}/games/chunithm/Single/pbs/all"
        self.best_old = best_old
        self.best_new = best_new
        self.best_naive = best_naive
        
    def add_pb(self, entry):
        pb = entry["pb"]
        score = pb['scoreData']['score']
        lamp = pb['scoreData']['lamp']
        songid = -1
        songname = entry["song"]['title']
        chart = entry["chart"]
        diff = chart['difficulty']
        internal_level = chart['levelNum']
        rating = pb["calculatedData"]["rating"]
        
        if is_verse_chart(chart):
            self.best_new.append(ChunithmScore(score, songid, songname, diff, internal_level, rating, lamp))
            self.best_new = sorted(self.best_new, key=lambda x: x.rating, reverse=True)[:new_amount]
        else:
            self.best_old.append(ChunithmScore(score, songid, songname, diff, internal_level, rating, lamp))
            self.best_old = sorted(self.best_old, key=lambda x: x.rating, reverse=True)[:old_amount]
            
        self.best_naive.append(ChunithmScore(score, songid, songname, diff, internal_level, rating, lamp))
        self.best_naive = sorted(self.best_naive, key=lambda x: x.rating, reverse=True)[:top_amount]

    def reload_pbs(self):
        self.best_old = []
        self.best_new = []
        self.best_naive = []
        try:
            response = requests.get(self.api_url)
            data = response.json()
            pbs = data["body"]["pbs"]
            charts = data["body"]["charts"]
            songs = data["body"]["songs"]

            for pb in pbs:
                chart = next((c for c in charts if c["chartID"] == pb["chartID"]), None)
                song = next((s for s in songs if s["id"] == pb["songID"]), None)

                if not chart:
                    continue
                
                entry = {"pb": pb, "song": song, "chart": chart}
                self.add_pb(entry)

        except Exception as e:
            print("Error fetching data:", e)
    
    def get_new_rating(self):
        sum_of_ratings = 0
        for score in self.best_new:
            sum_of_ratings += score.rating
        new_rating = round(sum_of_ratings/new_amount,2)
        return new_rating
    
    def get_old_rating(self):
        sum_of_ratings = 0
        for score in self.best_old:
            sum_of_ratings += score.rating
        old_rating = round(sum_of_ratings/old_amount,2)
        return old_rating
    
    def get_naive_rating(self):
        sum_of_ratings = 0
        for score in self.best_naive:
            sum_of_ratings += score.rating
        naive_rating = round(sum_of_ratings/top_amount,2)
        return naive_rating
    
    def get_ingame_rating(self):
        new_rating = self.get_new_rating()
        old_rating = self.get_old_rating()

        ingame_rating = round((new_rating*new_amount + old_rating*old_amount)/50,2)
        return ingame_rating
    
    def get_card(self, best_type="naive"):
        background = Image.open(f"cogs/GameSpecs/assets/scorecard_template/chunithm_{best_type}.png").convert("RGBA")
        with open("cogs/GameSpecs/covers/chunithm.json") as f:
            songs_data = json.load()
            
        if best_type == "naive":
            pass
        elif best_type == "ingame":
            for score in self.best_old:
                # 2️⃣ Charger une image depuis une URL
                image_url = songs_data[score.songname]["cover"]
                response = requests.get(image_url)
                overlay_image = Image.open(BytesIO(response.content)).convert("RGBA")

                # 4️⃣ Coller l'image téléchargée sur l'image de fond
                background.paste(overlay_image, (50, 50), overlay_image)

                # 5️⃣ Ajouter du texte
                draw = ImageDraw.Draw(background)

                # Charger une police (à adapter avec un chemin valide ou une police système)
                font = ImageFont.truetype("cogs/assets/fonts/Exo-medium.ttf", 40)

                # Ajouter le texte
                draw.text((200, 50), "Hello World!", fill="white", font=font)

                # 6️⃣ Sauvegarder le résultat
        background.save("resultat.png")