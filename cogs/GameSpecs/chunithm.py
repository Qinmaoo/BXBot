import requests, json
import re
from cogs.GameSpecs.gamelist import game_list
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO  

top_amount = game_list["chunithm"]["pb_amount_in_top"]
old_amount = game_list["chunithm"]["pb_amount_in_old"]
new_amount = game_list["chunithm"]["pb_amount_in_new"]

def is_latest_ver(chart):
        versions = chart.get("versions", [])
        return (
            (len(versions) == 2 and "verse" in versions and "verse-omni" in versions) or
            (len(versions) == 4 and all(v in versions for v in ["verse", "verse-omni", "luminousplus-intl", "luminousplus-omni"]))
        )

difficulty_to_color = {
    "BASIC":"green",
    "ADVANCED":"yellow",
    "EXPERT":"red",
    "MASTER":"purple",
    "ULTIMA":"black",
}

class ChunithmScore:
    def __init__(self, score, songid, songname, diff, internal_level, rating, lamp, grade=""):
        self.score = score
        self.songid = songid
        self.songname = songname
        self.diff = diff
        self.internal_level = internal_level
        self.rating = rating
        self.lamp = lamp
        self.grade = grade
    
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
        scoredata = pb['scoreData']
        score = scoredata['score']
        lamp = scoredata['lamp']
        grade = scoredata['grade']
        songid = -1
        songname = entry["song"]['title']
        chart = entry["chart"]
        diff = chart['difficulty']
        internal_level = chart['levelNum']
        rating = pb["calculatedData"]["rating"]
        
        
        if is_latest_ver(chart):
            self.best_new.append(ChunithmScore(score, songid, songname, diff, internal_level, rating, lamp, grade))
            self.best_new = sorted(self.best_new, key=lambda x: x.rating, reverse=True)[:new_amount]
        else:
            self.best_old.append(ChunithmScore(score, songid, songname, diff, internal_level, rating, lamp, grade))
            self.best_old = sorted(self.best_old, key=lambda x: x.rating, reverse=True)[:old_amount]
            
        self.best_naive.append(ChunithmScore(score, songid, songname, diff, internal_level, rating, lamp, grade))
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
    
    def get_card(self, player_username, best_type="naive"):
        print("loading bg")
        background = Image.open(f"cogs/assets/scorecard_template/chunithm_{best_type}.png").convert("RGBA")
        print("bg loaded")
        
        print("loading game data covers")
        with open("cogs/GameSpecs/covers/chunithm.json", encoding="utf-8") as f:
            songs_data = json.load(f)
        print("game data loaded")
        
        font_upper = ImageFont.truetype("cogs/assets/fonts/FugazOne-Regular.ttf", 36)
        draw = ImageDraw.Draw(background)
        
        
        def edit_image(best, initial_x, intial_y, spacing_x, spacing_y, length_size_x, length_size_y, border_size):
            i=1
            x, y = initial_x, intial_y
            for score in best:
                safe_songname = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', score.songname)
                try:
                    overlay_image = Image.open(f'cogs/GameSpecs/covers/chunithm/{safe_songname}.png').convert("RGBA")
                except FileNotFoundError:
                    print("Fetching cover for", score)
                    image_url = songs_data[score.songname]["cover"]
                    img_data = requests.get(image_url).content
                    with open(f"cogs/GameSpecs/covers/chunithm/{safe_songname}.png", 'wb') as handler:
                        handler.write(img_data)
                    overlay_image = Image.open(f'cogs/GameSpecs/covers/chunithm/{safe_songname}.png').convert("RGBA")
                border_color = difficulty_to_color[score.diff]
                overlay_image = overlay_image.resize((length_size_x, length_size_y))
                overlay_image = ImageOps.expand(overlay_image, border=border_size, fill=border_color)
                
                background.paste(overlay_image, (x-border_size, y-border_size), overlay_image)
                draw.polygon([(x, y), (x+20, y), (x, y+20)], fill=border_color)
                
                font_position = ImageFont.truetype("cogs/assets/fonts/Montserrat-Black.ttf", 23)
                font_rating = ImageFont.truetype("cogs/assets/fonts/Montserrat-Black.ttf", 18)
                font_title = ImageFont.truetype("cogs/assets/fonts/Source-Han-Sans-CN-Bold.otf", 18)
                font_score = ImageFont.truetype("cogs/assets/fonts/din-condensed-bold.ttf", 21)
                
                
                #Position display
                content = f"#{i}"
                bbox = draw.textbbox((0, 0), content, font=font_position)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-61, x-5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                draw.text((text_x, y), content, fill="white", font=font_position)
                
                #CC display
                content = f"{score.internal_level:.1f}"
                bbox = draw.textbbox((0, 0), content, font=font_rating)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-61, x-5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                draw.text((text_x, y+42), content, fill="white", font=font_rating)
                
                # Triangle downwards
                triangle = [(x-40, y+68), (x-25, y+68), (x-32, y+78)]

                draw.polygon(triangle, fill="white")
                
                #Rating display
                content = f"{score.rating:.2f}"
                bbox = draw.textbbox((0, 0), content, font=font_rating)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-61, x-5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                draw.text((text_x, y+83), content, fill="white", font=font_rating)
                
                # Score display
                score_amount = f"{score.score}"
                text_width, _ = draw.textbbox((0, 0), score_amount, font=font_score)[2:]

                x_right = x + length_size_x - text_width - 3

                draw.rectangle([(x+15, y+72), (x+length_size_x, y+100)], fill=(0, 0, 0))
                draw.text((x+18, y+80), score.grade, fill="white", font=font_score)
                draw.text((x_right, y+80), score_amount, fill="white", font=font_score)
                
                
                # Title length cropping if necessary
                songname = score.songname
                
                bbox = font_title.getbbox(songname)
                text_width = bbox[2] - bbox[0]
                while text_width > 180:
                    songname = songname[:-1]
                    bbox = font_title.getbbox(songname)
                    text_width = bbox[2] - bbox[0]
                
                text_x = x - 61 + (182 - text_width) / 2
                
                draw.rectangle([(x-61, y+126), (x+length_size_x + border_size + 2, y+127)], fill="white")    #Separator
                draw.text((text_x, y+132), f"{songname}", fill="white", font=font_title)

                if i%5 == 0: 
                    x = 115
                    y += spacing_y + length_size_y
                else:
                    x += spacing_x + length_size_x
                i+=1
        
        spacing_x, spacing_y = 80, 54
        length_size_x, length_size_y = 115, 115
        border_size = 5  
              
        if best_type == "naive":
            # Player, ratings
            content = f"{player_username} - {self.get_naive_rating():.2f}rt"
            bbox = draw.textbbox((0, 0), content, font=font_upper)
            text_width = bbox[2] - bbox[0]

            rect_x1, rect_x2 = 254, 886
            text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
            draw.text((text_x, 100), content, fill="white", font=font_upper, stroke_width=3, stroke_fill="black")
            edit_image(self.best_naive, 115, 177, spacing_x, spacing_y, length_size_x, length_size_y, border_size)
        
        elif best_type == "ingame":
            # Player, ratings
            content = f"{player_username} - {self.get_ingame_rating():.2f}rt (Old {self.get_old_rating():.2f} / New {self.get_new_rating():.2f})"
            bbox = draw.textbbox((0, 0), content, font=font_upper)
            text_width = bbox[2] - bbox[0]

            rect_x1, rect_x2 = 254, 886
            text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
            draw.text((text_x, 100), content, fill="white", font=font_upper, stroke_width=3, stroke_fill="black")
            edit_image(self.best_old, 115, 177, spacing_x, spacing_y, length_size_x, length_size_y, border_size)
            edit_image(self.best_new, 115, 1235, spacing_x, spacing_y, length_size_x, length_size_y, border_size)
        
        return background