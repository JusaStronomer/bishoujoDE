import gi
import subprocess
import simpleaudio # Assuming simpleaudio for audio playback
import os

# Import necessary GLib components
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

class MyApplicationWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        """Initializes the application window and its components."""
        super().__init__(*args, **kwargs)

        # --- UI Elements ---
        # Assuming you have a Gtk.Label for replies and a Gtk.Entry for command input
        self.reply_label = Gtk.Label(label="")
        self.command_entry = Gtk.Entry()

        # --- Data ---
        # Your action sequences defined as a dictionary
        self.command_actions = self._initialize_action_data()
        # A mapping for text and audio file paths based on keys in command_actions
        self.action_details_map = self._initialize_action_details_map()

        # --- State Variables ---
        self._current_action_sequence = None
        self._current_action_index = 0
        self._current_play_obj = None # To keep track of playing audio

        # --- UI Setup ---
        # Set up your window layout and add reply_label and command_entry
        # For simplicity, let's assume they are added to some container
        # For example:
        # main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        # main_box.append(self.reply_label)
        # main_box.append(self.command_entry)
        # self.set_child(main_box)

        # --- Connect Signals ---
        # Connect the 'activate' signal of the entry to your command handling function
        self.command_entry.connect("activate", self.on_command_input)

        # --- Start the Initial Sequence (Welcome) ---
        self._start_welcome_sequence()

    def _initialize_action_data(self):
        """Defines the sequences of actions for each command."""
        # Return your command_actions dictionary here
        return {
             "アニメ":[
                 {"type": "label_audio", "key": "vpn_start"}, # Changed key for clarity
                 {"type": "subprocess", "command": ["nordvpn", "connect", "DIRECT_IP"]},
                 {"type": "label_audio", "key": "danimestore_connecting"}, # Changed key
                 {"type": "subprocess", "command": ["google-chrome", "https://animestore.docomo.ne.jp"]}, # Corrected 'key' to 'command' based on usage
                 {"type": "label_audio", "key": "protocol_anime_complete"} # Changed key
             ],
             "ダラダラ":[
                 {"type": "label_audio", "key": "discord_start"}, # Changed key
                 {"type": "subprocess", "command": "discord"}, # Assuming 'discord' is in PATH
                 {"type": "label_audio", "key": "spotify_start"}, # Changed key
                 {"type": "subprocess", "command": "spotify"}, # Assuming 'spotify' is in PATH
                 {"type": "label_audio", "key": "youtube_connecting"}, # Changed key
                 {"type": "subprocess", "command": ["google-chrome", "https://youtube.com"]},
                 {"type": "label_audio", "key": "protocol_dara_complete"} # Changed key
             ],
             "プログラミング":[
                 {"type": "label_audio", "key": "nvim_start"}, # Changed key
                 {"type": "subprocess", "command": ["nvim", os.path.expanduser("~/Projects")]}, # Expanded user home directory
                 {"type": "label_audio", "key": "gemini_connecting"}, # Changed key
                 {"type": "subprocess", "command": ["google-chrome", "https://gemini.google.com/app"]},
                 {"type": "label_audio", "key": "protocol_vim_complete"} # Changed key
             ]
         }

    def _initialize_action_details_map(self):
        """Maps keys to label text and audio file paths."""
        # Return a dictionary mapping keys (like "vpn_start") to
        # another dictionary containing "text" and "audio_path"
        return {
            "welcome": {"text": "ようこそ。コマンドを入力しなさい", "audio_path": "audio/welcome.wav"},
            "command_not_found": {"text": "そのコマンドは登録してありません", "audio_path": "audio/command_not_found.wav"},
            "vpn_start": {"text": "VPN発動", "audio_path": "audio/vpn_start.wav"},
            "danimestore_connecting": {"text": "ｄアニメストアに接続中", "audio_path": "audio/danimestore_connecting.wav"},
            "protocol_anime_complete": {"text": "処理完了 (アニメ)", "audio_path": "audio/protocol_anime_complete.wav"},
            "discord_start": {"text": "Discord開始", "audio_path": "audio/discord_start.wav"},
            "spotify_start": {"text": "Spotify開始", "audio_path": "audio/spotify_start.wav"},
            "youtube_connecting": {"text": "YouTubeに接続", "audio_path": "audio/youtube_connecting.wav"},
            "protocol_dara_complete": {"text": "処理完了 (ダラダラ)", "audio_path": "audio/protocol_dara_complete.wav"},
            "nvim_start": {"text": "NeoVim開始", "audio_path": "audio/nvim_start.wav"},
            "gemini_connecting": {"text": "Geminiに接続", "audio_path": "audio/gemini_connecting.wav"},
            "protocol_vim_complete": {"text": "処理完了 (プログラミング)", "audio_path": "audio/protocol_vim_complete.wav"},
            # Add other keys and their details
        }


    def _start_welcome_sequence(self):
        """Starts the initial welcome audio and sets the welcome text."""
        welcome_details = self.action_details_map["welcome"]
        self.reply_label.set_text(welcome_details["text"])
        # After welcome audio, the entry should become active
        self._play_audio_and_schedule_next(
            welcome_details["audio_path"],
            self._welcome_audio_complete_callback
        )

    def _welcome_audio_complete_callback(self):
        """Callback executed after the welcome audio finishes."""
        # Enable the command entry to receive user input
        self.command_entry.set_sensitive(True)
        self.command_entry.set_text("") # Clear the entry
        self.command_entry.grab_focus() # Set focus to the entry

    def on_command_input(self, entry):
        """Handles the user pressing Enter in the command entry."""
        command = entry.get_text().strip().lower()
        self.command_entry.set_sensitive(False) # Disable entry while processing

        if command in self.command_actions:
            self._current_action_sequence = self.command_actions[command]
            self._current_action_index = 0
            self._execute_next_action() # Start executing the sequence
        else:
            # Handle command not found
            not_found_details = self.action_details_map["command_not_found"]
            self.reply_label.set_text(not_found_details["text"])
            self._play_audio_and_schedule_next(
                not_found_details["audio_path"],
                self._action_sequence_complete # After "not found" audio, ready for next command
            )


    def _execute_next_action(self):
        """Executes the current action in the sequence or finishes if done."""
        if self._current_action_index < len(self._current_action_sequence):
            action = self._current_action_sequence[self._current_action_index]

            if action["type"] == "label_audio":
                self._perform_label_audio_action(action)
            elif action["type"] == "subprocess":
                self._perform_subprocess_action(action)
            # Add other action types if needed

        else:
            # Sequence is finished
            self._action_sequence_complete()

    def _perform_label_audio_action(self, action_data):
        """Handles actions of type 'label_audio': updates label and plays audio."""
        key = action_data["key"]
        details = self.action_details_map.get(key)

        if details:
            self.reply_label.set_text(details.get("text", ""))
            audio_path = details.get("audio_path")
            if audio_path and os.path.exists(audio_path):
                self._play_audio_and_schedule_next(
                    audio_path,
                    lambda: self._schedule_next_step_after_delay(0) # No extra delay after audio itself, delay is handled in _schedule_next_step_after_delay
                )
            else:
                print(f"Audio file not found for key: {key}")
                # If audio file is missing, proceed to the next action after a short delay
                self._schedule_next_step_after_delay(500) # Short delay if audio is missing
        else:
            print(f"Action details not found for key: {key}")
            # If action details are missing, proceed to the next action after a short delay
            self._schedule_next_step_after_delay(500)


    def _perform_subprocess_action(self, action_data):
        """Handles actions of type 'subprocess': runs an external command."""
        command = action_data["command"]
        try:
            # Use subprocess.Popen to run the command in the background
            # Pass command as a list if it has arguments
            if isinstance(command, str):
                 subprocess.Popen(command, shell=True) # Use shell=True for simple commands or if shell features are needed
            elif isinstance(command, list):
                 subprocess.Popen(command) # Preferred for commands with arguments

            # Schedule the next action after a fixed delay (e.g., 2 seconds as in your original code)
            self._schedule_next_step_after_delay(2000) # Delay in milliseconds

        except FileNotFoundError:
            print(f"Error: Command not found - {command}")
            self.reply_label.set_text(f"エラー: コマンドが見つかりません: {command}") # Update label on error
            self._schedule_next_step_after_delay(2000) # Proceed after delay even on error
        except Exception as e:
            print(f"Error running subprocess {command}: {e}")
            self.reply_label.set_text(f"エラー: サブプロセス実行失敗: {command}") # Update label on error
            self._schedule_next_step_after_delay(2000) # Proceed after delay even on error


    def _play_audio_and_schedule_next(self, filepath, callback_after_audio):
        """Plays an audio file non-blocking and schedules a callback when done."""
        try:
            wave_obj = simpleaudio.WaveObject.from_wave_file(filepath)
            self._current_play_obj = wave_obj.play()
            # Schedule periodic checks for playback completion
            GLib.timeout_add(50, self._check_playback_status, callback_after_audio) # Check every 50 ms

        except Exception as e:
            print(f"Error playing audio {filepath}: {e}")
            self._current_play_obj = None
            # If audio playback fails, call the callback immediately or after a short delay
            if callback_after_audio:
                GLib.timeout_add(100, callback_after_audio) # Schedule callback after a minimal delay

    def _check_playback_status(self, callback_after_audio):
        """GLib timeout callback to check if audio playback is finished."""
        if self._current_play_obj is None or not self._current_play_obj.is_playing():
            # Playback is done
            self._current_play_obj = None
            if callback_after_audio:
                 # Schedule the next action callback
                 GLib.timeout_add(0, callback_after_audio) # Schedule immediately after playback ends
            return GLib.SOURCE_REMOVE # Stop checking
        else:
            return GLib.SOURCE_CONTINUE # Continue checking


    def _schedule_next_step_after_delay(self, delay_ms):
        """Schedules the execution of the next action after a specified delay."""
        self._current_action_index += 1
        # Schedule the execution of the next action in the sequence
        GLib.timeout_add(delay_ms, self._execute_next_action)
        return GLib.SOURCE_REMOVE # This timeout is a one-time trigger


    def _action_sequence_complete(self):
        """Called when a command action sequence finishes."""
        self._current_action_sequence = None
        self._current_action_index = 0
        # Re-enable the command entry and set the ready message
        welcome_details = self.action_details_map["welcome"] # Or a different "ready" message
        self.reply_label.set_text(welcome_details["text"]) # Set ready text
        self.command_entry.set_sensitive(True)
        self.command_entry.set_text("") # Clear the entry
        self.command_entry.grab_focus() # Set focus back to the entry


# --- GTK Application Entry Point ---
# Standard Gtk.Application setup
# class Application(Gtk.Application):
#     def __init__(self):
#         super().__init__(application_id="com.example.mycommandapp")
#
#     def do_activate(self):
#         self.window = MyApplicationWindow(application=self)
#         self.window.present()
#
# if __name__ == "__main__":
#     app = Application()
#     app.run(None)
