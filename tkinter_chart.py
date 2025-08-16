from tkhtmlview import HTMLLabel
import plotly.graph_objects as go
import tkinter as tk

fig = go.Figure(data=[go.Candlestick(
    x=["2025-07-18","2025-07-21"],
    open=[321.66, 334.39],
    high=[330.89, 338.00],
    low=[321.42, 326.88],
    close=[329.64, 328.48]
)])
fig.update_layout(title="TSLA Candlestick")
fig.write_html("temp_chart.html")

root = tk.Tk()
with open("temp_chart.html", "r") as f:
    html_content = f.read()

html_label = HTMLLabel(root, html=html_content)
html_label.pack(fill="both", expand=True)

root.mainloop()