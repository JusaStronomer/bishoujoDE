
# Importing PyGObject and Gtk4 related modules
import gi

from data.commands import DIRECT_IP
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib

import playsound
import threading
import os
#import subprocess
from data.serifu import dai_hon

# Getting file path to construct absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ~~~　美少女クラス　~~~
# Creating bishoujo class
# this is the character whose portrait, lines and voice is used
class Bishoujo:
    def __init__(self, name: str):
        self.name = name
        self.tachie = os.path.join(SCRIPT_DIR, "images", self.name + ".png")

    def get_tachie(self):
        return self.tachie
    
    def get_onsei(self, key: str):
        self.onsei_dir = os.path.join(SCRIPT_DIR, "voicevox", self.name + "/")
        self.onsei = self.onsei_dir + key + ".wav"
        return self.onsei
    
    def get_serifu(self, key: str):
        return dai_hon(self.name, key)

# ~~~　美少女の窓　~~~
# Creating Window Class, to replace a generic Gtk.ApplicationWindow
# window is not a cool word, so we are using "mado"
class MyWindow(Gtk.ApplicationWindow):
    def __init__(self, bishoujo: Bishoujo, **kargs):
        super().__init__(**kargs, title="Project Ouroboros")
        self.maximize()
        self.bishoujo = bishoujo
        self.commands = {
            "アニメ":[
                {"type": "update_label", "serifu_key": "vpn"},
                {"type": "play_audio", "serifu_key": "vpn"},
                {"type": "subprocess", "command": ["nordvpn", "connect", DIRECT_IP]},
                {"type": "update_label", "serifu_key": "danimestore"},
                {"type": "play_audio", "serifu_key": "danimestore"},
                {"type": "subprocess", "command": ["google-chrome", "https://animestore.docomo.ne.jp"]},
                {"type": "update_label", "serifu_key": "protocol_anime"},
                {"type": "play_audio", "serifu_key": "protocol_anime"}
            ],
            "ダラダラ":[
                {"type": "label_audio", "serifu_key": "discord"},
                {"type": "subprocess", "command": "discord"},
                {"type": "label_audio", "serifu_key": "spotify"},
                {"type": "subprocess", "command": "spotify"},
                {"type": "label_audio", "serifu_key": "youtube"},
                {"type": "subprocess", "command": ["google-chrome", "https://youtube.com"]},
                {"type": "label_audio", "serifu_key": "protocol_dara"}
            ],
            "プログラミング":[
                {"type": "label_audio", "serifu_key": "nvim"},
                {"type": "subprocess", "command": ["nvim", "~/Projects"]},
                {"type": "label_audio", "serifu_key": "gemini"},
                {"type": "subprocess", "command": ["google-chrome", "https://gemini.google.com/app"]},
                {"type": "label_audio", "serifu_key": "protocol_vim"}
            ]
        }

        # ~~~　窓の見た目　~~~
        # ----------------------
        # --- Overall Layout ---
        # ----------------------

        # Defining the canvas, which represents the drawable area in the appliaction
        # for now the canvas is the only direct child of the window
        # however, we plan to set a box with horizon orientation to suport two canvas in the Layout Overhaul
        self.canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_child(self.canvas) # Set this main box as the window's single child

        # ~~~　美少女の立ち絵　~~~
        # Creating container for the bishoujo image file
        image_container = Gtk.CenterBox()
        self.canvas.append(image_container) # Add the CenterBox to our main vertical canvas

        portrait_path = self.bishoujo.get_tachie()
        actual_display_widget = None # this is the widget variable that will contain either the image or an error label

        if os.path.exists(portrait_path):
            print(f"[MyWindow] Gtk.Image: Attempting to load from {portrait_path}")
            actual_display_widget = Gtk.Image.new_from_file(portrait_path)
            actual_display_widget.set_pixel_size(1200)
        else:
            print(f"[MyWindow] ERROR: Image file not found at {portrait_path}.")
            error_label_text = f"Error: Image not found!\nPath was:\n{portrait_path}"
            actual_display_widget = Gtk.Label(label=error_label_text)
        
        # Set the image (or error label) as the center widget of the CenterBox
        if actual_display_widget:
            image_container.set_center_widget(actual_display_widget)

        # ~~~　美少女の答え　~~~
        # --- Bishoujo Reply Label Section ---

        # Defining the Gtk.Label that will hold the textual representation of the bishoujo's serifu
        # might be changed to a Gtk.TextView in the Layout Overhaul
        self.reply = Gtk.Label(label=self.bishoujo.get_serifu("welcome"))
        self.reply.set_justify(Gtk.Justification.CENTER)
        self.canvas.append(self.reply)

        # ~~~　美少女に気持ちを伝える手段　~~~
        # --- Entry Box to interact with Bishoujo ---

        # Defining the text input
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("コマンド")
        self.entry.set_halign(Gtk.Align.CENTER)
        self.entry.set_width_chars(50)
        self.canvas.append(self.entry)

        #Initial greeting
        self._launch_initial_sound_thread("welcome")

        # Connecting the enter key press on the Entry Box to the method
        self.entry.connect('activate', self.on_entry_activate)

        print("[MyWindow] Window initialized with image, label, and entry.")

    # --- Helper method to update GUI from any thread (schedules on main thread) ---
    def _update_reply_label_on_main_thread(self, serifu_key_or_direct_text: str, is_key: bool = True):
        text = ""
        if is_key:
            text = self.bishoujo.get_serifu(serifu_key_or_direct_text)
        else:
            text = serifu_key_or_direct_text
        
        if text: # Only update if text is not empty
            self.reply.set_text(text)
        return GLib.SOURCE_REMOVE

    # --- Synchronous audio playback method (to be called from worker thread) ---
    def _play_audio_sync_in_worker(self, serifu_key: str):
        audio_file = self.bishoujo.get_onsei(serifu_key)
        if not os.path.exists(audio_file):
            print(f"[Worker] Audio file not found: {audio_file} for key '{serifu_key}'")
            GLib.idle_add(self._update_reply_label_on_main_thread, f"Audio for '{serifu_key}' missing!", False)
            return

        print(f"[Worker] Playing audio: {audio_file} for key '{serifu_key}'")
        try:
            playsound.playsound(audio_file, True)
            print(f"[Worker] Finished playing: {audio_file}")
        except Exception as e:
            print(f"[Worker] Error playing audio {audio_file}: {e}")
            GLib.idle_add(self._update_reply_label_on_main_thread, f"Audio error for '{serifu_key}': {e}", False)

    # --- Launching a sound thread for audio playback at the very start of the application ---
    def _launch_initial_sound_thread(self, serifu_key_for_audio: str):
            """Launches a thread to play an initial sound."""
            print(f"[MainThread] Launching initial sound thread for key: {serifu_key_for_audio}")
            thread = threading.Thread(target=self._play_audio_sync_in_worker, args=(serifu_key_for_audio,))
            thread.daemon = True # So it doesn't prevent app exit
            thread.start()

    # --- Worker thread function to process the command sequence ---
    def _process_command_sequence_thread(self, command: str):
        # Initial "checking" message
        GLib.idle_add(self._update_reply_label_on_main_thread, "checking", True)
        # self._play_audio_sync_in_worker("checking") # Optional: if you have a "checking" audio

        sequence = self.commands.get(command.lower())

        if not sequence:
            GLib.idle_add(self._update_reply_label_on_main_thread, "unknown_command", True) # Use key from dai_hon
            self._play_audio_sync_in_worker("unknown_command_audio") # Use audio key
            return

        for action_item in sequence:
            action_type = action_item["type"]
            serifu_key = action_item.get("serifu_key") # Might not exist for subprocess only

            if action_type == "update_label":
                if serifu_key:
                    GLib.idle_add(self._update_reply_label_on_main_thread, serifu_key, True)
            elif action_type == "play_audio":
                if serifu_key:
                    self._play_audio_sync_in_worker(serifu_key)
            # elif action_type == "subprocess":
            #     cmd_to_run = action_item["command"]
            #     # Optionally update label before running
            #     # GLib.idle_add(self._update_reply_label_on_main_thread, f"Running: {cmd_to_run[0]}...", False)
            #     try:
            #         print(f"[Worker] Running subprocess: {cmd_to_run}")
            #         # subprocess.run(cmd_to_run, check=True)
            #         print(f"[Worker] Subprocess finished: {cmd_to_run}")
            #     except FileNotFoundError:
            #         error_msg = f"Command not found: {cmd_to_run[0]}"
            #         print(f"[Worker] {error_msg}")
            #         GLib.idle_add(self._update_reply_label_on_main_thread, error_msg, False)
            #         break # Stop sequence on this kind of error
            #     except subprocess.CalledProcessError as e:
            #         error_msg = f"Error running {cmd_to_run[0]}: {e}"
            #         print(f"[Worker] {error_msg}")
            #         GLib.idle_add(self._update_reply_label_on_main_thread, error_msg, False)
            #         break # Stop sequence on error
            #     except Exception as e: # Catch other potential errors
            #         error_msg = f"Unexpected error with {cmd_to_run[0]}: {e}"
            #         print(f"[Worker] {error_msg}")
            #         GLib.idle_add(self._update_reply_label_on_main_thread, error_msg, False)
            #         break


        # Final "done" message (could also be the last item in the sequence)
        # GLib.idle_add(self._update_reply_label_on_main_thread, "process_finished", True)
        # self._play_audio_sync_in_worker("process_finished")
        print(f"[Worker] Finished processing command: {command}")

    # --- Renamed send_command to on_entry_activate for clarity ---
    def on_entry_activate(self, entry_widget: Gtk.Entry): # Changed method name
        command = entry_widget.get_text().strip() # Add strip() to remove leading/trailing whitespace
        print(f"Command entered: '{command}'")
        entry_widget.set_text("") # Clear entry immediately

        if not command: # Ignore empty commands
            return

        # Launch the *single* worker thread for the entire command sequence
        thread = threading.Thread(target=self._process_command_sequence_thread, args=(command,))
        thread.daemon = True # Allows main program to exit even if threads are running
        thread.start()

    # Remove the old play_audio, _play_audio_threaded, _on_audio_finished_main_thread, _on_audio_error_main_thread
    # as their logic is now incorporated into the new structure.


#　~~~　窓の作成　~~~
# -----------------------------------------
# --- Function that initializes the app ---
# -----------------------------------------
def on_activate(app):
    Usagi = Bishoujo("Usagi")

    window = MyWindow(Usagi, application=app)

    # Styling the window
    css_provider = Gtk.CssProvider()
    style_relative_path = "style.css"
    style_full_path = os.path.join(SCRIPT_DIR, style_relative_path)
    try:
        css_provider.load_from_path(style_full_path)
    except GLib.Error as e:
        print(f"Error loading CSS file: {e.message}")

    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    window.set_decorated(False)
    window.present()

# ******************************************
# ------------------------------------------
# --- Main Execution -----------------------
# ------------------------------------------
# ******************************************

# Creating a new application
app = Gtk.Application(application_id="com.example.App.Ouroboros")
app.connect("activate", on_activate)

# Running the application
app.run(None)
