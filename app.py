# TO DO LIST
# (1) Set up the threads for pausing the script without rendering the application unresponsive
# (2) Connect Label to Serifu
# (3) Add audio with simpleaudio
# (4) Add bash subprocesses
# (5) Fix startup systemd service
# (6) Restructure the layout to accomodate neofetch like data and terminal output with os.subprocess.stdout
# Importing libraries
import sys
import gi
import os
import subprocess
import simpleaudio
import time
import json
import threading

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
        self.serifu_data = {}
        serifu_config_path = os.path.join(SCRIPT_DIR, "serifu.json")
        try:
            with open(serifu_config_path, 'r', encoding='utf-8') as f:
                self.serifu_data = json.load(f)
        except FileNotFoundError:
            print(f"[Mado] ERROR: Serifu configuration file not found at {serifu_config_path}")
        except json.JSONDecodeError:
            print("[Mado] ERROR: Could not parse serifu.json")

        # ~~~　窓の見た目　~~~
        # ----------------------
        # --- Overall Layout ---
        # ----------------------
        self.canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12) # the canvas is the "drawable" area in the application
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
        self.reply = Gtk.Label(label="面あわせられしこと、幸いに存じます。ご用命を。")
        self.reply.set_justify(Gtk.Justification.CENTER)
        self.canvas.append(self.reply)

        # ~~~　美少女に気持ちを伝える手段　~~~
        # --- Entry Box to interact with Bishoujo ---
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("コマンド")
        self.entry.set_halign(Gtk.Align.CENTER)
        self.entry.set_width_chars(50)
        self.canvas.append(self.entry)
        # Connecting the enter key press on the Entry Box to the method
        self.entry.connect('activate', self.send_command)

        print("[Mado] Window initialized with image, label, and entry.")

    # ~~~　気持ちの伝え方　~~~
    # -----------------------------
    # --- Handler for Entry Box ---
    # -----------------------------
    def send_command(self, entry_widget: Gtk.Entry):
        """
        Processes the user input

        :param self: the Gtk.ApplicationWindow object
        :param entry_widget: the Gtk.Entry containing the user input string
        :return: None
        """
        command = entry_widget.get_text()
        print(f"Command entered: '{command}'")

        # Updating the reply label
        self.reply.set_text("コマンドを確認中")

        # Matching command
        match command.lower():
                case "アニメ":
                    self.reply.set_text("VPN発動")
                    # play audio
                    subprocess.run(["nordvpn", "connect", DIRECT_IP], check=True) # run in the background
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("ｄアニメストアに接続中")
                    # play audio
                    subprocess.run(["google-chrome", "https://animestore.docomo.ne.jp"], check=True)
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("接続完了")
                    # play audio
                case "ダラダラ":
                    self.reply.set_text("Discord開始")
                    # play audio
                    subprocess.run(["discord"], check=True)
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("Spotify開始")
                    # play audio
                    subprocess.run(["spotify"], check=True)
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("YouTubeに接続")
                    # play audio
                    subprocess.run(["google-chrome", "https://youtube.com"], check=True)
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("処理完了")
                    #play audio
                case "プログラミング":
                    self.reply.set_text("NeoVim開始")
                    # play audio
                    subprocess.run(["nvim", "~/Projects"], check=True)
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("Geminiに接続")
                    # play audio
                    subprocess.run(["google-chrome", "https://gemini.google.com/app"], check=True)
                    # function to tell the app to wait X seconds, while the audio is played
                    self.reply.set_text("処理完了")
                    #play audio
                case _:
                    self.reply.set_text("そのコマンドは登録してありません")
                    #play audio

        # Clearing entry
        entry_widget.set_text("")

#　~~~　窓の作成　~~~
# -----------------------------------
# --- Function to create a window ---
# -----------------------------------
def on_activate(app):
    """
    Function that runs when the application starts

    :param app: the Gtk.Application object
    :returns: None
    """
    usagi = Bishoujo("usagi")

    # Constructing the absolute path to the image
    image_relative_path = "images/usagi_010.png"
    image_full_path = os.path.join(SCRIPT_DIR, image_relative_path)

    usagi.setPortrait(image_full_path)
    print(f"[on_activate] Portrait path set to {usagi.getPortrait()}")

    mado = Mado(usagi, application=app)

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
    mado.set_decorated(False)
    mado.present()

# ------------------------------------------
# ******************************************
# --- Main Execution -----------------------
# ------------------------------------------
# Creating a new application
app = Gtk.Application(application_id="com.example.App.Ouroboros")
app.connect("activate", on_activate)

# Running the application
app.run(None)
