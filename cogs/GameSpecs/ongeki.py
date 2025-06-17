import requests, json
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO  
import os

from math import floor

def truncate(f, n):
    return int(f * 10**n) / 10**n


def is_latest_ver(chart):
        version = chart["data"]["displayVersion"]
        return version == "オンゲキ Re:Fresh"

difficulty_to_color = {
    "BASIC":"green",
    "ADVANCED":"yellow",
    "EXPERT":"red",
    "MASTER":"purple",
    "LUNATIC":"white",
}

def get_grade_color(grade):
    if grade == "SSS+": return "#de5bdc"
    if grade == "SSS": return "#f2f55f"
    if grade == "SS+": return "#e3a54d"
    if grade == "SS": return "#e3a54d"
    if grade == "S+": return "#e3a54d"
    if grade == "S": return "#e3a54d"
    return "white"

def get_lamp_color(lamp):
    if lamp == "AJ": return "#f2f55f"
    if lamp == "FC": return "#e3a54d"
    return "white"

def score_coefficient_function(x):
    points = [
        (800000, -6000),
        (900000, -4000),
        (970000,  0),
        (990000,  750),
        (1000000, 1250),
        (1007500, 1750),
        (1010000, 2000)
    ]

    if x <= points[0][0]:
        return -6000
    else:
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            if x0 <= x <= x1:
                break

    y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return y

def get_rating(internal_level, score, grade, bell_lamp, combo_lamp):
    grade_bonus_association = {
        "SS": 100,
        "SSS": 200,
        "SSS+": 300
    }
    if grade in grade_bonus_association.keys(): grade_bonus = grade_bonus_association[grade]
    else: grade_bonus = 0
    
    if bell_lamp == "FULL BELL": bell_bonus = 50
    else: bell_bonus = 0
    
    combo_bonus_association = {
        "FULL COMBO": 100,
        "ALL BREAK": 300,
        "ALL BREAK+": 350
    }
    if combo_lamp in combo_bonus_association.keys(): combo_bonus = combo_bonus_association[combo_lamp]
    else: combo_bonus = 0
    
    if score <= 500000: return 0
    
    score_coefficient = score_coefficient_function(score)
    
    if score < 800000: return (internal_level - 6)*(score-500000)/300000
    
    score_rating = max(0, internal_level*1000 + score_coefficient + grade_bonus + bell_bonus + combo_bonus)
    score_rating = score_rating
    return floor(score_rating)

def get_starrating(songname, platscore, max_platscore, internal_level):
    platscore_ratio = platscore/max_platscore
        
    if platscore_ratio < 0.94: stars = 0
    elif platscore_ratio < 0.95: stars = 1
    elif platscore_ratio < 0.96: stars = 2
    elif platscore_ratio < 0.97: stars = 3
    elif platscore_ratio < 0.98: stars = 4
    else: stars = 5
    
    starrating = truncate(stars*(internal_level**2), 3)
    # if starrating != 0.0: print(f"{songname} ({internal_level}): {platscore} / {max_platscore} - {stars}* - {starrating}")
    return floor(starrating)



class OngekiScore:
    def __init__(self, score, starrating, songid, songname, diff, internal_level, rating, lamp, grade=""):
        self.score = score
        self.starrating = starrating
        self.songid = songid
        self.songname = songname
        self.diff = diff
        self.internal_level = internal_level
        self.rating = rating
        self.lamp = lamp
        self.grade = grade
    
    def __str__(self):
        return f"{self.songname} [{self.diff[:3]} {self.internal_level}] - {self.score} ({self.rating})"

class OngekiProfile:
    def __init__(self, player, best_old = [], best_new = [], best_naive = [], best_star = []):
        self.player = player
        self.api_url = f"https://kamai.tachi.ac/api/v1/users/{player}/games/ongeki/Single/pbs/all"
        self.best_old = best_old
        self.best_new = best_new
        self.best_star = best_star
        self.best_naive = best_naive
        
    def add_pb(self, entry):
        pb = entry["pb"]
        scoredata = pb['scoreData']
        score = scoredata['score']
        platscore = scoredata['optional']["platScore"]
        lamp = scoredata['noteLamp']
        grade = scoredata['grade']
        songid = pb["songID"]
        songname = entry["song"]['title']
        chart = entry["chart"]
        diff = chart['difficulty']
        internal_level = chart['levelNum']
        bell_lamp = scoredata["bellLamp"]
        combo_lamp = scoredata["noteLamp"]
        rating = get_rating(internal_level, score, grade, bell_lamp, combo_lamp)
        # rating = pb["calculatedData"]["rating"]
        
        max_platscore = chart["data"]["maxPlatScore"]
        
        starrating = get_starrating(songname, platscore, max_platscore, internal_level)
        
        if is_latest_ver(chart):
            self.best_new.append(OngekiScore(score, starrating, songid, songname, diff, internal_level, rating, lamp, grade))
            self.best_new = sorted(self.best_new, key=lambda x: x.rating, reverse=True)[:new_amount]
        else:
            self.best_old.append(OngekiScore(score, starrating, songid, songname, diff, internal_level, rating, lamp, grade))
            self.best_old = sorted(self.best_old, key=lambda x: x.rating, reverse=True)[:old_amount]
            
        self.best_naive.append(OngekiScore(score, starrating, songid, songname, diff, internal_level, rating, lamp, grade))
        self.best_naive = sorted(self.best_naive, key=lambda x: x.rating, reverse=True)[:top_amount]
        
        self.best_star.append(OngekiScore(score, starrating, songid, songname, diff, internal_level, rating, lamp, grade))
        self.best_star = sorted(self.best_star, key=lambda x: x.starrating, reverse=True)[:star_rating_amount]

    def reload_pbs(self):
        self.best_old = []
        self.best_new = []
        self.best_naive = []
        self.best_star = []
        
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
            sum_of_ratings += 2*score.rating
        new_rating = sum_of_ratings/new_amount
        return floor(new_rating/10)
    
    def get_old_rating(self):
        sum_of_ratings = 0
        for score in self.best_old:
            sum_of_ratings += score.rating
        old_rating = sum_of_ratings/old_amount
        return floor(old_rating)
    
    def get_star_rating(self):
        sum_of_ratings = 0
        for score in self.best_star:
            sum_of_ratings += score.starrating
        star_rating = sum_of_ratings/star_rating_amount
        return floor(star_rating)
    
    def get_naive_rating(self):
        sum_of_ratings = 0
        for score in self.best_naive:
            sum_of_ratings += score.rating
        naive_rating = truncate(sum_of_ratings/top_amount,2)
        print('naiverate', naive_rating)
        
        return naive_rating
    
    def get_ingame_rating(self):
        new_rating = self.get_new_rating()
        old_rating = self.get_old_rating()
        star_rating = self.get_star_rating()

        ingame_rating = new_rating + old_rating + star_rating
        ingame_rating /= 1000
        print("new rt", new_rating/1000, "old rt", old_rating/1000, "star rt", star_rating/1000)
        print("ingame rt", ingame_rating)
        return ingame_rating
    
    def print_bests(self):
        print("best old")
        i = 1
        for e in self.best_old:
            print(f"#{i} {e.songname} [{e.diff} {e.internal_level}] - {e.score} ({e.grade} - {e.lamp} - {e.rating})")
            i+=1
        
        print("\n\nbest new")
        i=1
        for e in self.best_new:
            print(f"#{i} {e.songname} [{e.diff} {e.internal_level}] - {e.score} ({e.grade} - {e.lamp} - {e.rating})")
            i+=1
            
        print("\n\nbest star")
        i=1
        for e in self.best_star:
            print(f"#{i} {e.songname} [{e.diff} {e.internal_level}] - {e.score} ({e.grade} - {e.starrating} - {e.lamp} - {e.rating})")
            i+=1
            
    def get_card(self, player_username, best_type="naive"):
        print("loading bg")
        background = Image.open(f"cogs/assets/scorecard_template/ongeki_{best_type}.png").convert("RGBA")
        print("bg loaded")
        
        print("loading game data covers")
        with open("cogs/GameSpecs/covers/ongeki.json", encoding="utf-8") as f:
            songs_data = json.load(f)
        print("game data loaded")
        
        font_upper = ImageFont.truetype("cogs/assets/fonts/FugazOne-Regular.ttf", 36)
        draw = ImageDraw.Draw(background)
        
        
        def edit_image(best, initial_x, intial_y, spacing_x, spacing_y, length_size_x, length_size_y, border_size):
            i=1
            x, y = initial_x, intial_y
            for score in best:
                safe_songname = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', score.songname)
                cover_folder_path = "cogs/GameSpecs/covers/ongeki"
                
                if not os.path.isdir(cover_folder_path):
                    os.makedirs(cover_folder_path)
                
                try:
                    overlay_image = Image.open(f'{cover_folder_path}/{safe_songname}.png').convert("RGBA")
                except FileNotFoundError:
                    print("Fetching cover for", score)
                    try:
                        image_url = songs_data[score.songname]["cover"]
                        img_data = requests.get(image_url).content
                        with open(f"{cover_folder_path}/{safe_songname}.png", 'wb') as handler:
                            handler.write(img_data)
                    except KeyError:
                        sync_covers("ongeki")
                        try:
                            image_url = songs_data[score.songname]["cover"]
                            img_data = requests.get(image_url).content
                            with open(f"{cover_folder_path}/{safe_songname}.png", 'wb') as handler:
                                handler.write(img_data)
                        except KeyError:
                            safe_songname = "default_icon"
                    
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
                content = f"{score.internal_level:.1f}"
                bbox = draw.textbbox((0, 0), content, font=font_rating)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-border_size, x+38
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
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
                content = f"{score.rating:.2f}"
                bbox = draw.textbbox((0, 0), content, font=font_rating)
                text_width = bbox[2] - bbox[0]

                rect_x1, rect_x2 = x-65, x-5
                text_x = rect_x1 + (rect_x2 - rect_x1 - text_width) / 2
                draw.text((text_x, y+53), content, fill="white", font=font_rating)
                
                # Lamp display
                if score.lamp in ['FULL COMBO', "ALL JUSTICE"]:
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
    

if __name__ == "__main__":
    from gamelist import game_list
    from sync_covers import sync_covers
    top_amount = game_list["ongeki"]["pb_amount_in_top"]
    old_amount = game_list["ongeki"]["pb_amount_in_old"]
    new_amount = game_list["ongeki"]["pb_amount_in_new"]
    star_rating_amount = 50
    
    # print(get_rating(13.8, 1009135 , "SSS+","FULL BELL","ALL BREAK"))
    # print(get_starrating("test", 2592, 3492, 14.2))
    
    kamai_username = "lisieshy"
    display_username = "Twis"
    my_profile = OngekiProfile(kamai_username)
    my_profile.reload_pbs()
    
    my_profile.print_bests()
    print("")
    my_profile.get_ingame_rating()
    
    # background_naive = my_profile.get_card(display_username, "naive")
    # background_ingame = my_profile.get_card(display_username, "ingame")
    # background_naive.save(f"scorecard_output/resultat_naive_ongeki_{display_username}.png")

else:
    from cogs.GameSpecs.gamelist import game_list
    from cogs.GameSpecs.sync_covers import sync_covers
    top_amount = game_list["ongeki"]["pb_amount_in_top"]
    old_amount = game_list["ongeki"]["pb_amount_in_old"]
    new_amount = game_list["ongeki"]["pb_amount_in_new"]
    star_rating_amount = 50
