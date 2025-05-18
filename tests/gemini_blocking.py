# Add these imports at the top
import json
import threading # For running tasks in a separate thread

# ... (other imports: gi, os, subprocess, simpleaudio, Gtk, Gdk, Gio, GLib) ...
# SCRIPT_DIR and Bishoujo class as before

class MyWindow(Gtk.ApplicationWindow):
    def __init__(self, bishoujo: Bishoujo, **kargs):
        super().__init__(**kargs, title="Project Ouroboros")
        self.maximize()

        # --- Load Serifu Configuration ---
        self.serifu_data = {}
        serifu_config_path = os.path.join(SCRIPT_DIR, "serifu.json") # Or your chosen path
        try:
            with open(serifu_config_path, 'r', encoding='utf-8') as f:
                self.serifu_data = json.load(f)
            print(f"[MyWindow] Serifu configuration loaded from {serifu_config_path}")
        except FileNotFoundError:
            print(f"[MyWindow] ERROR: Serifu configuration file not found at {serifu_config_path}")
        except json.JSONDecodeError:
            print(f"[MyWindow] ERROR: Could not parse serifu.json")

        # Define action sequences for commands
        # Each action is a dictionary:
        # {"type": "label", "key": "serifu_key_for_text_and_audio"}
        # {"type": "audio", "key": "serifu_key_for_audio_only"} # if label is updated separately
        # {"type": "subprocess", "command": ["cmd", "arg1"], "label_key_after": "optional_serifu_key"}
        self.command_actions = {
            "アニメ": [
                {"type": "label_audio", "key": "anime_vpn"},
                {"type": "subprocess", "command": ["nordvpn", "connect", "JP732"]}, # Ensure JP732 is valid
                {"type": "label_audio", "key": "anime_store"},
                {"type": "subprocess", "command": ["google-chrome", "https://animestore.docomo.ne.jp"]},
                {"type": "label_audio", "key": "task_done"}
            ],
            "ダラダラ": [
                # Define similar sequence for "ダラダラ"
                # {"type": "label_audio", "key": "discord_start_key_from_serifu_json"},
                # {"type": "subprocess", "command": ["discord"]},
                # ...
                {"type": "label_audio", "key": "task_done"}
            ],
            "プログラミング": [
                # Define similar sequence for "プログラミング"
                {"type": "label_audio", "key": "task_done"}
            ]
            # Add more commands here
        }


        # --- UI Setup (self.canvas, image_container, etc. as before) ---
        self.canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_child(self.canvas)
        # ... (image loading code as before) ...
        image_container = Gtk.CenterBox() # Assuming this part is already correct
        self.canvas.append(image_container)
        portrait_path = bishoujo.getPortrait()
        actual_display_widget = None
        if os.path.exists(portrait_path):
            actual_display_widget = Gtk.Image.new_from_file(portrait_path)
            actual_display_widget.set_pixel_size(800) # Adjusted size
        else:
            error_label_text = f"Error: Image not found!\nPath: {portrait_path}"
            actual_display_widget = Gtk.Label(label=error_label_text)
        if actual_display_widget:
            image_container.set_center_widget(actual_display_widget)

        initial_reply_key = "welcome"
        initial_reply_text = self.serifu_data.get(initial_reply_key, {}).get("text", "ようこそ。")
        self.reply = Gtk.Label(label=initial_reply_text)
        self.reply.set_justify(Gtk.Justification.CENTER)
        self.canvas.append(self.reply)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("コマンド")
        self.entry.set_halign(Gtk.Align.CENTER)
        self.entry.set_width_chars(50)
        self.canvas.append(self.entry)
        self.entry.connect('activate', self.on_command_entered) # Changed name for clarity
        
        # Play welcome audio if available
        self._play_audio_from_key_async(initial_reply_key)


        print("[MyWindow] Window initialized.")

    def _update_reply_label_text(self, text_to_set):
        """Helper function to update label text from main thread."""
        self.reply.set_text(text_to_set)
        return GLib.SOURCE_REMOVE # Run once

    def _play_audio_from_key_sync(self, serifu_key: str):
        """Plays audio specified by key. BLOCKS. Call from a thread."""
        serifu_entry = self.serifu_data.get(serifu_key)
        if serifu_entry and "file" in serifu_entry:
            audio_file_relative = serifu_entry["file"]
            audio_path_abs = os.path.join(SCRIPT_DIR, audio_file_relative)
            if os.path.exists(audio_path_abs):
                try:
                    print(f"[Thread] Playing audio: {audio_path_abs} for key '{serifu_key}'")
                    wave_obj = simpleaudio.WaveObject.from_wave_file(audio_path_abs)
                    play_obj = wave_obj.play()
                    play_obj.wait_done()  # This blocks, but it's okay in a separate thread.
                    print(f"[Thread] Finished playing: {audio_path_abs}")
                except Exception as e:
                    print(f"[Thread] Error playing audio {audio_path_abs}: {e}")
            else:
                print(f"[Thread] Audio file not found: {audio_path_abs}")
        else:
            print(f"[Thread] No audio file found for serifu key: {serifu_key}")
            
    def _play_audio_from_key_async(self, serifu_key: str):
        """Plays audio in a new thread without blocking UI - for one-off plays"""
        thread = threading.Thread(target=self._play_audio_from_key_sync, args=(serifu_key,))
        thread.daemon = True
        thread.start()

    def _process_command_sequence_thread(self, command_key: str):
        """Worker thread function to process a sequence of actions."""
        actions = self.command_actions.get(command_key)
        if not actions:
            # Handle unknown command in thread
            unknown_key = "unknown_command"
            unknown_text = self.serifu_data.get(unknown_key, {}).get("text", "Unknown command.")
            GLib.idle_add(self._update_reply_label_text, unknown_text)
            self._play_audio_from_key_sync(unknown_key)
            return

        initial_processing_key = "processing"
        initial_processing_text = self.serifu_data.get(initial_processing_key, {}).get("text", "Processing...")
        GLib.idle_add(self._update_reply_label_text, initial_processing_text)
        # self._play_audio_from_key_sync(initial_processing_key) # Optional: play "processing" audio

        for action_index, action_config in enumerate(actions):
            action_type = action_config["type"]

            # Update label if a "key" is provided for text (for label_audio type)
            if action_type == "label_audio" and "key" in action_config:
                serifu_key = action_config["key"]
                action_text = self.serifu_data.get(serifu_key, {}).get("text", f"Step {action_index+1}...")
                GLib.idle_add(self._update_reply_label_text, action_text)
                self._play_audio_from_key_sync(serifu_key) # Play associated audio

            elif action_type == "audio" and "key" in action_config: # For audio only if label is separate
                self._play_audio_from_key_sync(action_config["key"])

            elif action_type == "subprocess":
                cmd_list = action_config["command"]
                # Optional: update label before running subprocess
                # if "label_key_before" in action_config:
                #    before_text = self.serifu_data.get(action_config["label_key_before"], {}).get("text", f"Running {cmd_list[0]}...")
                #    GLib.idle_add(self._update_reply_label_text, before_text)
                #    self._play_audio_from_key_sync(action_config["label_key_before"])

                print(f"[Thread] Running subprocess: {cmd_list}")
                try:
                    subprocess.run(cmd_list, check=True, capture_output=True) # capture_output to prevent terminal spam if not needed
                    print(f"[Thread] Subprocess finished: {cmd_list}")
                    # Optional: update label after subprocess
                    if "label_key_after" in action_config:
                        after_key = action_config["label_key_after"]
                        after_text = self.serifu_data.get(after_key, {}).get("text", f"{cmd_list[0]} finished.")
                        GLib.idle_add(self._update_reply_label_text, after_text)
                        self._play_audio_from_key_sync(after_key)
                except subprocess.CalledProcessError as e:
                    print(f"[Thread] Error running subprocess {cmd_list}: {e}")
                    error_text = f"Error with {cmd_list[0]}: {e.stderr.decode() if e.stderr else e}"
                    GLib.idle_add(self._update_reply_label_text, error_text)
                    # self._play_audio_from_key_sync("error_key_from_serifu") # Play error sound
                    break # Stop sequence on error
                except FileNotFoundError as e:
                    print(f"[Thread] Command not found for subprocess {cmd_list}: {e}")
                    error_text = f"Command not found: {cmd_list[0]}"
                    GLib.idle_add(self._update_reply_label_text, error_text)
                    break


        # Final "done" message/audio is handled by the last item in the actions list.
        # If you want a generic one if not specified, add it here.
        # Example: GLib.idle_add(self._update_reply_label_text, self.serifu_data.get("task_done", {}).get("text", "Done!"))
        # self._play_audio_from_key_sync("task_done")

    def on_command_entered(self, entry_widget: Gtk.Entry): # Renamed from send_command
        command_text = entry_widget.get_text().lower().strip()
        print(f"Command entered by user: '{command_text}'")
        entry_widget.set_text("") # Clear entry immediately

        if not command_text:
            return # Ignore empty commands

        # Launch the processing in a separate thread so the GUI doesn't freeze
        thread = threading.Thread(target=self._process_command_sequence_thread, args=(command_text,))
        thread.daemon = True # Allows main program to exit even if threads are running
        thread.start()

# --- on_activate function ---
def on_activate(app):
    usagi = Bishoujo("usagi") # Or your character's name
    # Make sure this image exists or adjust the path
    image_relative_path = "images/usagi_miko_neutral.png" # Example filename
    image_full_path = os.path.join(SCRIPT_DIR, image_relative_path)
    usagi.setPortrait(image_full_path)
    print(f"[on_activate] Portrait path set to {usagi.getPortrait()}")

    window = MyWindow(usagi, application=app)

    # Styling (as before)
    css_provider = Gtk.CssProvider()
    style_relative_path = "style.css" # Ensure this file exists
    style_full_path = os.path.join(SCRIPT_DIR, style_relative_path)
    try:
        if os.path.exists(style_full_path):
            css_provider.load_from_path(style_full_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            print(f"[on_activate] CSS style loaded from {style_full_path}")
        else:
            print(f"[on_activate] CSS file not found at {style_full_path}, using default styles.")
    except GLib.Error as e:
        print(f"Error loading CSS file: {e.message}")
    
    window.set_decorated(False) # If you want a borderless window
    window.present()

# --- Main application setup ---
app = Gtk.Application(application_id="com.example.App.OuroborosMiko") # Unique ID
app.connect("activate", on_activate)
app.run(None)
