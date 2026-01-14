from lib import TextTable

table = TextTable(style="box", horizontal_lines=True)

# Let's create MANY columns to force scrolling
for i in range(1, 40):
    table.add_column(f"Column_{i}", align="center", max_width=10)

# Add some dummy data
data = []
for r in range(5):
    row_data = [f"Data_{r}_{c}" for c in range(1, 40)]
    data.append(row_data)

table.add_rows(data)

# Launch the interactive viewer
# Note: This requires running in a real terminal, not a simple IDE output window
table.view()
