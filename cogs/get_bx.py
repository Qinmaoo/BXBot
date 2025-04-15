import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from .gamelist import game_list
from .GameSpecs.chunithm import ChunithmProfile
from .GameSpecs.maimaidx import MaimaiDXProfile
from typing import Optional

parentPath = os.path.dirname(os.path.abspath(__file__))
supported_games = list(game_list.keys())
best_types = {"ingame":"In-game","naive":"Naive"}


def get_bx(game, ratingType, id):
    path = parentPath+f"/profiles/{id}.json"
    
    if os.path.exists(path):
        with open(path, "r") as f:
            user_json = json.load(f)
            try:
                kamai_username = user_json["profileData"]["kamaiUsername"]
            except KeyError:
                return {}, "Please link your Kamaitachi account first."
               
            if game == "chunithm":
                game_profile = ChunithmProfile(kamai_username)
            elif game == "maimaidx":
                game_profile = MaimaiDXProfile(kamai_username)
            else:
                return {}, "An error has occured"
            
            game_profile.reload_pbs()
            
            
            if ratingType == "naive":
                best = game_profile.best_naive
                rating = game_profile.get_naive_rating()
                
                output = {"rating":rating, "best":[str(score) for score in best]}
                return output, "Done!"
            
            elif ratingType == "ingame":
                best_old = game_profile.best_old
                best_new = game_profile.best_new
                rating = game_profile.get_ingame_rating()
                
                output = {"rating":rating, "best_old":[str(score) for score in best_old], "best_new": [str(score) for score in best_new]}
                return output, "Done!"
                    
    else:
        return {}, "Please register first."

class GetBX(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(
        name = "getbx",
        description = "Get your Best X for a game"
    )
    
    @app_commands.describe(
        game_name = "Game",
        best_type = "Type of best (in-game / naive)"
    )
    
    @app_commands.choices(
    game_name = [app_commands.Choice(name=gamemetadata["display_name"], value=gameid) for gameid, gamemetadata in game_list.items()],
    best_type = [app_commands.Choice(name=f"{typename} rating", value = typeid) for typeid, typename in best_types.items()]
)
    
    async def getbx(
        self,
        interaction: discord.Interaction,
        game_name: app_commands.Choice[str],
        best_type: Optional[app_commands.Choice[str]] = None) -> None:
        
        name = interaction.user.display_name
        id = interaction.user.id
        game_name = game_name.value
        best_type = best_type.value if best_type else "naive"
                
        data, answer = get_bx(game_name, best_type, id)

        embed=discord.Embed(title=f"{name}\'s {game_list[game_name]['display_name']} best {game_list[game_name]['pb_amount_in_top']} ({best_types[best_type]})")

        for fieldname, fieldvalue in data.items():
            if fieldname == "rating":
                embed.add_field(name=game_list[game_name]["rating_name"], value=fieldvalue, inline=False)
            else:
                fieldvalue = "\n".join(fieldvalue)
                print(len(fieldvalue))
                # embed.add_field(name=fieldname, value=fieldvalue, inline=False)
            

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GetBX(bot))