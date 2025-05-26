class SerifuData:
	def __init__(self):

		self.characters = {
				"Usagi": {
					"welcome": "中国うさぎ　待機",
					"checking": "確認中",
					"process_finished": "処理完了",
					"protocol_anima": "プロトコル・アニマ　発動",
					"protocol_serisu": "プロトコル・セリス　発動",
					"protocol_estheim": "プロトコル・エストハイム　発動",
					"protocol_etro": "プロトコル・エトロ　発動",
					"vpn": "VPNより日本サーバーに接続中",
					"danimestore": "ｄアニメストアに接続",
					"nvim": "NeoVim開始",
					"gemini": "Geminiに接続",
					"discord": "Discord開始",
					"spotify": "Spotify開始",
					"youtube": "YouTubeに接続",
					"error" : "こく・エラーの発生確率上昇",
					"llm" : "とい・不明コマンドをLLMで対応する機能は利用可能",
					"negation" : "否",
					"affirmation" : "是",
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
