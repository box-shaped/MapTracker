import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import mapgrabber
import json
from time import sleep as delay
import asyncio
load_dotenv()

token = os.getenv('TOKEN')

intents = discord.Intents.default()


bot = commands.Bot(command_prefix='.map ', intents=intents)

@bot.command()
async def config(ctx, *args):
    if not args:
        await ctx.send("No arguments provided.")
        return

    cmd = args[0].lower()
    if cmd =="testlog":
        await log("This is a test log message.")
        await ctx.send("Test log message sent.")

        return
    if cmd == "setlogchannel":
        if len(args) < 2:
            await ctx.send("Please provide a channel ID.")
            return
        try:
            channel_id = int(args[1])
            channel = bot.get_channel(channel_id)
            if channel is None:
                await ctx.send("Channel not found.")
                return
            mapgrabber.config[2] = channel_id
            with open("config.json", "w", encoding="utf-8") as write_file:
                json.dump(mapgrabber.config, write_file, indent=4)
            await ctx.send(f"Log channel set to {channel.name}.")
        except ValueError:
            await ctx.send("Invalid channel ID.")
        return


    if cmd == "reload":
        mapgrabber.reload_config()
        await ctx.send("Config reloaded.")
        return

    if cmd == "show":
        await ctx.send(mapgrabber.config)
        return

    if cmd == "whitelist":
        if len(args) < 2:
            await ctx.send("Usage: .map config whitelist <show|add|remove> [user]")
            return
        action = args[1].lower()
        if action == "show":
            await ctx.send(mapgrabber.config.get("whitelist", []))
        elif action == "add" and len(args) > 2:
            user = args[2]
            if user not in mapgrabber.config["whitelist"]:
                mapgrabber.config["whitelist"].append(user)
                with open("config.json", "w", encoding="utf-8") as write_file:
                    json.dump(mapgrabber.config, write_file, indent=4)
                await ctx.send(f"Added {user} to whitelist.")
            else:
                await ctx.send(f"{user} is already in whitelist.")
        elif action == "remove" and len(args) > 2:
            user = args[2]
            if user in mapgrabber.config["whitelist"]:
                mapgrabber.config["whitelist"].remove(user)
                with open("config.json", "w", encoding="utf-8") as write_file:
                    json.dump(mapgrabber.config, write_file, indent=4)
                await ctx.send(f"Removed {user} from whitelist.")
            else:
                await ctx.send(f"{user} not found in whitelist.")
        else:
            await ctx.send("Invalid whitelist command or missing user.")
        return

    if cmd == "regions":
        if len(args) < 2:
            await ctx.send("Usage: .map config regions <show|add|remove> [region] [inherit_whitelist|new_whitelist]")
            return
        action = args[1].lower()
        if action == "show":
            await ctx.send(mapgrabber.config.get("regions", {}))
        elif action == "add" and len(args) > 2:
            region = args[2]
            if region not in mapgrabber.config["regions"]:
                # Prompt for bounds or use defaults
                try:
                    bound1 = [int(args[4]), int(args[5]), int(args[6])] if len(args) > 6 else [0, 0, 0]
                    bound2 = [int(args[7]), int(args[8]), int(args[9])] if len(args) > 9 else [100, 100, 100]
                except (ValueError, IndexError):
                    await ctx.send("Invalid bounds. Usage: .map config regions add <region> [inherit_whitelist|new_whitelist] <bound1_x> <bound1_y> <bound1_z> <bound2_x> <bound2_y> <bound2_z>")
                    return

                new_region = {
                    "bound1": bound1,
                    "bound2": bound2,
                    "logging_status": True,
                    "exclude_whitelist": False
                }
                # Whitelist handling
                if len(args) > 3 and args[3].lower() == "inherit_whitelist":
                    new_region["whitelist"] = mapgrabber.config.get("whitelist", []).copy()
                else:
                    new_region["whitelist"] = []
                mapgrabber.config["regions"][region] = new_region
                with open("config.json", "w", encoding="utf-8") as write_file:
                    json.dump(mapgrabber.config, write_file, indent=4)
                await ctx.send(
                    f"Added region {region} with bounds {bound1} to {bound2}, logging_status=True, exclude_whitelist=False, "
                    f"whitelist={'inherited' if len(args) > 3 and args[3].lower() == 'inherit_whitelist' else 'new'}."
                )
            else:
                await ctx.send(f"Region {region} already exists.")
        elif action == "remove" and len(args) > 2:
            region = args[2]
            if region in mapgrabber.config["regions"]:
                del mapgrabber.config["regions"][region]
                with open("config.json", "w", encoding="utf-8") as write_file:
                    json.dump(mapgrabber.config, write_file, indent=4)
                await ctx.send(f"Removed region {region}.")
            else:
                await ctx.send(f"Region {region} not found.")
        else:
            await ctx.send("Invalid regions command or missing region.")
        return

    await ctx.send("Unknown config command.")
@bot.command()
async def ping(ctx):
    await ctx.send("pong")
@bot.command()
async def tracker(ctx, *args):
    if not args:
        await ctx.send("No arguments provided.")
        return

    cmd = args[0].lower()
    if cmd == "manual":
        if len(args) > 1 and args[1] == "check":
            detectedplayers = mapgrabber.check_all_regions()
            if not detectedplayers:
                await ctx.send("No players detected in any region.")
            else:
                msg = "Players detected:\n"
                for region, players in detectedplayers.items():
                    if players:
                        player_names = ', '.join([p['name'] for p in players])
                        msg += f"Region '{region}': {player_names}\n"
                await ctx.send(msg)
            return
        if len(args) > 2 and args[1] == "checkregion":
            region_name = args[2]
            detectedplayers = mapgrabber.check_region_presence(region_name)
            if not detectedplayers:
                await ctx.send(f"No players detected in region '{region_name}'.")
            else:
                player_names = ', '.join([p['name'] for p in detectedplayers])
                await ctx.send(f"Players detected in region '{region_name}': {player_names}")
            return
    if cmd == "logging":
        if args[1] == "config":
            if args[2] == "region":
                region_name = args[3]
                action = args[4].lower()
                if region_name not in mapgrabber.config.get("regions", {}):
                    await ctx.send(f"Region {region_name} not found.")
                    return

                if action == "logging_status":
                    if len(args) < 6:
                        await ctx.send("Usage: .map tracker logging config region <region_name> logging_status <true|false>")
                        return
                    logging_status = args[5].lower() == "true"
                    mapgrabber.config["regions"][region_name]["logging_status"] = logging_status
                    with open("config.json", "w", encoding="utf-8") as write_file:
                        json.dump(mapgrabber.config, write_file, indent=4)
                    await ctx.send(f"Set logging_status for region {region_name} to {logging_status}.")
                    return

                elif action == "exclude_whitelist":
                    if len(args) < 6:
                        await ctx.send("Usage: .map tracker logging config region <region_name> exclude_whitelist <true|false>")
                        return
                    exclude = args[5].lower() == "true"
                    mapgrabber.config["regions"][region_name]["exclude_whitelist"] = exclude
                    with open("config.json", "w", encoding="utf-8") as write_file:
                        json.dump(mapgrabber.config, write_file, indent=4)
                    await ctx.send(f"Set exclude_whitelist for region {region_name} to {exclude}.")
                    return

                else:
                    await ctx.send("Invalid action. Use logging_status or exclude_whitelist.")
                    return
            
                
           

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith(".map help") or message.content.startswith(".help"):
        help_text = (
            "```MapTracker Bot Help:\n"
            "\n"
            "General:\n"
            "  .map help                                  - Show this help message\n"
            "  .map ping                                  - Test bot responsiveness\n"
            "\n"
            "Configuration:\n"
            "  .map config reload                         - Reload the configuration from file\n"
            "  .map config show                           - Show the current configuration\n"
            "  .map config setlogchannel <channel_id>     - Set the log channel\n"
            "\n"
            "Whitelist:\n"
            "  .map config whitelist show                 - Show the whitelist\n"
            "  .map config whitelist add <user>           - Add a user to the whitelist\n"
            "  .map config whitelist remove <user>        - Remove a user from the whitelist\n"
            "\n"
            "Regions:\n"
            "  .map config regions show                   - Show all regions\n"
            "  .map config regions add <region> [inherit_whitelist|new_whitelist] <bound1_x> <bound1_y> <bound1_z> <bound2_x> <bound2_y> <bound2_z>\n"
            "                                            - Add a new region with bounds and whitelist options\n"
            "  .map config regions remove <region>        - Remove a region\n"
            "\n"
            "Tracker:\n"
            "  .map tracker manual check                  - Check all regions manually\n"
            "  .map tracker manual checkregion <region>   - Check a specific region manually\n"
            "  .map tracker logging config region <region> logging_status <true|false>\n"
            "                                            - Enable/disable logging for a region\n"
            "  .map tracker logging config region <region> exclude_whitelist <true|false>\n"
            "                                            - Exclude whitelist from logging for a region\n```"
        )
        await message.channel.send(help_text)
        

    await bot.process_commands(message)

async def log(message):
    channel = bot.get_channel(mapgrabber.config["log_channel"]) # Replace with your channel ID
    if channel:
        await channel.send(message)
    else:
        print('Channel not found.')
    return

async def tracker_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for region_name in mapgrabber.config.get("regions", {}):
            region = mapgrabber.config["regions"][region_name]
            if region.get("logging_status", 1):
                detectedplayers = mapgrabber.check_region_presence(region_name)
                if region.get("exclude_whitelist", 1):
                    detectedplayers = mapgrabber.filter_whitelist(detectedplayers, region_name)
                if detectedplayers:
                    player_names = ', '.join([player['name'] for player in detectedplayers])
                    log_message = f"Players detected in region '{region_name}': {player_names}"
                    await log(log_message)
       
        await asyncio.sleep(5)

@bot.event
async def on_ready():
    bot.loop.create_task(tracker_loop())

bot.run(token)

