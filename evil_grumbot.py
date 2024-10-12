import os
from typing import Any, Callable, Literal
import logging
import socket

import discord
from discord import app_commands, utils

from mcstatus import JavaServer

from custom_logger import Logger, BasicFormatter
logger = Logger('evil.grumbot')


class ServerDoesNotSupportQuerying(Exception):
    pass


class MyBot(discord.Client):
    def __init__(self, *args: Any, **kwargs: Any):
        discord.VoiceClient.warn_nacl = False

        intents = discord.Intents.default()
        super().__init__(*args,
                         intents=intents,
                         command_prefix="!",
                         activity=discord.Game(name='Gwaff'),
                         **kwargs)

        self.synced = False

    async def on_ready(self) -> None:
        if not self.synced:
            await tree.sync()
            for server in self.guilds:
                await tree.sync(guild=discord.Object(id=server.id))
                logging.info("- " + server.name)
            self.synced = True
        logging.info("Ready!")

    async def on_app_command_completion(self, interaction, command):
        logger.info(f"User '{interaction.user.name}' "
                    f"used command '{command.name}' "
                    f"in guild '{interaction.guild.name}'")


bot = MyBot()
tree = app_commands.CommandTree(bot)

survival_channels: list[int] = [930585547842404372, 930322945040072734]
events_channels: list[int] = [1241016401502928967, 1237006920863453225, 1167958292245512213, 1276552236323045437]
creative_channels: list[int] = []
testing_channels: list[int] = [646113723550924849]

server_type = Literal["Default", "Survival", "Events", "Creative"]

ips: dict[server_type, str] = {
    "Survival": "173.233.142.94:25565",
    "Events": "173.233.142.10:25565",
    "Creative": "173.233.142.2:25565",
    "Testing": "173.233.142.3:25565"
}


@tree.command(name="list",
              description="Lists the active members of a spooncraft server.")
@app_commands.describe(server='The Minecraft server to check. Not required in certain channels.',
                        hidden='Hide from others in this server (Default True). May depend on the server.')
@app_commands.allowed_installs(guilds=True, users=True)
async def send_data(interaction: discord.Interaction,
                    server: server_type = "Default",
                    hidden: bool = True):
    await interaction.response.defer(ephemeral=hidden)
    if server == "Default":
        if interaction.channel_id in survival_channels:
            server = "Survival"
        elif interaction.channel_id in events_channels:
            server = "Events"
        elif interaction.channel_id in creative_channels:
            server = "Creative"
        elif interaction.channel_id in testing_channels:
            server = "Testing"
        else:
            await interaction.followup.send("**You must either select a server "
                                            "or be in a recognised channel**")
            return
    server_name = f"**Spooncraft {server} Server**\n"
    server_lookup = JavaServer.lookup(ips.get(server))

    # Attempt to get the server information.
    status: JavaServer.JavaStatusResponse = None
    count = 0
    while count < 5:
        try:
            status = server_lookup.status()
            break
        except socket.timeout:
            logging.warn(f"Status TimeoutError {count}")
            count += 1
        except Exception as e:
            logging.warn(f"Status Unknown exception {e} {count}")
            count += 1
    # Attempt an error had occured.
    if status is None:
        await interaction.followup.send(f"**An unexpected error occurred**")
        return

    player_count = status.players.online
    if player_count == 0:
        await interaction.followup.send(f"{server_name}**No online players**")
        return

    max_count = status.players.max

    # Attempt to get the player list
    try:
        # Try through query if server supports it
        if server in ("Events", "Testing"):
            raise ServerDoesNotSupportQuerying(
                f"{server} Server does not support queying method."
            )
        query = server_lookup.query()
        players = query.players.names
        player_list = ', '.join(players)
        await interaction.followup.send(f"{server_name}**Online players ({player_count}/{max_count}):**\n```{player_list}```")
        return
    except (socket.timeout, ServerDoesNotSupportQuerying) as e:
        if e is socket.timeout:
            logging.error(f'Using backup for {server}, despite being supported.')
        else:
            logging.warning('Using backup')
        players = status.players.sample
        player_list = ', '.join(
            [i.name for i in players if i.name != "Anonymous Player"])
        # Sample has a possibility of missing players.
        if len(player_list) == 0 and player_count >= 1:
            player_list += 'Anonymous Player'
        elif len(players) < player_count:
            player_list += ', ...'
        await interaction.followup.send(f"{server_name}**Online players ({player_count}/{max_count}):**\n```{player_list}```")
        return


def runTheBot(token) -> None:
    '''
    Runs the bot
    '''
    bot.run(token)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)8s [%(asctime)s] %(filename)13s | %(message)s',
                        datefmt='%H:%M:%S')

    TOKEN = os.environ['BOT_TOKEN']
    runTheBot(TOKEN)

    logging.info("Fin!")
