import os
import db
import panel as panel_ui
import discord
from discord.ext import commands
from dotenv import load_dotenv



load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    db.init_db()
    bot.add_view(panel_ui.MagazynView())
    print("Bot widzi serwery:", [(g.name, g.id) for g in bot.guilds])
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f"Zalogowano jako {bot.user} - bot działa")

@bot.tree.command(name="ping", description="Sprawdza, czy bot zipie")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Obiecano mi to 3000 lat temu", ephemeral=True)

@bot.tree.command(name="panel", description="Wyświetla panel magazynu")
async def panel_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=panel_ui.buduj_embed(interaction.guild_id),
        view=panel_ui.MagazynView()
    )

bot.run(TOKEN)