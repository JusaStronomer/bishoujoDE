"""Handles the definition and retrieval of sequential command protocols.

This module definse the 'ProtocolData' class, which encapsulates pre-defined sequences of commands, referred to as 'protocols'.
The protocols are structured as lists of dictionaries, with each dict representing a single step in the sequence,
associating it's type and the key.

The possible types are:
        'update_label', which is associated to a string to be set as text in a Gtk.Label;
        'play_audio', which is associated to a audio_file name in a voicevox subdirectory;
        'subprocess', which is associated to a bash command and it's arguments.

Example Usage:
    # Assuming this file is named 'protocol_manager.py'
    from protocol_manager import ProtocolData

    data_manager = ProtocolData()
    anime_protocol = data_manager.get_protocol("アニメ")
    if anime_protocol:
        for command_step in anime_protocol:
            print(f"Executing: {command_step['type']} with data {command_step}")

Notes:

To use 'play_audio', it's necessary to prefix the string with './voicevox/character_name/'
and to sufix it with a '.wav' or any other valid audio file extension.

The keys in 'subprocess' are hardcoded as commands relevants to my reality (using nordvpn and having a DIRECT_IP address),
so it should be heavily modified to suit the needs of the any given reimplementation of the present project.

It's encouraged to store sensitive data in the '.env' file and use the 'dotenv' module to load it.

"""

# Importing env file
import os
from dotenv import load_dotenv

load_dotenv()
DIRECT_IP = os.getenv("DIRECT_IP")

class ProtocolData:
    def __init__(self) -> None:
        self.protocols = {

                "アニメ": [
                        {"type": "update_label", "serifu_key": "protocol_anima"},
                        {"type": "play_audio", "serifu_key": "protocol_anima"},
                        {"type": "update_label", "serifu_key": "vpn"},
                        {"type": "play_audio", "serifu_key": "vpn"},
                        {"type": "subprocess", "mode":"run", "command": "nordvpn connect " + str(DIRECT_IP)},
                        {"type": "update_label", "serifu_key": "danimestore"},
                        {"type": "play_audio", "serifu_key": "danimestore"},
                        {
                            "type": "subprocess",
                            "mode": "run",
                            "command": "google-chrome https://animestore.docomo.ne.jp",
                        },
                ],

                "ダラダラ": [
                        {"type": "update_label", "serifu_key": "protocol_serisu"},
                        {"type": "play_audio", "serifu_key": "protocol_serisu"},
                        {"type": "update_label", "serifu_key": "discord"},
                        {"type": "play_audio", "serifu_key": "discord"},
                        {"type": "subprocess", "mode":"popen", "command": "discord"},
                        {"type": "update_label", "serifu_key": "spotify"},
                        {"type": "play_audio", "serifu_key": "spotify"},
                        {"type": "subprocess", "mode":"popen", "command": "spotify"},
                        {"type": "update_label", "serifu_key": "youtube"},
                        {"type": "play_audio", "serifu_key": "youtube"},
                        {
                            "type": "subprocess",
                            "mode":"popen",
                            "command": "google-chrome https://youtube.com",
                        },
                ],

                "プログラミング": [
                        {"type": "update_label", "serifu_key": "protocol_estheim"},
                        {"type": "play_audio", "serifu_key": "protocol_estheim"},
                        {"type": "update_label", "serifu_key": "nvim"},
                        {"type": "play_audio", "serifu_key": "nvim"},
                        {"type": "subprocess", "mode":"popen", "command": ["nvim", "~/Projects"]},
                        {"type": "update_label", "serifu_key": "gemini"},
                        {"type": "play_audio", "serifu_key": "gemini"},
                        {
                            "type": "subprocess",
                            "mode":"popen",
                            "command": "google-chrome https://gemini.google.com/app",
                        },
                        {"type": "update_label", "serifu_key": "spotify"},
                        {"type": "play_audio", "serifu_key": "spotify"},
                        {"type": "subprocess", "mode":"popen", "command": "spotify"},
                ],
        }

    def get_protocol(self, key: str):
        """
        Retrieves a iterable list of dictionaries which
        represent sequences of commands.

        Args:
                key: represents the protocol name

        Returns:
                lits[dict]: the corresponding list of commands, as a list of dictionaries,
                                with the "update_label" type associated to a key for updating labels,
                                the "play_audio" type to a key for playing audio files
                                and the "subprocess" type to a key for background bash commands
        """

        return self.protocols.get(key)
