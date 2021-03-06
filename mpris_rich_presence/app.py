import argparse
import traceback
from datetime import datetime, timedelta
from operator import attrgetter
from pathlib import Path
from urllib.parse import urlparse, unquote
import sys

try:
    import gi
    # If this fails, then we know PyGObject was not installed, and it's kinda
    # crucial that it be installed.
except ImportError:
    print("PyGObject is not installed. It must be installed before the program can run.")
    exit()

try:
    gi.require_version("Playerctl", "2.0")
    # If this fails, then we know that Playerctl is not installed, and it as well
    # is kinda sorta super important for anything to work here.
except ValueError:
    print(
        "One of 2 things has happened here:\n"
        "1) Playerctl is not installed. Please install it!\n"
        "2) The typelib file for Playerctl is not present. "
        "You might need to uninstall Playerctl and PyGObject, "
        "and then reinstall them in a different order."
    )
    exit()

from gi.repository import Playerctl, GLib

from .rpc import DiscordIpcClient

UPDATE_SIGNALS = [
    "metadata",
    "playback-status::playing",
    "playback-status::paused",
    "playback-status::stopped",
    "seeked"
]
manager = Playerctl.PlayerManager()

ipc = DiscordIpcClient.on_platform("831641858643460106")
try:
    ipc.connect()
except Exception as error:
    pass

def get_mode():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")

    args = parser.parse_args()

    if args.auto:
        player_index = 0
    else:
        prompt = (
            "Select the player to be monitored for Rich Presence:\n"
            "{0}\n"
            "> "
        )

        players = [*map(attrgetter("name"), manager.props.player_names)]
        players.insert(0, "Auto-Detect Active Player (Default)")

        players_list = "\n".join(f"{index}) {name}" for index, name in enumerate(players))
        player_index = int(input(prompt.format(players_list)) or 0)

    return player_index

# Listener function to handle signals from playerctl
def on_status_update(player, stuff, manager):

    if player.props.player_name not in [
        *map(attrgetter("name"), manager.props.player_names)
    ]:
        return

    if not ipc.connected:
        # We might need to reconnect for various reasons
        try:
            ipc.reconnect()
        except Exception as error:
            return

    try:
        media_path = Path(unquote(urlparse(
                player.props.metadata["xesam:url"]
            ).path)
        )
    except KeyError:
        return

    if not media_path.exists(): # Ensure that only local files are allowed
        return

    state = "{0} - {1}".format(
        player.get_artist() or "Unknown Artist",
        player.get_album() or "Unknown Album"
    )
    details = player.get_title() or media_path.name
    end = datetime.now() + timedelta(
        microseconds=player.props.metadata["mpris:length"] - player.get_position()
    )

    data = {
        "state": state,
        "details": details,
        "timestamps": {
            "end": int(end.timestamp())
        },
        "assets": {
            "large_text": f"Listening with {player.props.player_name}",
            "large_image": "logo"
        }
    }

    if player.props.playback_status.value_nick != "Playing":
        data.pop("timestamps")

    try:
        ipc.set_activity(data)
    except BrokenPipeError:
        # Discord has been closed if this happens
        ipc.reconnect()

def on_player_vanish(manager, player):
    ipc.reconnect()

def register_player(name):
    player = Playerctl.Player.new_from_name(name)

    for signal in UPDATE_SIGNALS:
        player.connect(signal, on_status_update, manager)

    manager.manage_player(player)

def main():
    player_index = get_mode()

    if player_index != 0:
        register_player(manager.props.player_names[player_index])
    else:
        def on_new_player(manager, name):
            register_player(name)

        manager.connect("name-appeared", on_new_player)
        manager.connect("player-vanished", on_player_vanish)

        for name in manager.props.player_names:
            register_player(name)

    loop = GLib.MainLoop()
    loop.run()

main()
