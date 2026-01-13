class TextTable:
    """
    A simple utility class to generate ASCII/Markdown style tables.
    """
    def __init__(self):
        # Stores column definitions (header name, alignment)
        self.columns = []
        # Stores the actual data rows
        self.rows = []

    def add_column(self, header_name, align="left"):
        """
        Adds a column definition to the table.
        
        Args:
            header_name (str): The text to display in the header.
            align (str): 'left', 'center', or 'right'. Defaults to 'left'.
        """
        self.columns.append({
            "header": header_name,
            "align": align
        })

    def add_row(self, *args):
        """
        Adds a row of data. 
        Arguments must match the number of columns defined.
        """
        if len(args) != len(self.columns):
            raise ValueError("Number of arguments does not match number of columns.")
        
        # Convert all items to string immediately to safely measure length later
        self.rows.append([str(item) for item in args])

    def generate(self):
        """
        Calculates widths and renders the table as a string.
        """
        if not self.columns:
            return ""

        # 1. Calculate the maximum width for each column
        # Start with the header length
        col_widths = [len(col["header"]) for col in self.columns]

        # Check every row to see if data is wider than the header
        for row in self.rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        # 2. Define helper to format a single line based on alignment map
        # Mapping readable names to f-string format specifiers
        align_map = {"left": "<", "center": "^", "right": ">"}

        def format_row(row_data):
            cells = []
            for i, cell_text in enumerate(row_data):
                width = col_widths[i]
                align = align_map.get(self.columns[i]["align"], "<")
                # Format: " {text:<width} " (padded with spaces)
                cells.append(f" {cell_text:{align}{width}} ")
            return "|" + "|".join(cells) + "|"

        # 3. Build the table string
        lines = []
        
        # Header row
        header_names = [col["header"] for col in self.columns]
        lines.append(format_row(header_names))

        # Separator row (e.g., "|---|---|")
        separators = []
        for width in col_widths:
            # Add 2 to width because we add a space padding on left and right
            separators.append("-" * (width + 2))
        lines.append("|" + "|".join(separators) + "|")

        # Data rows
        for row in self.rows:
            lines.append(format_row(row))

        return "\n".join(lines)
    