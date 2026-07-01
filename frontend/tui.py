from State import AgentState
from .term_colors import *
import itertools
import time
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import Completion, Completer
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.filters import is_done
import shutil



splash_text = """ ██████╗██╗   ██╗██████╗ ██╗██╗  ██╗
██╔════╝██║   ██║██╔══██╗██║╚██╗██╔╝
██║     ██║   ██║██████╔╝██║ ╚███╔╝ 
██║     ██║   ██║██╔══██╗██║ ██╔██╗ 
╚██████╗╚██████╔╝██████╔╝██║██╔╝ ██╗
 ╚═════╝ ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═╝"""

mascot = """   ▄   ▄   
  ███████  
▀▄█ ■ ■ █▄▀
  ███████  
    ▌ ▐    """

# completionsStyle = Style.from_dict({
#     # Entire popup
#     "completion-menu": "bg:#202020 #ffffff",

#     # Normal items
#     "completion-menu.completion": "bg:#202020 #aaaaaa",

#     # Selected item
#     "completion-menu.completion.current": "bg:#4c7899 #ffffff bold",

#     # Right-hand description
#     "completion-menu.meta": "bg:#202020 #888888",

#     # Selected description
#     "completion-menu.meta.current": "bg:#4c7899 #ffffff",

#     # Scrollbar
#     "scrollbar": "bg:#303030",
#     "scrollbar.button": "bg:#888888",
# })




# def spinner(status: str = "Thinking...", style: str = "braile-classic"):
#     if status == "":
#         status = "Thinking..."
#     frames = itertools.cycle(spinners[style])


class Spinner:
    def __init__(self, style: str = "braile-classic"):
        self.running = False
        self.spinners = {
            "braile-classic": "⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏".split(),
            "braile-dense": "⣷ ⣯ ⣟ ⡿ ⢿ ⣻ ⣽ ⣾".split(),
            "braile-inf": "⠋ ⠙ ⠚ ⠞ ⠖ ⠦ ⠴ ⠲ ⠳ ⠓".split(),
            "wave1": "⠁⠂⠄⡀ ⠂⠁⠄⡀ ⠄⠂⠁⡀ ⡀⠄⠂⠁ ⡀⠄⠁⠂ ⡀⠁⠂⠄ ⠁⠂⠄⡀".split(),
            "wave2": "⠁⡀⡀⡀ ⠁⡀⡀⡀ ⡀⠁⡀⡀ ⡀⡀⠁⡀ ⡀⡀⡀⠁".split(),
            "moon": "🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘".split(),
            "earth": "🌍 🌎 🌏 🌍 🌎 🌏".split(),
            "circle": "◜ ◠ ◝ ◞ ◡ ◟".split()
        }

        self.style = style

    def start(self):
        # print()
        frames = itertools.cycle(self.spinners.get(self.style))
        while self.running:
            # sys.stdout.write("\033[1A")
            sys.stdout.write(f"\r{next(frames)} Thinking...")
            sys.stdout.flush()

        else:
            sys.stdout.write("\r")
            sys.stdout.flush()

    
class SlashCompleter(Completer):
    
    def __init__(self, commands):
        super().__init__()
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only show completions if the input starts with "/"
        if not text.startswith("/"):
            return

        for cmd in self.commands:
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                )










class TUI:
    
    def __init__(self, bg: str, fg: str, accent_color: str, state: AgentState, slash_commands: list[str], ai):
        self.bg = bg
        self.fg = fg
        self.state = state
        self.ai = ai
        self.width = shutil.get_terminal_size().columns
        self.slash_commands = slash_commands
        self.accent_color = accent_color
        self.error = ForegroundColor.RED
        self.warning = ForegroundColor.YELLOW
        self.success = ForegroundColor.GREEN
        self.white = "#ffffff"
        self.init_ui()

    def init_ui(self):
        Color.clear_screen()
        self.display_splash_screen()
        Color.set_screen_color(bg = self.bg, fg = self.fg)
        

    def display_splash_screen(self):
        mascot_lines = mascot.splitlines()
        splash_text_lines = splash_text.splitlines()

        height = max(len(mascot_lines), len(splash_text_lines))
        while len(splash_text_lines) < height:
            splash_text_lines.append("")
        top = (height - len(mascot_lines)) // 2
        mascot_lines = (
            [""] * top
            + mascot_lines
            + [""] * (height - top - len(mascot_lines))
        )

        combined = [
            f"{Color.c(f"{left:<15}", fg=self.accent_color)} {
                Color.c(right, fg=self.white)}"
            for right, left in zip(splash_text_lines, mascot_lines)
        ]

        for l in combined:
            print(l)
        print("─"*self.width)
        print("Current porvider:", Color.c(self.ai.provider, fg = self.accent_color))
        print("Current model:", Color.c(self.ai.model_id, fg = self.accent_color))
        print("─"*self.width)

    def select_model(self, current, available_models):
        style = Style.from_dict(
            {
                "selected-option": "fg:#b625ff bold",
                "frame.border": "#b625ff"
            }
        )

        print(Color.c("Current model:", fg="YELLOW"), Color.c(current, fg=self.accent_color))
        print()
        print(Color.c("Select a model:", fg = "#55D4FF"), "Use Ctrl+C to cancel")
        try:
            result = choice(
            message="",
            options=[(mod, mod) for mod in available_models],
            default= current,
            style=style,
            show_frame=~is_done
            )

            return result
        except KeyboardInterrupt:
            return None

    def select_provider(self, provider_list):
        style = Style.from_dict(
            {
                "selected-option": "fg:#b625ff bold",
                "frame.border": "#b625ff"
            }
        )

        print(Color.c("Select provider:", fg = "#55D4FF"), "Use Ctrl+C to cancel")
        try:
            result = choice(
            message="",
            options=[(pro, pro) for pro in provider_list],
            style=style,
            show_frame=~is_done
            )

            return result
        except KeyboardInterrupt:
            return None
    def select_session(self, sessions_list):
        style = Style.from_dict(
            {
                "selected-option": "fg:#b625ff bold",
                "frame.border": "#b625ff"
            }
        )

        print(Color.c("Select session:", fg = "#55D4FF"), "Use Ctrl+C to cancel")
        try:
            result = choice(
            message="",
            options=sessions_list,
            style=style,
            show_frame=~is_done
            )

            return result
        except KeyboardInterrupt:
            return None

    def multiline_input(self, prompt_text=""):
        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            event.current_buffer.validate_and_handle()
        @kb.add("c-j")
        def _(event):
            event.current_buffer.insert_text("\n")

        @kb.add("escape", "enter")
        def _(event):
            event.current_buffer.insert_text("\n")

        completionsStyle = Style.from_dict({
            # Entire popup
            "completion-menu": "bg:#202020 #ffffff",
        
            # Normal items
            "completion-menu.completion": "bg:#202020 #aaaaaa",
        
            # Selected item
            "completion-menu.completion.current": "bg:#4c7899 #ffffff bold",
        
            # Right-hand description
            "completion-menu.meta": "bg:#202020 #888888",
        
            # Selected description
            "completion-menu.meta.current": "bg:#4c7899 #ffffff",
        
            # Scrollbar
            "scrollbar": "bg:#303030",
            "scrollbar.button": "bg:#888888",
            })

        session = PromptSession(multiline=True, key_bindings=kb,
                                style=completionsStyle, completer=SlashCompleter(commands=self.slash_commands))

        text = session.prompt(prompt_text, multiline=True)

        return text

    def show_cursor(self):
        print("\033[?25h", end="", flush=True)
        
    def hide_cursor(self):
        print("\033[?25l", end="", flush=True)

    def tool_announcement(tool_calls, announcemets, idx):
        pass