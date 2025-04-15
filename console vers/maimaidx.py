import requests

def is_latest_ver_chart(chart):
    return (chart["data"]["displayVersion"] == "maimaiでらっくす PRISM PLUS")
    
class MaimaiDXScore:
    def __init__(self, score, songid, songname, diff, internal_level, rating, lamp):
        self.score = score
        self.songid = songid
        self.songname = songname
        self.diff = diff
        self.internal_level = internal_level
        self.rating = rating
        self.lamp = lamp
    
    def __str__(self):
        diff = self.diff.split(' ')
        if len(diff) == 2:
            diff = f'DX {diff[1][:3]}'
        else:
            diff = f'STD {diff[0][:3]}'
        return f"{self.songname} [{diff} {self.internal_level}] - {self.score} ({self.rating})"

class MaimaiDXProfile:
    def __init__(self, player, best_old = [], best_new = [], best_naive = []):
        self.player = player
        self.api_url = f"https://kamai.tachi.ac/api/v1/users/{player}/games/maimaidx/Single/pbs/all"
        self.best_old = best_old
        self.best_new = best_new
        self.best_naive = best_naive
        
    def add_pb(self, entry):
        pb = entry["pb"]
        score = pb['scoreData']['percent']
        lamp = pb['scoreData']['lamp']
        songid = -1
        songname = entry["song"]['title']
        chart = entry["chart"]
        diff = chart['difficulty']
        internal_level = chart['levelNum']
        rating = pb["calculatedData"]["rate"]
        
        if is_latest_ver_chart(chart):
            self.best_new.append(MaimaiDXScore(score, songid, songname, diff, internal_level, rating, lamp))
            self.best_new = sorted(self.best_new, key=lambda x: x.rating, reverse=True)[:15]
        else:
            self.best_old.append(MaimaiDXScore(score, songid, songname, diff, internal_level, rating, lamp))
            self.best_old = sorted(self.best_old, key=lambda x: x.rating, reverse=True)[:35]
            
        self.best_naive.append(MaimaiDXScore(score, songid, songname, diff, internal_level, rating, lamp))
        self.best_naive = sorted(self.best_naive, key=lambda x: x.rating, reverse=True)[:50]

    def reload_pbs(self):
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
        i=1
        new_rating = 0
        print("----- Newest version B15 -----")
        for score in self.best_new:
            print(f"#{i} - {score}")
            new_rating += score.rating
            i+=1
        print(f"Newest version average: {new_rating} (avg. {round(new_rating/15)})")
        return new_rating
    
    def get_old_rating(self):
        i=1
        old_rating = 0
        print("----- Old versions B35 -----")
        for score in self.best_old:
            print(f"#{i} - {score}")
            old_rating += score.rating
            i+=1
        print(f"Old versions rating: {old_rating} (avg. {round(old_rating/35)})")
        return old_rating
    
    def get_naive_rating(self):
        i=1
        naive_rating = 0
        print("----- Naive B50 -----")
        for score in self.best_naive:
            print(f"#{i} - {score}")
            naive_rating += score.rating
            i+=1
        print(f"Naive rating: {naive_rating} (avg. {round(naive_rating/50)})")
        return naive_rating
    
    def get_ingame_rating(self):
        new_rating = self.get_new_rating()
        print("")
        old_rating = self.get_old_rating()

        ingame_rating = new_rating + old_rating
        print(f"In-game rating: {ingame_rating}")

my_profile = MaimaiDXProfile("qinmao")
my_profile.reload_pbs()
my_profile.get_ingame_rating()