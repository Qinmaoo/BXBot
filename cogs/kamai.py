import discord
from discord import app_commands
from discord.ext import commands
import os
import json

parentPath = os.path.dirname(os.path.abspath(__file__))

def register_kamai(id, kamai_username):
    path = parentPath+f"/profiles/{id}.json"
    try:
        with open(path, "r") as f:
            user_json = json.load(f)
            user_json["profileData"]["kamaiUsername"] = kamai_username
        with open(path, "w") as f:
            json.dump(user_json, f)
        return "Kamaitachi profile linked!"
    except FileNotFoundError:
        return "You haven't registered yet!"

class Kamai(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.describe(
        kamai_username = "Kamaitachi username"
    )
    
    @app_commands.command(
        name = "kamai",
        description = "Link your kamaitachi profile!"
    )

    async def kamai(
        self,
        interaction: discord.Interaction,
        kamai_username: str) -> None:
        name = interaction.user.name
        id = interaction.user.id
        answer = register_kamai(id, kamai_username)
        await interaction.response.send_message(answer,ephemeral=True)
        print(f"{name} has linked their kamaitachi. See {id}.json")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kamai(bot))