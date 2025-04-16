game_list = {
    "chunithm": {
        "display_name":"Chunithm",
        "rating_name":"Rating",
        "rating_shortcut":"rt",
        "has_old_new": True,
        "pb_amount_in_old": 30,
        "pb_amount_in_new": 20,
        "has_recent": False,
        "pb_amount_in_top": 50,
        "name_in_url_ztk": "chunithm",
        },
    "maimaidx": {
        "display_name":"Maimai DX",
        "rating_name":"Rating",
        "rating_shortcut":"rt",
        "has_old_new": True,
        "pb_amount_in_old": 35,
        "pb_amount_in_new": 15,
        "has_recent": False,
        "pb_amount_in_top": 50,
        "name_in_url_ztk": "maimai",
        },
    # "iidx": {
    #     "display_name":"Beatmania IIDX",
    #     "rating_name":"KTLampRating",
    #     "rating_shortcut":"kt",
    #     "has_old_new": False,
    #     "has_recent": False,
    #     "pb_amount_in_top": 20,
    #     },
}

class Game:
    def __init__(self, game_id, game_name):
        self.game_id = game_id
        self.game_name = game_name