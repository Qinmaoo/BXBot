import requests, json
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO  
import os

difficulty_to_color = {
    "NOV":"blue",
    "ADV":"yellow",
    "EXH":"red",
    "MXM":"gray",
    "GRV":"brown",
    "VVD":"pink",
    "XCD":"blue",
    
}

def get_grade_color(grade):
    if grade == "S": return "#de5bdc"
    if grade == "AAA+": return "#f2f55f"
    if grade == "AAA": return "#e3a54d"
    if grade == "AA+": return "#e3a54d"
    if grade == "AA": return "#e3a54d"
    return "white"

def get_lamp_color(lamp):
    if lamp == "PUC": return "#f2f55f"
    if lamp == "UC": return "#e3a54d"
    if lamp == "EC": return "red"
    return "white"

name_whitelist = {
    "ANGER of the GOD":"ANGER of the GOD(EXIT TUNES)",
}

class SDVXScore:
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

class SDVXProfile:
    def __init__(self, player, best_naive = []):
        self.player = player
        self.api_url = f"https://kamai.tachi.ac/api/v1/users/{player}/games/sdvx/Single/pbs/all"
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
        rating = pb["calculatedData"]["VF6"]
            
        self.best_naive.append(SDVXScore(score, songid, songname, diff, internal_level, rating, lamp, grade))
        self.best_naive = sorted(self.best_naive, key=lambda x: x.rating, reverse=True)[:top_amount]

    def reload_pbs(self):
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
    
    def get_naive_rating(self):
        sum_of_ratings = 0
        for score in self.best_naive:
            sum_of_ratings += score.rating
        return sum_of_ratings
    
    def get_ingame_rating(self):
        return self.get_naive_rating()
    
    def get_card(self, player_username):
        print("loading bg")
        background = Image.open(f"cogs/assets/scorecard_template/sdvx.png").convert("RGBA")
        print("bg loaded")
        
        print("loading game data covers")
        with open("cogs/GameSpecs/covers/sdvx.json", encoding="utf-8") as f:
            songs_data = json.load(f)
        print("game data loaded")
        
        font_upper = ImageFont.truetype("cogs/assets/fonts/FugazOne-Regular.ttf", 36)
        draw = ImageDraw.Draw(background)
        
        
        def edit_image(best, initial_x, intial_y, spacing_x, spacing_y, length_size_x, length_size_y, border_size):
            i=1
            x, y = initial_x, intial_y
            for score in best:
                
                if score.songname in name_whitelist.keys():
                    score.songname = name_whitelist[score.songname]
                    
                safe_songname = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', score.songname)
                cover_folder_path = "cogs/GameSpecs/covers/sdvx"
                
                    
                if not os.path.isdir(cover_folder_path):
                    os.makedirs(cover_folder_path)
                
                try:
                    overlay_image = Image.open(f'{cover_folder_path}/{safe_songname}.png').convert("RGBA")
                except FileNotFoundError:
                    print("Fetching cover for", score)
                    try:
                        image_url = songs_data[score.songname]["cover"]
                    except KeyError:
                        sync_covers("sdvx")
                        image_url = songs_data[score.songname]["cover"]
                    
                    image_url = songs_data[score.songname]["cover"]
                    img_data = requests.get(image_url).content
                    with open(f"{cover_folder_path}/{safe_songname}.png", 'wb') as handler:
                        handler.write(img_data)
                    overlay_image = Image.open(f'{cover_folder_path}/{safe_songname}.png').convert("RGBA")
                border_color = difficulty_to_color[score.diff]
                overlay_image = overlay_image.resize((length_size_x, length_size_y))
                overlay_image = ImageOps.expand(overlay_image, border=border_size, fill=border_color)
                
                background.paste(overlay_image, (x-border_size, y-border_size), overlay_image)
                draw.rectangle([(x, y), (x+38,y+25)], fill=border_color)
                
                font_position = ImageFont.truetype("cogs/assets/fonts/Montserrat-Black.ttf", 23)
                font_rating = ImageFont.truetype("cogs/assets/fonts/Montserrat-Black.ttf", 18)
                font_title = ImageFont.truetype("cogs/assets/fonts/Source-Han-Sans-CN-Bold.otf", 18)
                font_score = ImageFont.truetype("cogs/assets/fonts/din-condensed-bold.ttf", 21)
                
                #CC display
                
                content = f"{score.diff[:3]} {score.internal_level}"
                bbox = draw.textbbox((0, 0), content, font=font_rating)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-border_size, x + text_width + 5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                
                draw.rectangle([(x, y), (x + text_width + 5,y+25)], fill=border_color)
                draw.text((text_x, y), content, fill="white", font=font_rating)
                
                #Position display
                content = f"#{i}"
                bbox = draw.textbbox((0, 0), content, font=font_position)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-65, x-5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                draw.text((text_x, y), content, fill="white", font=font_position)
                
                # Triangle downwards
                triangle = [(x-40, y+35), (x-30, y+35), (x-35, y+45)]

                draw.polygon(triangle, fill="white")
                
                #Rating display
                content = f"{score.rating}"
                bbox = draw.textbbox((0, 0), content, font=font_rating)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-65, x-5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                draw.text((text_x, y+53), content, fill="white", font=font_rating)
                
                # Lamp display
                if score.lamp in ['ULTIMATE CHAIN', "PERFECT ULTIMATE CHAIN", "EXCESSIVE CLEAR"]:
                    lamp = f"{''.join([x[0] for x in score.lamp.split(' ')])}"
                    
                    draw.rectangle([(x + length_size_x - 25, y+40), (x+length_size_x, y+68)], fill=(0, 0, 0))
                    draw.text((x + length_size_x - 20, y+46), lamp, fill=get_lamp_color(lamp), font=font_score)
                
                # Score display
                score_amount = f"{score.score}"
                grade = score.grade
                
                grade_width, _ = draw.textbbox((0, 0), grade, font=font_score)[2:]
                text_width, _ = draw.textbbox((0, 0), score_amount, font=font_score)[2:]

                x_right = x + length_size_x - text_width - 3
                
                grade_rect_x1, grade_rect_x2 = x+18, x_right
                grade_text_x = grade_rect_x1 + (grade_rect_x2 - grade_rect_x1 - grade_width) / 2
                
                draw.rectangle([(x+15, y+72), (x+length_size_x, y+100)], fill=(0, 0, 0))
                draw.text((grade_text_x, y+80), grade, fill=get_grade_color(grade), font=font_score)
                draw.text((x_right, y+80), score_amount, fill="white", font=font_score)
                
                
                # Title length cropping if necessary
                songname = score.songname
                
                bbox = font_title.getbbox(songname)
                text_width = bbox[2] - bbox[0]
                while text_width > 180:
                    songname = songname[:-1]
                    bbox = font_title.getbbox(songname)
                    text_width = bbox[2] - bbox[0]
                    
                # if text_width <= 115:
                #     text_x = x + (115 - text_width) / 2
                # else:
                #     text_x = x - 61 + (182 - text_width) / 2
                text_x = x - 61 + 182 - text_width
                
                draw.text((text_x, y+126), f"{songname}", fill="white", font=font_title)
                draw.rectangle([(x-61, y+148), (x+length_size_x + border_size + 2, y+149)], fill="white")    #Separator

                if i%5 == 0: 
                    x = 115
                    y += spacing_y + length_size_y
                else:
                    x += spacing_x + length_size_x
                i+=1
        
        spacing_x, spacing_y = 80, 54
        length_size_x, length_size_y = 115, 115
        border_size = 5  
              
        content = f"{player_username} - {self.get_naive_rating()}VF"
        bbox = draw.textbbox((0, 0), content, font=font_upper)
        text_width = bbox[2] - bbox[0]

        rect_x1, rect_x2 = 418, 840
        text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
        draw.text((text_x, 100), content, fill="white", font=font_upper, stroke_width=3, stroke_fill="black")
        edit_image(self.best_naive, 115, 177, spacing_x, spacing_y, length_size_x, length_size_y, border_size)
        
        return background
    

if __name__ == "__main__":
    from gamelist import game_list
    from sync_covers import sync_covers
    
    top_amount = game_list["sdvx"]["pb_amount_in_top"]
    
    kamai_username = "qinmao"
    display_username = "Qinmao"
    my_profile = SDVXProfile(kamai_username)
    
    my_profile.reload_pbs()
    
    # for x in my_profile.best_naive:
    #     print(x, x.lamp)
    # print(f"Total VF: {my_profile.get_naive_rating()} VF")
    
    background = my_profile.get_card(display_username)
    background.save(f"scorecard_output/resultat_SDVX_{display_username}.png")

else:
    from cogs.GameSpecs.gamelist import game_list
    from cogs.GameSpecs.sync_covers import sync_covers
    top_amount = game_list["sdvx"]["pb_amount_in_top"]
