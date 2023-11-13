from bokeh.models import ColumnDataSource, NumeralTickFormatter, HoverTool
from bokeh.plotting import figure

def create_bar_chart(data: list, x_axis: str, y_axis: str, title: str) -> figure:
    try:
        # Check if data is empty and display a message if so
        if not data:
            p = figure(title=title)
            p.text(
                x=[0],
                y=[0],
                text=["No data available"],
                text_color=["black"],
                text_font_size="20pt",
                text_baseline="middle",
                text_align="center",
            )
            return p
        # Validate that data contains the expected keys and structure
        if not all([isinstance(d, dict) and x_axis in d and y_axis in d for d in data]):
            raise ValueError("Invalid data format or missing x_axis/y_axis keys.")
        # Existing visualization code
        source = ColumnDataSource(data)
        p = figure(x_range=[str(d[x_axis]) for d in data], height=400, title=title)
        p.vbar(x=x_axis, top=y_axis, width=0.5, source=source)
        p.y_range.start = 0
        p.xgrid.grid_line_color = None
        p.yaxis.formatter = NumeralTickFormatter(format="0,0")
        p.xaxis.major_label_orientation = "vertical"
        hover = HoverTool()
        hover.tooltips = [(x_axis, "@" + x_axis), (y_axis, "@" + y_axis)]
        p.add_tools(hover)
        return p
    except Exception as e:
        # Handle unexpected errors and log them
        print(f"Error creating bar chart: {e}")
        p = figure(title="Error")
        p.text(x=[0], y=[0], text=["Error creating chart"], text_color=["black"], text_font_size="20pt", text_baseline="middle", text_align="center")
        return p


