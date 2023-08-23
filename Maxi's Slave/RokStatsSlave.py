import asyncio
import discord
import os

from dotenv import load_dotenv
from discord.ext import commands
from sheets import KvkStats, DiscordDB, TopX
from StringProgressBar import progressBar

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)
objDiscordGuildID = discord.Object(id=int(GUILD))
kvk_stats = KvkStats()
discord_db = DiscordDB()
topx = TopX()
bot.remove_command("help")


async def send_id_stats(gov_id: int, author_id, interaction: discord.Interaction=None, channel=None):
    """
    Sends individual player stats in an embed message.

    Args:
        gov_id (int): Governor ID.
        author_id: Discord user ID.
        interaction (discord.Interaction, optional): Discord interaction for responding to slash commands. Defaults to None.
        channel (discord.TextChannel, optional): Discord channel for sending the message. Defaults to None.
    """    
    player_stats = kvk_stats.get_player_stats(gov_id)
    player_name = player_stats["Governor"]
    player_id = player_stats["Governor ID"]
    player_rank = player_stats["Rank"]
    player_snapshot_power = player_stats["Starting Power"]
    player_current_points = player_stats["Current Points"]
    player_status = player_stats["Current Status"]
    player_t4kills = player_stats["T4 Kills"]
    player_t5kills = player_stats["T5 Kills"]
    player_total_kills = int(player_t4kills) + int(player_t5kills)
    player_total_deads = int(player_stats["Deads"])
    kills_percentage = player_total_kills * 100 // int(player_stats["Kills Required"])
    deads_percentage =  player_total_deads * 100 // int(player_stats["Deads Required"])
    total = 100
    size = 15    
    killsbar = progressBar.filledBar(total, kills_percentage, size)
    deadsbar = progressBar.filledBar(total, int(deads_percentage), size)
    user = await bot.fetch_user(author_id)
    if user.avatar:
        userpfp = user.avatar
    else:
        userpfp = "https://media.discordapp.net/attachments/1076154233197445201/1127610236744773792/discord-black-icon-1.png"

    if player_stats:
        embed = discord.Embed(color=0xf90101)

        embed.title = f"KvK Personal stats"
        embed.set_author(name="TheMaxi7", url="https://github.com/TheMaxi7",
                             icon_url="https://avatars.githubusercontent.com/u/102146744?v=4")
         
        #embed.set_thumbnail(url=f"https://rokstats.online/img/governors/{gov_id}.jpg")

        description = f"Governor: {player_name if player_name else '0'}\nPower snapshot: {player_snapshot_power if player_snapshot_power else '0'}\nGovernor ID: {player_id if player_id else '0'}\nCurrent points: {player_current_points if player_current_points else '0'}\nAccount status: {player_status if player_status else '0'}\n" 
        embed.description = description

        embed.add_field(name="Rank", value=player_rank, inline=True)
        embed.add_field(name="Kills required", value=player_stats["Kills Required"], inline=True)
        embed.add_field(name="Deads required", value=player_stats["Deads Required"], inline=True)
        embed.add_field(name="CURRENT KILLS", value=f"{player_total_kills}\n{killsbar[0]}   {int(killsbar[1])}%", inline=False)
        embed.add_field(name="CURRENT DEADS", value=f"{player_total_deads}\n{deadsbar[0]}   {int(deadsbar[1])}%", inline=False)
        
        embed.set_footer(text=f"Requested by @{author_id}",
                             icon_url=f"{userpfp}")

        if interaction:
            await interaction.response.send_message(embed=embed)
        elif channel:
            await channel.send(embed=embed)
    else:
        if interaction:
            await interaction.response.send_message(
                "Bro, this ID does not exist",
                ephemeral=True
            )
        elif channel:
            await channel.send("Bro, this ID does not exist", ephemeral=True)

async def send_top_x_stats(value:int, interaction:discord.Interaction=None, channel=None):
    """
    Sends cumulative top X stats in an embed message.

    Args:
        value (int): Top X value.
        interaction (discord.Interaction, optional): Discord interaction for responding to slash commands. Defaults to None.
        channel (discord.TextChannel, optional): Discord channel for sending the message. Defaults to None.
    """
    top_x_stats = topx.top_x(value)
    title = f"KvK stats of Top "+ str(value) +" by power"
    fields = ["Total T4 Kills", "Total T5 Kills", "Total Deads"]
    if top_x_stats:
        embed = discord.Embed(color=0xa30000)
        embed.title= title
        embed.description = f"- Stay strapped or get clapped -"
        embed.add_field(name=fields[0], value=f"{top_x_stats[0]:,}" if top_x_stats[0] != "" else "No data", inline=True)
        embed.add_field(name=fields[1], value=f"{top_x_stats[1]:,}" if top_x_stats[1] != "" else "No data", inline=True)
        embed.add_field(name=fields[2], value=f"{top_x_stats[2]:,}" if top_x_stats[2] != "" else "No data", inline=True)
        embed.set_image(url="https://cdn.discordapp.com/attachments/917952363808059444/1075874094429524068/cropped-Kingdom-of-Alberta-2-1.png")
        if interaction:
            await interaction.response.send_message(embed=embed)
        elif channel:
            await channel.send(embed=embed)
    else:
        if interaction:
            await interaction.response.send_message("You need to enter a number greater than 0", ephemeral=True)
        elif channel:
            await channel.send("You need to enter a number greater than 0", ephemeral=True)

@bot.hybrid_command(name="stats")
async def stats(ctx):
    """
    Command to fetch and display player's KvK stats.
    """
    interaction: discord.Interaction = ctx.interaction
    author_id = interaction.user.id
    data = interaction.data
    options = data["options"]
    option = options[0]
    value = option["value"]
    player_id = None
    try:
        player_id = int(value)
    except Exception as e:
        print(e)
    if player_id :
        await send_id_stats(player_id, author_id,interaction)
        await discord_db.save_dc_id(author_id,player_id)

@bot.hybrid_command(name="top")
async def top(ctx):
    """
    Command to fetch and display cumulative KvK stats of top X players.
    """    
    interaction: discord.Interaction = ctx.interaction
    data = interaction.data
    options = data["options"]
    option = options[0]
    value = option["value"]
    ranks = None
    try:
        ranks = int(value)
    except Exception as e:
        print (e)
    if ranks:
        if ranks > 450:
            await interaction.response.send_message("We track only top 300 players by power. Enter a value less than 300", ephemeral=True)
        else:
            await send_top_x_stats(value, interaction)
            
@bot.event
async def on_message(msg: discord.Message):
    """
    Event handler for processing messages.
    """
    author=msg.author
    author_id = author.id
    content = msg.content
    channel = msg.channel

    content = content.split(" ")
    if len(content) == 1:
        request = content[0].lower()
        if request == "stats":
            id_from_db = discord_db.get_id_from_discord(author_id=author_id)
            if id_from_db:
               await send_id_stats(gov_id= id_from_db, author_id=author_id, channel=channel)
            else:
                await channel.send(content = "Your ID has not been registered yet. Write 'stats <your id>' to save your ID before using 'stats'. (Example: stats 12345678)")
    elif len(content) == 2:
        request = content[0].lower()
        id = content[1]
        if request == "stats" and id:
            try:
                player_id = int(id)
            except Exception as e:
                print(e)
            if kvk_stats.get_player_stats(player_id):
                await send_id_stats(gov_id= player_id, author_id=author_id, channel=channel)
                await discord_db.save_dc_id(author_id, player_id)
            else:
                await channel.send("Bro, this ID does not exist")

@bot.hybrid_command(name="help")
async def help(ctx):
    """
    Command to display bot commands and usage.
    """
    embed = discord.Embed(title="Commands list", description=" ")
    embed.add_field(name="`/stats`", value="Shows KvK stats of the ID you enter. Also saves it for future uses")
    embed.add_field(name="`stats`", value="Shows KvK stats of the ID saved in the database for your Discord ID")
    embed.add_field(name="`/top`", value="Shows cumulated KvK stats of top X of the kingdom")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1076154233197445201/1076154255108485140/7biumd.jpg")
    await ctx.send(embed=embed)

async def main():
    await bot.start(TOKEN, reconnect=True)

asyncio.run(main())
