import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

def lat_parser(lat_range = None):
    lat_range_string = ''
    if lat_range[0] > 0:
        lat_range_string = str(abs(lat_range[0]))+'˚N'
    else:
        lat_range_string = str(abs(lat_range[0]))+'˚S'
    if lat_range[1] > 0:
        lat_range_string = lat_range_string+' - '+str(abs(lat_range[0]))+'˚N'
    else:
        lat_range_string = lat_range_string+' - '+str(abs(lat_range[0]))+'˚S'
    return lat_range_string
    
df = pd.read_csv('ZONAL_CONTRIBUTIONS.csv')
doy = dict(zip([str(x)[5:10] for x in pd.date_range(start = '1901-01-01', end = '1901-12-31', freq = '1D')], np.arange(1,366)))
df['TIME'] = pd.to_datetime(df['TIME'])
df.set_index('TIME', inplace = True)
df = df[~((df.index.month == 2) & (df.index.day == 29))]


regions = {
    "Polar (N)": {"lat_range": (66.5, 90), "color": "blue"},
    "High-Latitudes (N)": {"lat_range": (55, 66.5), "color": "purple"},
    "Mid-Latitudes (N)": {"lat_range": (23.5, 55), "color": "green"},
    "Tropics": {"lat_range": (-23.5, 23.5), "color": "orange"},
    "Mid-Latitudes (S)": {"lat_range": (-55, -23.5), "color": "green"},
    "High-Latitudes (S)": {"lat_range": (-66.5, -55), "color": "purple"},
    "Polar (S)": {"lat_range": (-90, -66.5), "color": "blue"},
}

# Create figure and subplots
fig, axes = plt.subplots(3, 3, figsize=(20, 10))
#plt.subplots_adjust(bottom=0.1, right=0.85)  # Adjust space for legend and buttons
axes = axes.flatten()
ax_map = axes[0]
ax_map = fig.add_subplot(3,3,1, projection=ccrs.PlateCarree())

ax_map.set_global()
ax_map.add_feature(cfeature.LAND, color="grey")
ax_map.coastlines()

gl = ax_map.gridlines(draw_labels=True, linestyle="--", color="black", alpha=0.5)
gl.top_labels = gl.right_labels = False  

for name, info in regions.items():
    lat_min, lat_max = info["lat_range"]
    ax_map.fill_betweenx(
        [lat_min, lat_max],
        -180, 180,
        color=info["color"],
        alpha=0.3,
    )
    ax_map.text(
        0, (lat_min + lat_max) / 2, name.split(' ')[0]+' ('+lat_parser(info["lat_range"])+')',
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=6,
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'),
        transform=ccrs.PlateCarree()
    )
ax_map.set_title("Latitude Regions of Earth with Other Plots")
axes[0].axis('off')


# Store line objects for toggling
lines = {}


for reg,ax in zip(list(df.columns), axes[1:]):
    for y in range(1981,2025):
        if y == 2024:
            color = 'orange'
            alpha = 1
        elif y == 2023:
            color = 'black'
            alpha = 1
        else:
            color = 'grey'
            alpha = 0.2
        line, = ax.plot([doy[_] for _ in [str(x)[5:10] for x in df[df.index.year == y].index]], df[df.index.year == y][reg], color = color, alpha = alpha, label = y, visible=True)
        if str(y) not in lines:
            lines[str(y)] = []
        lines[str(y)].append(line)
    ax.set_title(reg)
    ax.set_xticks(ticks = [doy[_] for _ in [str(x)[5:10] for x in pd.date_range(start = '1901-01-01', end = '1901-12-31', freq = '1MS')]], labels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
    ax.grid()    

# Apply tight_layout to optimize spacing
fig.tight_layout(rect=[0, 0.20, 1, 1])  # Reserve space for buttons and legend

# Buttons: "Show all" and "Hide all" (Positioned above the legend)
show_ax = plt.axes([0.35, 0.15, 0.15, 0.05])  # "Show all" button
hide_ax = plt.axes([0.55, 0.15, 0.15, 0.05])  # "Hide all" button
show_button = Button(show_ax, "Show all")
hide_button = Button(hide_ax, "Hide all")

# Common legend below the subplots with specific styling
legend = fig.legend(lines.keys(), loc="lower center", title="Years", frameon=True, ncol=15, fontsize=8)

# Adjust legend appearance for better clickability
for legline in legend.get_lines():
    legline.set_linewidth(4)  # Make legend lines thicker

# Function to toggle visibility when clicking legend items
def on_legend_click(event):
    for legline, (year, line_list) in zip(legend.get_lines(), lines.items()):
        if event.artist == legline:
            visible = not line_list[0].get_visible()  # Check visibility from one line
            for line in line_list:
                line.set_visible(visible)  # Toggle all matching lines
            legline.set_alpha(1.0 if visible else 0.2)  # Dim legend item when hidden
            fig.canvas.draw()

# Connect event to legend items
fig.canvas.mpl_connect("pick_event", on_legend_click)

# Make legend items pickable
for legline in legend.get_lines():
    legline.set_picker(10)  # Increase picker area for easier clicking

# Functions to show/hide all lines
def show_all(event):
    for line_list in lines.values():
        for line in line_list:
            line.set_visible(True)
    for legline in legend.get_lines():
        legline.set_alpha(1.0)  # Reset legend opacity
    fig.canvas.draw()

def hide_all(event):
    for line_list in lines.values():
        for line in line_list:
            line.set_visible(False)
    for legline in legend.get_lines():
        legline.set_alpha(0.2)  # Dim legend items
    fig.canvas.draw()

# Ensure all lines start as visible
show_all(None)

# Connect buttons to functions
show_button.on_clicked(show_all)
hide_button.on_clicked(hide_all)

# Show plot
plt.show()