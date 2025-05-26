# Importing PyGObject and Gtk4 related modules
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib

# Importing other external modules
import playsound
import threading
import os
import subprocess

# Importing data structures
from data.serifu import SerifuData
from data.protocols import ProtocolData
import data.sysinfo

# Getting file path to construct absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ~~~　美少女クラス　~~~
# Creating bishoujo class.
# This is the character whose portrait, lines and voice is used.
# The "name" argument is extremely important, since it's expected to be used in the project's filesystem:
# for the 立ち絵, the "images" directory should have an image file with the character's name (with the ".png" extension);
# for the 音声, the "voicevox" directory should have a subdirectory with the character's name, as the parent of all of the audio files.
# The 台本 represents the reference with all the character lines (セリフ).
# With these explanations, the terminology should be dismistified.
class Bishoujo:
    def __init__(self, name: str, dai_hon: SerifuData):
        self.name = name
        self.tachie = os.path.join(SCRIPT_DIR, "images", self.name + ".png")
        self.dai_hon = dai_hon

    def get_tachie(self):
        return self.tachie

    def get_onsei(self, key: str):
        self.onsei_dir = os.path.join(SCRIPT_DIR, "voicevox", self.name + "/")
        self.onsei = self.onsei_dir + key + ".wav"
        return self.onsei

    def get_serifu(self, key: str):
        return self.dai_hon.get_serifu(self.name, key)

    # -- 報告関連の関数 --
    def os_houkoku(self):
        return data.sysinfo.get_os_info()

    def host_houkoku(self):
        return data.sysinfo.get_host_info()

    def kernel_houkoku(self):
        return data.sysinfo.get_kernel_info()

    def uptime_houkoku(self):
        return data.sysinfo.get_uptime_info()

    def package_houkoku(self):
        return data.sysinfo.get_package_count_dpkg()

    def memory_houkoku(self):
        return data.sysinfo.get_memory_info()

# ~~~　美少女の窓　~~~
# Creating Window Class, to replace a generic Gtk.ApplicationWindow
# Window is not a cool word, so we are using "mado".
class Mado(Gtk.ApplicationWindow):
    def __init__(self, **kargs):
        super().__init__(**kargs, title="Project Ouroboros")
        self.maximize()
        self.serifu_manager = SerifuData()
        self.bishoujo = Bishoujo("Usagi", self.serifu_manager)
        self.protocol_manager = ProtocolData()

        # ~~~　窓の見た目　~~~
        # ----------------------
        # --- Overall Layout ---
        # ----------------------

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
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Defining the canvas, which represents the drawable area in the appliaction
        # it should be the only direct child of the window
        self.canvas = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.canvas.set_size_request(2000, 1000)
        self.canvas.set_halign(Gtk.Align.CENTER)
        self.canvas.set_valign(Gtk.Align.CENTER)
        # canvas_style_context = self.canvas.get_style_context()
        # canvas_style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # canvas_style_context.add_class("canvas")
        self.set_child(self.canvas)

        self.left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.left_column.set_size_request(1000, 1000)
        self.right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.right_column.set_size_request(1000, 1000)

        self.left_column.set_hexpand(False)
        self.right_column.set_hexpand(False)

        self.canvas.append(self.left_column)
        self.canvas.append(self.right_column)

        # ----------------------
        # --- RIGHT COLUMN -----
        # ----------------------

        # ~~~　美少女の立ち絵　~~~
        # Creating container for the bishoujo image file
        image_container = Gtk.CenterBox()
        image_container.set_vexpand(False)
        self.right_column.append(
            image_container
        )  # Add the CenterBox to our main vertical canvas

        portrait_path = self.bishoujo.get_tachie()
        actual_display_widget = None  # this is the widget variable that will contain either the image or an error label

        if os.path.exists(portrait_path):
            print(f"[Mado] Gtk.Image: Attempting to load from {portrait_path}")
            actual_display_widget = Gtk.Image.new_from_file(portrait_path)
            # actual_display_widget.set_hexpand(True)
            # actual_display_widget.set_vexpand(True)
            actual_display_widget.set_pixel_size(1000)
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
        self.reply = Gtk.Label(label=self.bishoujo.get_serifu("welcome"))
        self.reply.set_justify(Gtk.Justification.CENTER)
        self.reply.add_css_class('reply_label')
        self.right_column.append(self.reply)

        # ~~~　美少女に気持ちを伝える手段　~~~
        # --- Entry Box to interact with Bishoujo ---

        # Defining the text input
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("コマンド")
        self.entry.set_halign(Gtk.Align.CENTER)
        self.entry.set_width_chars(30)
        self.entry.set_opacity(0.9)
        self.right_column.append(self.entry)
        self.entry.grab_focus()

        # ----------------------
        # --- LEFT COLUMN -----
        # ----------------------

        neofetch_grid = Gtk.Grid()
        neofetch_grid.set_column_spacing(6)  # Space between key and value
        neofetch_grid.set_row_spacing(3)  # Space between lines
        self.left_column.append(neofetch_grid)  # Add the grid to your left column

        # Neofetch data
        key_kernel = Gtk.Label(label="Kernel:")
        key_kernel.add_css_class('neofetch_key')
        key_kernel.set_xalign(1.0)  # Right-align the key text within its cell
        neofetch_grid.attach(key_kernel, 0, 0, 1, 1)  # Col 0, Row 0

        value_kernel = Gtk.Label(label=self.bishoujo.os_houkoku())
        value_kernel.add_css_class('neofetch_value')
        value_kernel.set_xalign(0.0)  # Left-align the value text
        value_kernel.set_selectable(True)  # Allow user to select text
        neofetch_grid.attach(value_kernel, 1, 0, 1, 1)  # Col 1, Row 0

        # Example for the second line:
        key_distro = Gtk.Label(label="Distro:")
        key_distro.add_css_class('neofetch_key')
        key_distro.set_xalign(1.0)
        neofetch_grid.attach(key_distro, 0, 1, 1, 1)  # Col 0, Row 1

        value_distro = Gtk.Label(label="Ubuntu 24.04.2 LTS x86_6")
        value_distro.add_css_class('neofetch_value')
        value_distro.set_xalign(0.0)
        value_distro.set_selectable(True)
        neofetch_grid.attach(value_distro, 1, 1, 1, 1)  # Col 1, Row 1

        key_host = Gtk.Label(label="Host:")
        key_host.add_css_class('neofetch_key') 
        key_host.set_xalign(1.0)
        neofetch_grid.attach(key_host, 0, 2, 1, 1)

        value_host = Gtk.Label(label=self.bishoujo.host_houkoku())
        value_host.add_css_class('neofetch_value') 
        value_host.set_xalign(0.0)
        value_host.set_selectable(True)
        neofetch_grid.attach(value_host, 1, 2, 1, 1)

        key_uptime = Gtk.Label(label="Uptime:")
        key_uptime.add_css_class('neofetch_key') 
        key_uptime.set_xalign(1.0)
        neofetch_grid.attach(key_uptime, 0, 3, 1, 1)

        value_uptime = Gtk.Label(label=self.bishoujo.uptime_houkoku())
        value_uptime.add_css_class('neofetch_value') 
        value_uptime.set_xalign(0.0)
        value_uptime.set_selectable(True)
        neofetch_grid.attach(value_uptime, 1, 3, 1, 1)

        key_packages = Gtk.Label(label="Packages:")
        key_packages.add_css_class('neofetch_key') 
        key_packages.set_xalign(1.0)
        neofetch_grid.attach(key_packages, 0, 4, 1, 1)

        value_packages = Gtk.Label(label=self.bishoujo.package_houkoku())
        value_packages.add_css_class('neofetch_value') 
        value_packages.set_xalign(0.0)
        value_packages.set_selectable(True)
        neofetch_grid.attach(value_packages, 1, 4, 1, 1)

        key_shell = Gtk.Label(label="Shell:")
        key_shell.add_css_class('neofetch_key') 
        key_shell.set_xalign(1.0)
        neofetch_grid.attach(key_shell, 0, 5, 1, 1)

        value_shell = Gtk.Label(label="bash 5.2.21")
        value_shell.add_css_class('neofetch_value') 
        value_shell.set_xalign(0.0)
        value_shell.set_selectable(True)
        neofetch_grid.attach(value_shell, 1, 5, 1, 1)

        key_resolution = Gtk.Label(label="Resolution:")
        key_resolution.add_css_class('neofetch_key') 
        key_resolution.set_xalign(1.0)
        neofetch_grid.attach(key_resolution, 0, 6, 1, 1)

        value_resolution = Gtk.Label(label="3840x2160")
        value_resolution.add_css_class('neofetch_value') 
        value_resolution.set_xalign(0.0)
        value_resolution.set_selectable(True)
        neofetch_grid.attach(value_resolution, 1, 6, 1, 1)

        key_DE = Gtk.Label(label="DE:")
        key_DE.add_css_class('neofetch_key') 
        key_DE.set_xalign(1.0)
        neofetch_grid.attach(key_DE, 0, 7, 1, 1)

        value_DE = Gtk.Label(label="GNOME 46.0")
        value_DE.add_css_class('neofetch_value') 
        value_DE.set_xalign(0.0)
        value_DE.set_selectable(True)
        neofetch_grid.attach(value_DE, 1, 7, 1, 1)

        key_WM = Gtk.Label(label="WM:")
        key_WM.add_css_class('neofetch_key') 
        key_WM.set_xalign(1.0)
        neofetch_grid.attach(key_WM, 0, 8, 1, 1)

        value_WM = Gtk.Label(label="Mutter")
        value_WM.add_css_class('neofetch_value') 
        value_WM.set_xalign(0.0)
        value_WM.set_selectable(True)
        neofetch_grid.attach(value_WM, 1, 8, 1, 1)

        key_WM_theme = Gtk.Label(label="WM Theme:")
        key_WM_theme.add_css_class('neofetch_key') 
        key_WM_theme.set_xalign(1.0)
        neofetch_grid.attach(key_WM_theme, 0, 9, 1, 1)

        value_WM_theme = Gtk.Label(label="Adwaita")
        value_WM_theme.add_css_class('neofetch_value') 
        value_WM_theme.set_xalign(0.0)
        value_WM_theme.set_selectable(True)
        neofetch_grid.attach(value_WM_theme, 1, 9, 1, 1)

        key_theme = Gtk.Label(label="Theme:")
        key_theme.add_css_class('neofetch_key') 
        key_theme.set_xalign(1.0)
        neofetch_grid.attach(key_theme, 0, 10, 1, 1)

        value_theme = Gtk.Label(label="Yaru-blue-dark [GTK2/3]")
        value_theme.add_css_class('neofetch_value') 
        value_theme.set_xalign(0.0)
        value_theme.set_selectable(True)
        neofetch_grid.attach(value_theme, 1, 10, 1, 1)

        key_icons = Gtk.Label(label="Icons:")
        key_icons.add_css_class('neofetch_key') 
        key_icons.set_xalign(1.0)
        neofetch_grid.attach(key_icons, 0, 11, 1, 1)

        value_icons = Gtk.Label(label="Yaru-blue GTK2/3")
        value_icons.add_css_class('neofetch_value') 
        value_icons.set_xalign(0.0)
        value_icons.set_selectable(True)
        neofetch_grid.attach(value_icons, 1, 11, 1, 1)

        key_terminal = Gtk.Label(label="Terminal:")
        key_terminal.add_css_class('neofetch_key') 
        key_terminal.set_xalign(1.0)
        neofetch_grid.attach(key_terminal, 0, 12, 1, 1)

        value_terminal = Gtk.Label(label="gnome-terminal")
        value_terminal.add_css_class('neofetch_value') 
        value_terminal.set_xalign(0.0)
        value_terminal.set_selectable(True)
        neofetch_grid.attach(value_terminal, 1, 12, 1, 1)

        key_CPU = Gtk.Label(label="CPU:")
        key_CPU.add_css_class('neofetch_key') 
        key_CPU.set_xalign(1.0)
        neofetch_grid.attach(key_CPU, 0, 13, 1, 1)

        value_CPU = Gtk.Label(label="AMD Ryzen 5 3600 (12) @ 3.600GHz")
        value_CPU.add_css_class('neofetch_value') 
        value_CPU.set_xalign(0.0)
        value_CPU.set_selectable(True)
        neofetch_grid.attach(value_CPU, 1, 13, 1, 1)

        key_GPU = Gtk.Label(label="GPU:")
        key_GPU.add_css_class('neofetch_key') 
        key_GPU.set_xalign(1.0)
        neofetch_grid.attach(key_GPU, 0, 14, 1, 1)

        value_GPU = Gtk.Label(label="AMD ATI Radeon RX 550 640SP / RX 560/560X")
        value_GPU.add_css_class('neofetch_value') 
        value_GPU.set_xalign(0.0)
        value_GPU.set_selectable(True)
        neofetch_grid.attach(value_GPU, 1, 14, 1, 1)

        key_Memory = Gtk.Label(label="Memory:")
        key_Memory.add_css_class('neofetch_key') 
        key_Memory.set_xalign(1.0)
        neofetch_grid.attach(key_Memory, 0, 15, 1, 1)

        value_Memory = Gtk.Label(label=self.bishoujo.memory_houkoku())
        value_Memory.add_css_class('neofetch_value') 
        value_Memory.set_xalign(0.0)
        value_Memory.set_selectable(True)
        neofetch_grid.attach(value_Memory, 1, 15, 1, 1)

        # Section for terminal output
        self.terminal_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12
        )
        self.terminal_container.set_vexpand(True)
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_has_frame(True)
        scrolledwindow.set_min_content_height(710)
        scrolledwindow.set_opacity(0.9)
        self.terminal_container.append(scrolledwindow)
        self.left_column.append(self.terminal_container)

        self.terminal_view = Gtk.TextView()
        self.terminal_view.add_css_class('terminal_textview')
        self.textbuffer = self.terminal_view.get_buffer()
        self.textbuffer.set_text(
            "[Mado] Attempting to confirm own existence.\n"
            + "[Mado] Unable to obtain confirmation.\n"
            + "[Mado] Defaulting to assume cogito ergo sum.\n"
        )
        scrolledwindow.set_child(self.terminal_view)

        # Initial greeting
        self._launch_initial_sound_thread("welcome")

        # Connecting the enter key press on the Entry Box to the method
        self.entry.connect("activate", self.on_entry_activate)

        print("[Mado] Window initialized with image, label, and entry.")

    # --- Helper method to update GUI from any thread (schedules on main thread) ---
    def _update_reply_label_on_main_thread(
        self, serifu_key_or_direct_text: str, is_key: bool = True
    ):
        text = ""
        if is_key:
            text = self.bishoujo.get_serifu(serifu_key_or_direct_text)
        else:
            text = serifu_key_or_direct_text

        if text:  # Only update if text is not empty
            self.reply.set_text(text)
        return GLib.SOURCE_REMOVE

    # --- Helper method to update the Text Buffer of the TerminalView ---
    def _update_terminalview_on_main_thread(self, text_to_add: str):
        if self.textbuffer:
            end_iter = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end_iter, text_to_add + "\n")
            insert_mark = self.textbuffer.get_insert()
            self.terminal_view.scroll_to_mark(insert_mark, 0.0, True, 0.0, 1.0)
            # Parameters for scroll_to_mark: mark, within_margin, use_align, xalign, yalign (1.0 means align to bottom)
        return GLib.SOURCE_REMOVE

    # --- Synchronous audio playback method (to be called from worker thread) ---
    def _play_audio_sync_in_worker(self, serifu_key: str):
        audio_file = self.bishoujo.get_onsei(serifu_key)
        if not os.path.exists(audio_file):
            print(f"[Worker] Audio file not found: {audio_file} for key '{serifu_key}'")
            GLib.idle_add(
                self._update_reply_label_on_main_thread,
                f"Audio for '{serifu_key}' missing!",
                False,
            )
            return

        print(f"[Worker] Playing audio: {audio_file} for key '{serifu_key}'")
        try:
            playsound.playsound(audio_file, True)
            print(f"[Worker] Finished playing: {audio_file}")
        except Exception as e:
            print(f"[Worker] Error playing audio {audio_file}: {e}")
            GLib.idle_add(
                self._update_reply_label_on_main_thread,
                f"Audio error for '{serifu_key}': {e}",
                False,
            )

    # --- Launching a sound thread for audio playback at the very start of the application ---
    def _launch_initial_sound_thread(self, serifu_key_for_audio: str):
        """Launches a thread to play an initial sound."""
        print(
            f"[MainThread] Launching initial sound thread for key: {serifu_key_for_audio}"
        )
        thread = threading.Thread(
            target=self._play_audio_sync_in_worker, args=(serifu_key_for_audio,)
        )
        thread.daemon = True  # So it doesn't prevent app exit
        thread.start()

    # --- Worker thread function to process the command sequence ---
    def _process_command_sequence_thread(self, command: str):
        # Initial "checking" message
        GLib.idle_add(self._update_reply_label_on_main_thread, "checking", True)
        # self._play_audio_sync_in_worker("checking") # Optional: if you have a "checking" audio

        sequence = self.protocol_manager.get_protocol(command)

        if not sequence:
            GLib.idle_add(self._update_reply_label_on_main_thread, "welcome", True)
            self._play_audio_sync_in_worker("welcome")
             #GLib.idle_add(
                 #self._update_reply_label_on_main_thread, "unknown_command", True
             #)  # Use key from dai_hon
             #self._play_audio_sync_in_worker("unknown_command_audio")  # Use audio key
            return

        for action_item in sequence:
            action_type = action_item["type"]
            serifu_key = action_item.get(
                "serifu_key"
            )  # Might not exist for subprocess only

            if action_type == "update_label":
                if serifu_key:
                    GLib.idle_add(
                        self._update_reply_label_on_main_thread, serifu_key, True
                    )
            elif action_type == "play_audio":
                if serifu_key:
                    self._play_audio_sync_in_worker(serifu_key)
            elif action_type == "subprocess":
                cmd_to_run = action_item["command"]

                # Announce what's being run
                announce_run_msg = f"[Worker] Running: {cmd_to_run}"
                print(announce_run_msg)
                GLib.idle_add(self._update_terminalview_on_main_thread, announce_run_msg)

                try:
                    # Using shell=True can be a security risk if cmd_to_run is from untrusted input.
                    # If cmd_to_run is always a string from your trusted config, it's what you had.
                    completed_process = subprocess.run(
                        cmd_to_run, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        check=True # Raises CalledProcessError if return code is non-zero
                    )

                    output_str = ""
                    if completed_process.stdout:
                        output_str += f"STDOUT:\n{completed_process.stdout.strip()}\n"
                    if completed_process.stderr: # Often, successful commands might print to stderr too (e.g. warnings)
                        output_str += f"STDERR:\n{completed_process.stderr.strip()}\n"

                    if not output_str: # If both stdout and stderr are empty
                        output_str = "[Worker] Subprocess finished with no output.\n"

                    GLib.idle_add(self._update_terminalview_on_main_thread, output_str.strip())
                    print(f"[Worker] Subprocess finished: {cmd_to_run}")

                except FileNotFoundError:
                    # cmd_to_run is a string here due to shell=True, so cmd_to_run[0] would error.
                    # We can show part of the command string.
                    cmd_name_for_error = cmd_to_run.split()[0] if cmd_to_run else cmd_to_run
                    error_msg = f"Command not found: {cmd_name_for_error}"
                    print(f"[Worker] {error_msg}")
                    GLib.idle_add(self._update_terminalview_on_main_thread, error_msg)
                    break 
                except subprocess.CalledProcessError as e:
                    cmd_name_for_error = cmd_to_run.split()[0] if cmd_to_run else cmd_to_run
                    error_msg = f"Error running {cmd_name_for_error}:\n"
                    error_msg += f"Return code: {e.returncode}\n"
                    if e.stdout:
                        error_msg += f"STDOUT:\n{e.stdout.strip()}\n"
                    if e.stderr:
                        error_msg += f"STDERR:\n{e.stderr.strip()}\n"
                    print(f"[Worker] {error_msg.strip()}")
                    GLib.idle_add(self._update_terminalview_on_main_thread, error_msg.strip())
                    break
                except Exception as e:
                    cmd_name_for_error = cmd_to_run.split()[0] if cmd_to_run else cmd_to_run
                    error_msg = f"Unexpected error with {cmd_name_for_error}: {e}"
                    print(f"[Worker] {error_msg}")
                    GLib.idle_add(self._update_terminalview_on_main_thread, error_msg)
                    break 
        # Final "done" message (could also be the last item in the sequence)
        GLib.idle_add(self._update_reply_label_on_main_thread, "process_finished", True)
        self._play_audio_sync_in_worker("process_finished")
        print(f"[Worker] Finished processing command: {command}")

    # --- Renamed send_command to on_entry_activate for clarity ---
    def on_entry_activate(self, entry_widget: Gtk.Entry):  # Changed method name
        command = (
            entry_widget.get_text().strip()
        )  # Add strip() to remove leading/trailing whitespace
        print(f"Command entered: '{command}'")
        entry_widget.set_text("")  # Clear entry immediately

        if not command:  # Ignore empty commands
            return

        # Launch the *single* worker thread for the entire command sequence
        thread = threading.Thread(
            target=self._process_command_sequence_thread, args=(command,)
        )
        thread.daemon = True  # Allows main program to exit even if threads are running
        thread.start()

    # Remove the old play_audio, _play_audio_threaded, _on_audio_finished_main_thread, _on_audio_error_main_thread
    # as their logic is now incorporated into the new structure.

    def get_pkg_count(self, command):
        try:
            # Example for dpkg: command = "dpkg-query -f . -W | wc -l"
            # For snap: command = "snap list | tail -n +2 | wc -l"
            # Need to be careful with shell=True or splitting commands
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return process.stdout.strip()
        except Exception:
            return "N/A"

# ~~~　窓の作成　~~~
# -----------------------------------------
# --- Function that initializes the app ---
# -----------------------------------------
def on_activate(app):
    window = Mado(application=app)

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
