import os
from typing import Any, Callable, Literal
import logging

import discord
from discord import app_commands, utils

from mcstatus import JavaServer


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
        self.servers = []

    async def on_ready(self) -> None:
        if not self.synced:
            await tree.sync()
            for server in self.guilds:
                await tree.sync(guild=discord.Object(id=server.id))
                logging.info("- " + server.name)
            self.synced = True
        logging.info("Ready!")


bot = MyBot()
tree = app_commands.CommandTree(bot)

survival_channels: list[int] = [930585547842404372, 930322945040072734]
modded_channels: list[int] = [1241016401502928967, 1237006920863453225]
creative_channels: list[int] = []

server_type = Literal["None", "Survival", "Modded", "Creative"]

ips: dict[server_type, str] = {
    "Survival": "173.233.142.94:25565",
    "Modded": "173.233.142.10:25565",
    "Creative": "173.233.142.2:25565"
}

@tree.command(name="list",
              description="Lists the active members of a spooncraft server.")
@app_commands.describe(server='The Minecraft server to check. Not required in certain channels.')
@app_commands.allowed_installs(guilds=True, users=True)
async def send_data(interaction: discord.Interaction,
                    server: server_type = "None"):
    await interaction.response.defer(ephemeral=True)
    if server == "None":
        if interaction.channel_id in survival_channels:
            server = "Survival"
        elif interaction.channel_id in modded_channels:
            server = "Modded"
        elif interaction.channel_id in creative_channels:
            server = "Creative"
        else:
            await interaction.followup.send("**You must either select a server "
                                            "or be in a recognised channel**")
            return
    server_lookup = JavaServer.lookup(ips.get(server))
    try:
        status = server_lookup.status()
    except TimeOutError:
        # For some reason it times out when getting the status of an empty server
        await interaction.followup.send(f"**No players online**")
        return
    except Exception as e:
        await interaction.followup.send(f"**An unexpected error occurred**")
        return
    count = status.players.online
    if count == 0:
        await interaction.followup.send(f"**No players online**")
        return
    max_count = status.players.max
    # query = server_lookup.query()
    # players = query.players.names
    players = status.players.sample
    player_list = ', '.join([i.name for i in players])
    await interaction.followup.send(f"**Online players ({count}/{max_count}):**\n```{player_list}```")


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
