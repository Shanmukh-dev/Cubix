ESCAPE = '\033['
OSC_ESCAPE = '\033]'

class ForegroundColor:
    BLACK = f'{ESCAPE}90m'
    RED  = f'{ESCAPE}91m'
    GREEN = f'{ESCAPE}92m'
    YELLOW = f'{ESCAPE}93m'
    BLUE = f'{ESCAPE}94m'
    MEGANTA = f'{ESCAPE}95m'
    CYAN = f'{ESCAPE}96m'
    WHITE = f'{ESCAPE}97m'


class BackgroundColor:
    BLACK = f'{ESCAPE}100m'
    RED  = f'{ESCAPE}101m'
    GREEN = f'{ESCAPE}102m'
    YELLOW = f'{ESCAPE}103m'
    BLUE = f'{ESCAPE}104m'
    MEGANTA = f'{ESCAPE}105m'
    CYAN = f'{ESCAPE}106m'
    WHITE = f'{ESCAPE}107m'


class Color:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    REVERSED = '\033[7m'
    DIM = '\033[2m'

    def resolve_hex(hex_color: str, layer: str, category: str = "txt") -> str:
        """
        Resolves a hex color code to an ANSI escape code for terminal colors.

        Args:
            hex_color (str): The hex color code (e.g., '#RRGGBB').

        """

        if layer == "38;2;" and hasattr(ForegroundColor, hex_color.upper()):
            return getattr(ForegroundColor, hex_color.upper())
        if layer == "48;2;" and hasattr(BackgroundColor, hex_color.upper()):
            return getattr(BackgroundColor, hex_color.upper())

        if not hex_color:
            return ""
        if category == "scr":
            return f"{OSC_ESCAPE}{'10;' if layer == '38;2;' else '11;'}{hex_color}\007"

        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            color = f"{r};{g};{b}"
            return f"{ESCAPE}{layer}{color}m"
        else:
            raise ValueError("Invalid hex color code. It should start with '#' and be in the format '#RRGGBB'.")

    def c(text: str, fg: str = "", bg: str = "") -> str:
        color_code = Color.resolve_hex(fg, "38;2;") + Color.resolve_hex(bg, "48;2;")
        return f"{color_code}{text}{Color.RESET}"

    def set_screen_color(fg: str = "", bg: str = "") -> None:
        color_code = Color.resolve_hex(fg, "38;2;", "scr") + Color.resolve_hex(bg, "48;2;", "scr")
        print(color_code, end='')

    def reset_screen_color() -> None:
        print(f"{OSC_ESCAPE}110;\007{OSC_ESCAPE}111;\007", end='')

    def clear_screen() -> None:
        print(f"{ESCAPE}2J{ESCAPE}H", end='')

    

if __name__ == "__main__":
    print(Color.c("TEST", fg="yellow"))

