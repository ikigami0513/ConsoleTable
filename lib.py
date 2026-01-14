import os
import sys
import textwrap

class InputHelper:
    """Helper to detect key presses on Windows and Linux without hitting Enter."""
    @staticmethod
    def get_key():
        # --- WINDOWS ---
        if os.name == 'nt':
            import msvcrt
            # msvcrt.kbhit() permet de vérifier si une touche est pressée sans bloquer,
            # mais ici on veut bloquer (attendre une touche).
            key = msvcrt.getch()
            
            # Les flèches sont des touches spéciales préfixées par \xe0 ou \x00
            if key in (b'\xe0', b'\x00'): 
                try:
                    key = msvcrt.getch()
                    # Codes courants : M=Droite, K=Gauche, H=Haut, P=Bas
                    if key == b'M': return 'right'
                    if key == b'K': return 'left'
                except Exception:
                    return None
            
            # Gestion touche 'q' ou 'Q'
            if key.lower() == b'q': return 'q'
            return None

        # --- LINUX / MAC ---
        else:
            import tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                
                if ch == 'q': return 'q'
                
                if ch == '\x1b': # Escape sequence start
                    # On lit les 2 caractères suivants pour voir si c'est une flèche
                    ch2 = sys.stdin.read(1)
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'C': return 'right'
                    if ch3 == 'D': return 'left'
                return None
            except Exception:
                return None
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class TextTable:
    """
    A utility class to generate tables with customizable border styles and sorting.
    """
    
    STYLES = {
        "markdown": {
            "h_line": "-", "v_line": "|", 
            "corner": "|", "intersect": "|" 
        },
        "box": {
            "h_line": "─", "v_line": "│",
            "top_left": "┌", "top_right": "┐", "top_intersect": "┬",
            "bot_left": "└", "bot_right": "┘", "bot_intersect": "┴",
            "mid_left": "├", "mid_right": "┤", "mid_intersect": "┼",
            "corner": "+", "intersect": "┼" 
        }
    }

    def __init__(self, horizontal_lines=False, style="markdown"):
        self.columns = []
        self.rows = []
        self.horizontal_lines = horizontal_lines
        self.style = self.STYLES.get(style, self.STYLES["markdown"])
        self.style_name = style

    def add_column(self, header_name, align="left", max_width=None, overflow="truncate"):
        self.columns.append({
            "header": header_name, "align": align,
            "max_width": max_width, "overflow": overflow
        })

    def add_row(self, *args):
        if len(args) != len(self.columns):
            raise ValueError(f"Expected {len(self.columns)} columns.")
        # We store everything as string for display safety
        self.rows.append([str(item) for item in args])

    def add_rows(self, data_list):
        for row in data_list:
            self.add_row(*row)

    def sort_by(self, header_name, key=None, reverse=False):
        """
        Sorts the rows in-place based on a specific column.

        Args:
            header_name (str): The name of the column to sort by.
            key (callable, optional): A function to transform the data before sorting.
                                      Useful for sorting numbers stored as strings.
                                      e.g., key=int, key=float.
            reverse (bool): If True, sorts in descending order.
        """
        # 1. Find the index of the column
        col_idx = -1
        for i, col in enumerate(self.columns):
            if col["header"] == header_name:
                col_idx = i
                break
        
        if col_idx == -1:
            raise ValueError(f"Column '{header_name}' not found.")

        # 2. Define the sorting strategy
        # If no key is provided, we sort by the string value naturally
        if key is None:
            sort_func = lambda row: row[col_idx]
        else:
            # If a key is provided (like int), we apply it to the value 
            # safely to handle potential conversion errors without crashing
            def sort_func(row):
                val = row[col_idx]
                try:
                    return key(val)
                except ValueError:
                    # Fallback for unconvertible data (keeps them at the end or beginning)
                    return val

        # 3. Apply sort
        self.rows.sort(key=sort_func, reverse=reverse)

    def _process_cell(self, text, col_idx):
        col_def = self.columns[col_idx]
        limit = col_def["max_width"]
        mode = col_def["overflow"]

        if not limit or mode == 'ignore': return [text]
        if mode == 'truncate':
            return [text[:limit-3] + "..."] if len(text) > limit else [text]
        if mode == 'wrap':
            wrapped = textwrap.wrap(text, width=limit)
            return wrapped if wrapped else [""]
        return [text]

    def _build_separator(self, col_widths, position="middle"):
        s = self.style
        if self.style_name == "markdown":
            sep_parts = ["-" * (w + 2) for w in col_widths]
            return "|" + "|".join(sep_parts) + "|"

        if position == "top":
            left, right, cross = s["top_left"], s["top_right"], s["top_intersect"]
        elif position == "bottom":
            left, right, cross = s["bot_left"], s["bot_right"], s["bot_intersect"]
        else: 
            left, right, cross = s["mid_left"], s["mid_right"], s["mid_intersect"]

        line_parts = [s["h_line"] * (w + 2) for w in col_widths]
        return left + cross.join(line_parts) + right

    def generate(self):
        if not self.columns: return ""

        col_widths = []
        for i, col in enumerate(self.columns):
            limit = col["max_width"]
            header_len = len(col["header"])
            current_max = header_len
            if col["overflow"] == "wrap" and limit:
                current_max = max(header_len, limit)
            else:
                for row in self.rows:
                    cell_len = len(row[i])
                    if col["overflow"] == "truncate" and limit:
                        cell_len = min(cell_len, limit)
                    if cell_len > current_max:
                        current_max = cell_len
            col_widths.append(current_max)

        align_map = {"left": "<", "center": "^", "right": ">"}
        v_line = self.style["v_line"]

        return self._generate_subset(range(len(self.columns)))

    def _generate_subset(self, col_indices):
        """Generates the table string but ONLY for the specified column indices."""
        if not col_indices: return "No columns to display."
        
        # 1. Calculate widths for selected columns
        col_widths = []
        for real_idx in col_indices:
            col = self.columns[real_idx]
            limit = col["max_width"]
            header_len = len(col["header"])
            current_max = header_len
            
            if col["overflow"] == "wrap" and limit:
                current_max = max(header_len, limit)
            else:
                for row in self.rows:
                    cell_len = len(row[real_idx])
                    if col["overflow"] == "truncate" and limit:
                        cell_len = min(cell_len, limit)
                    if cell_len > current_max:
                        current_max = cell_len
            col_widths.append(current_max)

        # 2. Rendering Logic
        align_map = {"left": "<", "center": "^", "right": ">"}
        v_line = self.style["v_line"]

        def format_line(line_parts):
            cells = []
            for i, part in enumerate(line_parts):
                width = col_widths[i]
                
                # CORRECTION 1 : Il faut retrouver le VRAI index pour l'alignement
                # car 'i' ici est l'index dans le sous-ensemble (0 à 19)
                # alors que l'alignement est stocké dans la colonne d'origine (ex: 30 à 49)
                real_idx = col_indices[i] 
                align = align_map.get(self.columns[real_idx]["align"], "<")
                
                cells.append(f" {part:{align}{width}} ")
            return v_line + v_line.join(cells) + v_line

        lines = []
        if self.style_name == "box":
            lines.append(self._build_separator(col_widths, "top"))

        # CORRECTION 2 : On ne prend que les headers du sous-ensemble
        header_names = [self.columns[i]["header"] for i in col_indices]
        lines.append(format_line(header_names))
        
        lines.append(self._build_separator(col_widths, "middle" if self.style_name == "box" else "markdown"))

        for row_idx, row in enumerate(self.rows):
            # CORRECTION 3 : On ne traite que les cellules du sous-ensemble
            # On boucle sur 'col_indices' pour récupérer la bonne donnée dans 'row'
            formatted_cells = [self._process_cell(row[i], i) for i in col_indices]

            row_height = max(len(cell_lines) for cell_lines in formatted_cells)
            
            for line_idx in range(row_height):
                current_line_parts = []
                for i, cell_lines in enumerate(formatted_cells):
                    if line_idx < len(cell_lines):
                        current_line_parts.append(cell_lines[line_idx])
                    else:
                        current_line_parts.append("")
                lines.append(format_line(current_line_parts))

            if self.horizontal_lines and row_idx < len(self.rows) - 1:
                lines.append(self._build_separator(col_widths, "middle"))

        if self.style_name == "box":
            lines.append(self._build_separator(col_widths, "bottom"))

        return "\n".join(lines)
    
    def view(self):
        """
        Starts an interactive console viewer with horizontal scrolling.
        """
        start_col = 0
        total_cols = len(self.columns)
        last_action = "Waiting for input..." # Pour le debug
        
        while True:
            # 1. Clear Screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 2. Get Terminal Size
            try:
                # On enlève 1 ou 2 colonnes par sécurité pour éviter les sauts de ligne intempestifs
                term_width = os.get_terminal_size().columns - 2
            except OSError:
                term_width = 80
            
            # 3. Calculate visible columns
            temp_indices = []
            used_width = 4 # Borders
            
            for i in range(start_col, total_cols):
                col_header_len = len(self.columns[i]["header"])
                # Estimation large de la taille de la colonne pour l'affichage
                # (On prend 15 chars mini ou la taille du header + marge)
                est_width = max(col_header_len, 15) + 3 
                
                if used_width + est_width < term_width:
                    temp_indices.append(i)
                    used_width += est_width
                else:
                    break
            
            # Safety: always show at least one column
            if not temp_indices and start_col < total_cols:
                temp_indices.append(start_col)

            # 4. Render Interface
            print(f"VIEWER | Cols {start_col+1}-{start_col+len(temp_indices)} of {total_cols} | Terminal Width: {term_width}")
            print("Use ARROW KEYS (Left/Right) to scroll. Press 'q' to quit.")
            print("-" * term_width)
            
            # Affiche le tableau
            print(self._generate_subset(temp_indices))
            
            print("-" * term_width)
            print(f"Debug Info: {last_action}") # Affiche ce qu'il se passe

            # 5. Wait for input
            key = InputHelper.get_key()
            
            if key == 'q':
                print("Exiting viewer.")
                break
            elif key == 'right':
                if start_col + len(temp_indices) < total_cols: # Empêche de scroller dans le vide
                    start_col += 1
                    last_action = "Action: Scrolled Right"
                else:
                    last_action = "Action: End of columns reached"
            elif key == 'left':
                if start_col > 0:
                    start_col -= 1
                    last_action = "Action: Scrolled Left"
                else:
                    last_action = "Action: Already at start"
            else:
                last_action = "Action: Key ignored or unknown"
                