class SerifuData:
	def __init__(self):

		self.characters = {
				"Usagi": {
					"welcome": "中国うさぎ　待機",
					"checking": "確認中",
					"process_finished": "処理完了",
					"protocol_anime": "プロトコルアニメ終了",
					"protocol_dara": "プロトコルヴィム終了",
					"protocol_vim": "プロトコルダラ終了",
					"vpn": "VPN発動",
					"danimestore": "ｄアニメストアに接続",
					"nvim": "NeoVim開始",
					"gemini": "Geminiに接続",
					"discord": "Discord開始",
					"spotify": "Spotify開始",
					"youtube": "YouTubeに接続",
					"unknown_command": "理解不能"
				},
				# "OtherCharacter": { ... }
			}

	def get_serifu(self, bishoujo: str, key: str):
		"""
		Retrieves the serifu (text) for a given bishoujo character and key
		from an optimized nested dictionary structure.

		Args:
			bishoujo: The name of the character (e.g., "Usagi").
			key: The specific serifu key (e.g., "welcome", "checking").

		Returns:
			str: The corresponding serifu text if found, otherwise None.
		"""
		# Safely get the character's serifu dictionary
		character_serifu_dict = self.characters.get(bishoujo)

		if character_serifu_dict:
			# Safely get the serifu text from the character's dictionary
			return character_serifu_dict.get(key)
		else:
			print(f"Error: Character '{bishoujo}' not found.")
			return None

def dai_hon(bishoujo: str, key: str):
	data = SerifuData()
	return data.get_serifu(bishoujo, key)
