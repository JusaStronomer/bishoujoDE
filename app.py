# TO DO LIST
# (5) Fix startup systemd service
# (6) Restructure the layout to accomodate neofetch like data and terminal output with os.subprocess.stdout

# Importing libraries
import enum
import sys
import gi
import os
import subprocess
import simpleaudio
import time
import json

# Importing the threading module and preventing segfault
import threading
threading.Thread(target=lambda: None).start()

# Importing GTK 4
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib

# Getting file path to construct absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Loading env file
from dotenv import load_dotenv
load_dotenv()
DIRECT_IP = os.getenv("DIRECT_IP")

# ~~~　美少女クラス　~~~
# Creating bishoujo class, in order to support character change
class Bishoujo:
    def __init__(self, name: str):
        self.name = name
        self.portrait = ""

    def setPortrait(self, filepath: str):
        self.portrait = filepath

    def getPortrait(self):
        return self.portrait

# ~~~　美少女の窓　~~~
# Creating Window Class, to replace a generic Gtk.ApplicationWindow
class Mado(Gtk.ApplicationWindow):
    def __init__(self, bishoujo: Bishoujo, **kargs):
        super().__init__(**kargs, title="bishoujoDE")
        self.maximize()

        # ~~~　美少女のセリフ　~~~
        # --- Loading Serifu Configuration ---
        # serifu.jon is the file containing
        # all of the bishoujo's lines, both as strings and as audio file paths
        # english is weird, so intead of "line" we use the term "serifu"
        self.serifu_data = {}
        serifu_config_path = os.path.join(SCRIPT_DIR, "serifu.json")
        try:
            with open(serifu_config_path, 'r', encoding='utf-8') as f:
                self.serifu_data = json.load(f)
        except FileNotFoundError:
            print(f"[Mado] ERROR: Serifu configuration file not found at {serifu_config_path}")
        except json.JSONDecodeError:
            print("[Mado] ERROR: Could not parse serifu.json")

        # --- Commands ---
        # this is the list of possible commands the user can input
        # and the associated actions
        # label_audio are used for getting a serifu text and audio file
        # subprocess are used to get a list of bash commands
        self.command_actions = {
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

        # --- State Variables ---
        # Since the threading module approach is incompatible with GLib
        # we are now trying to work with a "State Machine" approach.
        # All actions are going to be described as a sequence of events
        # and these are the relevant variables to handle the state
        self._current_action_sequence = None
        self._current_action_index = 0
        self._current_play_obj = None


        # ~~~　窓の見た目　~~~
        # ----------------------
        # --- Overall Layout ---
        # ----------------------

        # Defining the canvas, which represents the drawable area in the appliaction
        # for now the canvas is the only direct chield of the window
        # however, we plan to set a box with horizon orientation to suport two canvas in the Layout Overhaul
        self.canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_child(self.canvas)

        # ~~~　美少女の立ち絵　~~~
        # Creating container for the bishoujo image file
        image_container = Gtk.CenterBox()
        self.canvas.append(image_container)

        portrait_path = bishoujo.getPortrait()
        actual_display_widget = None # this is the widget variable that will contain either the image or an error label

        if os.path.exists(portrait_path):
            print(f"[Mado] Gtk.Image: Attempting to load from {portrait_path}")
            actual_display_widget = Gtk.Image.new_from_file(portrait_path)
            actual_display_widget.set_pixel_size(1200)
        else:
            print(f"[Mado] ERROR: Image file not found at {portrait_path}.")
            error_label_text = f"Error: Image not found!\nPath was:\n{portrait_path}"
            actual_display_widget = Gtk.Label(label=error_label_text)

        # Set the image (or error label) as the center widget of the CenterBox
        if actual_display_widget:
            image_container.set_center_widget(actual_display_widget)

        # ~~~　美少女の答え　~~~
        # --- Bishoujo Reply Label Section ---

        # Defining the Gtk.Label that will hold the textual representation of the bishoujo's serifu
        # might be changed to a Gtk.TextView in the Layout Overhaul
        initial_reply_key = "welcome"
        initial_reply_text = self.serifu_data.get(initial_reply_key, {}).get("text", "ようこそ")
        self.reply = Gtk.Label(label=initial_reply_text)
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
        # Connecting the enter key press on the Entry Box to the method
        self.entry.connect('activate', self.on_command_entered)
        # Play welcome audio
        self._play_audio_from_key_async(initial_reply_key)

        print("[Mado] Window initialized with image, label, and entry.")

    # ~~~　気持ちの伝え方　~~~
    # ------------------------------
    # --- Handlers for Entry Box ---
    # ------------------------------
    def _update_reply_label_text(self, new_label: str):
        """
        Updates the bishoujo reply label.

        Args:
            self: the Gtk.ApplicationWindow object
            new_label: the string to be set on the label
        
        Returns:
            GLib.SOURCE_REMOVE: boolean, with value False, that removes the source from the main loop
            
        """
        self.reply.set_text(new_label)
        return GLib.SOURCE_REMOVE

    def _play_audio_from_key_sync(self, serifu_key: str):
        """
        Plays audio specified by the serifu_key.
        It blocks execution, so it should idealy not be called in the main thread.

        Args:
            self: the Gtk.ApplicationWindow object
            serifu_key: string that corresponds to the dictionary key with the list containing the audio to be played

        Returns:
            None: the method only executes an action
        """
        serifu_entry = self.serifu_data.get(serifu_key)
        if serifu_entry and "file" in serifu_entry:
            audio_file_relative = serifu_entry["file"]
            audio_path_abs = os.path.join(SCRIPT_DIR, audio_file_relative)
            if os.path.exists(audio_path_abs):
                try:
                    print(f"[Thread/play_sync] Playing audio: {audio_path_abs} for key {serifu_key}")
                    wave_obj = simpleaudio.WaveObject.from_wave_file(audio_path_abs)
                    play_obj = wave_obj.play()
                    play_obj.wait_done()
                    print(f"[Thread/play_sync] Finished playing: {audio_path_abs}")
                except Exception as e:
                    print(f"[Thread/play_sync] Error playing audio: {audio_path_abs}: {e}")
            else:
                print(f"[Thread/play_sync] Audio file not found: {audio_path_abs}")
        else:
            print(f"[Thread/play_sync] No audio file found for key: {serifu_key}")

    def _play_audio_from_key_async(self, serifu_key: str):
        """
        Plays audio in a new thread without blocking UI for one-off plays

        Args:
            self: the Gtk.ApplicationWindow object
            serifu_key: string that corresponds to the dictionary key with the list containing the audio to be played

        Returns:
            None: the method only executes an action
        """
        thread = threading.Thread(target=self._play_audio_from_key_sync, args=(serifu_key,))
        thread.daemon = True
        thread.start()

    def _process_command_sequence_thread(self, command_key: str):
        """
        Reads the user input and executes the appropriated action.
        Should not be called in the main thread, since it contains code that blocks execution.

        Args:
            self: the Gtk.ApplicationWindow object
            command_key: string that corresponds to the input
        """
        actions = self.command_actions.get(command_key)

        checking_key = "checking"
        checking_text = self.serifu_data.get(checking_key, {}).get("text", "確認中")
        GLib.idle_add(self._update_reply_label_text, checking_text)
        self._play_audio_from_key_sync(checking_key)

        if not actions:
            unknown_key = "unkown_command"
            unkown_text = self.serifu_data.get(unknown_key, {}).get("text", "理解不能")
            GLib.iddle_add(self._update_reply_label_text, unkown_text)
            self._play_audio_from_key_sync(unknown_key)
            return

        for action_index, action_config in enumerate(actions):
            action_type = action_config["type"]

            if action_type == "label_audio" and "key" in action_config:
                serifu_key = action_config["key"]
                action_text = self.serifu_data.get(serifu_key, {}).get("text", "")
                GLib.iddle_add(self._update_reply_label_text, action_text)
                self._play_audio_from_key_async(serifu_key)

            elif action_type == "subprocess":
                cmd_list = action_config["command"]
                print(f"Subprocess received: {cmd_list}")
                print("Subprocessing not yet implemented")

    def on_command_entered(self, entry_widget: Gtk.Entry):
        """
        Handles user input, initiating the thread that will process it.

        Args:
            self: the Gtk.ApplicationWindow object
            entry_widget: the Gtk.Entry in which the user command was entered

        Returns:
            None
        """
        command_text = entry_widget.get_text()
        print(f"Command entered by the user: '{command_text}'")
        entry_widget.set_text("") # in order to clear the Gtk.Entry

        if not command_text:
            return
        
        thread = threading.Thread(target=self._process_command_sequence_thread, args=(command_text,))
        thread.daemon = True
        thread.start()

#　~~~　窓の作成　~~~
# -----------------------------------------
# --- Function that initializes the app ---
# -----------------------------------------
def on_activate(app):
    """
    Runs when the application starts.
    Initializes the bishoujo, loads CSS and creates a window


    Args:
        app: the Gtk.Application that will run on the window

    Returns:
        None
    """
    usagi = Bishoujo("usagi")

    # Constructing the absolute path to the image
    image_relative_path = "images/usagi_010.png"
    image_full_path = os.path.join(SCRIPT_DIR, image_relative_path)

    usagi.setPortrait(image_full_path)
    print(f"[on_activate] Portrait path set to {usagi.getPortrait()}")

    mado = Mado(usagi, application=app)

    # Loading the CSS file to style the window
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

    # Removing the window top bar and presenting it
    mado.set_decorated(False)
    mado.present()

# ******************************************
# ------------------------------------------
# --- Main Execution -----------------------
# ------------------------------------------
# ******************************************

# Creating a new application
app = Gtk.Application(application_id="com.example.App.bishoujoDE")
app.connect("activate", on_activate)

# Running the application
app.run(None)
