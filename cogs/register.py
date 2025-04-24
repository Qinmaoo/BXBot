import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from cogs.GameSpecs.gamelist import game_list


parentPath = os.path.dirname(os.path.abspath(__file__))
supported_games = list(game_list.keys())

def register_player(id):
    folder_path =parentPath+f"/profiles"
    path = parentPath+f"/profiles/{id}.json"
    
    if os.path.exists(path):
        return "You're already registered!"
    else:
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        with open(path,"w") as f:
            out = {"profileData":{}}
            for game in supported_games:
                out[game] = {}
            json.dump(out, f)
        return "Profile successfully created!"

class Register(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(
        name = "register",
        description = "Register your profile!"
    )

    async def register(
        self,
        interaction: discord.Interaction) -> None:
        name = interaction.user.name
        id = interaction.user.id
        answer = register_player(str(interaction.user.id))
        await interaction.response.send_message(answer, ephemeral=True)
        print(f"{name} has registered to the database. See {id}.json")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Register(bot))