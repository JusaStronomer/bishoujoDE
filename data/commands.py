# Importing env file
import os
from dotenv import load_dotenv
load_dotenv()
DIRECT_IP = os.getenv("DIRECT_IP")

class CommandData:
	def __init__(self, data):
		self.data = data
	
	def get_protocol(self, key: str):
		if key in self.data:
			return self.data[key]
		else:
			return []

commands = {
	"アニメ":[
		{"type": "label_audio", "key": "vpn"},
		{"type": "subprocess", "command": ["nordvpn", "connect", DIRECT_IP]},
		{"type": "label_audio", "key": "danimestore"},
		{"type": "subprocess", "command": ["google-chrome", "https://animestore.docomo.ne.jp"]},
		{"type": "label_audio", "key": "protocol_anime"}
	],
	"ダラダラ":[
		{"type": "label_audio", "key": "discord"},
		{"type": "subprocess", "command": "discord"},
		{"type": "label_audio", "key": "spotify"},
		{"type": "subprocess", "command": "spotify"},
		{"type": "label_audio", "key": "youtube"},
		{"type": "subprocess", "command": ["google-chrome", "https://youtube.com"]},
		{"type": "label_audio", "key": "protocol_dara"}
	],
	"プログラミング":[
		{"type": "label_audio", "key": "nvim"},
		{"type": "subprocess", "command": ["nvim", "~/Projects"]},
		{"type": "label_audio", "key": "gemini"},
		{"type": "subprocess", "command": ["google-chrome", "https://gemini.google.com/app"]},
		{"type": "label_audio", "key": "protocol_vim"}
	]
}

CommandManager = CommandData(commands)
