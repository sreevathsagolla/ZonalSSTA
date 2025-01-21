import mpld3
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import numpy as np
from matplotlib.widgets import Button
import mplcursors

def lat_parser(lat_range):
    """Parses latitude range into a readable string format."""
    lat_min, lat_max = lat_range
    lat_str = f"{abs(lat_min)}˚{'N' if lat_min > 0 else 'S'}"
    lat_str += f" - {abs(lat_max)}˚{'N' if lat_max > 0 else 'S'}"
    return lat_str

# Load data
df = pd.read_csv('ZONAL_CONTRIBUTIONS.csv')
df['TIME'] = pd.to_datetime(df['TIME'])
df.set_index('TIME', inplace=True)
df = df[~((df.index.month == 2) & (df.index.day == 29))]  # Remove leap days

doy = {str(x)[5:10]: i for i, x in enumerate(pd.date_range('1901-01-01', '1901-12-31', freq='1D'), 1)}

# Define regions
regions = {
    "Polar (N)": ((66.5, 90), "blue"),
    "High-Latitudes (N)": ((55, 66.5), "purple"),
    "Mid-Latitudes (N)": ((23.5, 55), "green"),
    "Tropics": ((-23.5, 23.5), "orange"),
    "Mid-Latitudes (S)": ((-55, -23.5), "green"),
    "High-Latitudes (S)": ((-66.5, -55), "purple"),
    "Polar (S)": ((-90, -66.5), "blue"),
}

# Create figure and axes
fig, axes = plt.subplots(2, 3, figsize=(20, 10))
axes = axes.flatten()
ax_map = fig.add_subplot(2, 3, 1, projection=ccrs.PlateCarree())
ax_map.set_global()
ax_map.add_feature(cfeature.LAND, color="grey")
ax_map.coastlines()

gl = ax_map.gridlines(draw_labels=True, linestyle="--", color="black", alpha=0.5)
gl.top_labels = gl.right_labels = False  

# Draw latitude regions on map
for name, (lat_range, color) in regions.items():
    lat_min, lat_max = lat_range
    ax_map.fill_betweenx([lat_min, lat_max], -180, 180, color=color, alpha=0.3)
    ax_map.text(
        0, (lat_min + lat_max) / 2, f"{name.split()[0]} ({lat_parser(lat_range)})",
        ha='center', va='center', fontsize=6,
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'),
        transform=ccrs.PlateCarree()
    )
ax_map.set_title("Latitude Regions of Earth with Other Plots")
axes[0].axis('off')

# Dictionary to store line objects
lines = {}

# Plot data
for reg, ax in zip(df.columns, axes[1:]):
    for year in range(1981, 2025):
        color, alpha = ('orange', 1) if year == 2024 else ('black', 1) if year == 2023 else ('grey', 0.2)
        line, = ax.plot(
            [doy[str(x)[5:10]] for x in df[df.index.year == year].index],
            df[df.index.year == year][reg],
            color=color, alpha=alpha, label=str(year), visible=True
        )
        lines.setdefault(str(year), []).append(line)
    
    ax.set_title(reg)
    ax.set_xticks([doy[str(x)[5:10]] for x in pd.date_range('1901-01-01', '1901-12-31', freq='1MS')])
    ax.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
    ax.grid()

fig.tight_layout(rect=[0, 0.20, 1, 1])  # Adjust layout

# Buttons for toggling visibility
show_ax, hide_ax = plt.axes([0.35, 0.15, 0.15, 0.05]), plt.axes([0.55, 0.15, 0.15, 0.05])
show_button, hide_button = Button(show_ax, "Show all"), Button(hide_ax, "Hide all")

# Create legend
legend = fig.legend(lines.keys(), loc="lower center", title="Years", frameon=True, ncol=15, fontsize=8)
for legline in legend.get_lines():
    legline.set_linewidth(4)
    legline.set_picker(2)

# Functions to show/hide all lines
def show_all(event):
    for line_list in lines.values():
        for line in line_list:
            line.set_visible(True)
    for legline in legend.get_lines():
        legline.set_alpha(1.0)  # Reset legend opacity
    fig.canvas.draw()
    
def toggle_visibility(event, show=True):
    """Show or hide all lines."""
    for line_list in lines.values():
        for line in line_list:
            line.set_visible(show)
    for legline in legend.get_lines():
        legline.set_alpha(1.0 if show else 0.2)
    fig.canvas.draw()

def on_legend_click(event):
    """Toggle visibility of individual lines when clicking legend items."""
    for legline, (year, line_list) in zip(legend.get_lines(), lines.items()):
        if event.artist == legline:
            visible = not line_list[0].get_visible()
            for line in line_list:
                line.set_visible(visible)
            legline.set_alpha(1.0 if visible else 0.2)
            fig.canvas.draw()

fig.canvas.mpl_connect("pick_event", on_legend_click)

show_button.on_clicked(lambda event: toggle_visibility(event, True))
hide_button.on_clicked(lambda event: toggle_visibility(event, False))

# Enable mplcursors for tooltips
cursor = mplcursors.cursor(hover=True)
@cursor.connect("add")
def on_hover(sel):
    sel.annotation.set_text(f"SSTA: {sel.target[1]:.3f}\nDOY: {sel.target[0]:.1f}")
    sel.annotation.get_bbox_patch().set(fc="white", ec="black", boxstyle="round,pad=0.3")

# Ensure all lines start as visible
show_all(None)

# Show plot
plt.show()

html_str = mpld3.fig_to_html(fig)
Html_file= open("index.html","w")
Html_file.write(html_str)
Html_file.close()
