from flask import Flask, render_template, request, jsonify
import numpy as np
import plotly.graph_objs as go

app = Flask(__name__)

def calculate_positions(room_length, room_width, rows, cols, shelves, custom_distances):
    adjusted_length = room_length - shelves['north'] - shelves['south']
    adjusted_width = room_width - shelves['east'] - shelves['west']

    if custom_distances['top_bottom'] > 0:
        y_positions = np.linspace(shelves['south'] + custom_distances['top_bottom'],
                                  room_length - shelves['north'] - custom_distances['top_bottom'],
                                  rows)
    else:
        y_positions = np.linspace(shelves['south'], room_length - shelves['north'], rows + 1)[1:-1]

    if custom_distances['left_right'] > 0:
        x_positions = np.linspace(shelves['west'] + custom_distances['left_right'],
                                  room_width - custom_distances['left_right'] - shelves['east'],
                                  cols)
    else:
        x_positions = np.linspace(shelves['west'], room_width - shelves['east'], cols + 1)[1:-1]

    return x_positions, y_positions

def create_plot(x_positions, y_positions, room_length, room_width, shelves):
    fig = go.Figure()

    # Add the scatter points (downlight positions)
    X, Y = np.meshgrid(x_positions, y_positions)
    fig.add_trace(go.Scatter(
        x=X.flatten(),
        y=Y.flatten(),
        mode='markers',
        marker=dict(size=10, color='blue'),
        name='Downlights'
    ))

    # Add grid lines to match exactly with the x and y positions
    for x in x_positions:
        fig.add_shape(type="line", x0=x, y0=0, x1=x, y1=room_length, line=dict(color="grey", width=1, dash="dash"))
    for y in y_positions:
        fig.add_shape(type="line", x0=0, y0=y, x1=room_width, y1=y, line=dict(color="grey", width=1, dash="dash"))

    # Draw shelves as rectangles
    if shelves['north'] > 0:
        fig.add_shape(type="rect", x0=0, y0=room_length - shelves['north'], x1=room_width, y1=room_length,
                      fillcolor="grey", opacity=0.5, line_width=0)
    if shelves['south'] > 0:
        fig.add_shape(type="rect", x0=0, y0=0, x1=room_width, y1=shelves['south'],
                      fillcolor="grey", opacity=0.5, line_width=0)
    if shelves['east'] > 0:
        fig.add_shape(type="rect", x0=room_width - shelves['east'], y0=0, x1=room_width, y1=room_length,
                      fillcolor="grey", opacity=0.5, line_width=0)
    if shelves['west'] > 0:
        fig.add_shape(type="rect", x0=0, y0=0, x1=shelves['west'], y1=room_length,
                      fillcolor="grey", opacity=0.5, line_width=0)

    # Draw the room outline
    fig.add_shape(type="rect", x0=0, y0=0, x1=room_width, y1=room_length,
                  line=dict(color="black", width=2))

    # Annotate distances with corrected arrow positions
    for i, x in enumerate(x_positions):
        if i == 0:
            fig.add_annotation(x=x, y=shelves['south'] + (room_length * 0.1), text=f"{x - shelves['west']:.2f}",
                               showarrow=True, arrowhead=2, arrowsize=1, arrowcolor="red", ax=0, ay=-30, xanchor="center")
        else:
            prev_x = x_positions[i - 1]
            fig.add_annotation(x=(x + prev_x) / 2, y=shelves['south'] + (room_length * 0.1), text=f"{x - prev_x:.2f}",
                               showarrow=True, arrowhead=2, arrowsize=1, arrowcolor="blue", ax=0, ay=-30, xanchor="center")

    for j, y in enumerate(y_positions):
        if j == 0:
            fig.add_annotation(x=shelves['west'] + (room_width * 0.1), y=y, text=f"{y - shelves['south']:.2f}",
                               showarrow=True, arrowhead=2, arrowsize=1, arrowcolor="green", ax=-30, ay=0, yanchor="middle")
        else:
            prev_y = y_positions[j - 1]
            fig.add_annotation(x=shelves['west'] + (room_width * 0.1), y=(y + prev_y) / 2, text=f"{y - prev_y:.2f}",
                               showarrow=True, arrowhead=2, arrowsize=1, arrowcolor="purple", ax=-30, ay=0, yanchor="middle")

    # Define maximum width and height
    max_width = 1000
    max_height = 1000

    # Calculate aspect ratio
    aspect_ratio = room_length / room_width

    # Adjust width and height based on aspect ratio
    if aspect_ratio > 1:  # Taller than wide
        height = max_height
        width = max_width / aspect_ratio
    else:  # Wider than tall
        width = max_width
        height = max_height * aspect_ratio

    fig.update_layout(
        title='Downlight Positions',
        xaxis=dict(range=[0, room_width], title='Width (m)', constrain='domain', fixedrange=True),
        yaxis=dict(range=[0, room_length], title='Length (m)', fixedrange=True),
        showlegend=False,
        width=width,
        height=height,
        plot_bgcolor='white',
        dragmode=False,  # Disable dragging
        hovermode='closest',  # Force closest data point on hover
        spikedistance=-1,  # Force spike lines on
    )

    # Ensure spike lines are always on and cannot be toggled off
    fig.update_xaxes(showspikes=True, spikemode='across', spikethickness=1)
    fig.update_yaxes(showspikes=True, spikemode='across', spikethickness=1)

    # Disable the mode bar options for lasso, box select, hover, and spike lines
    fig.update_layout(
        dragmode='pan',  # Set default drag mode to pan or you can use 'zoom'
        modebar_remove=['toggleSpikelines', 'hoverClosestCartesian', 'select2d', 'lasso2d']
    )

    return fig


    return fig

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        room_length = float(data['room_length']) if data['room_length'] else 0.0
        room_width = float(data['room_width']) if data['room_width'] else 0.0
        rows = int(data['rows'])+1 if data['rows'] else 1
        cols = int(data['cols'])+1 if data['cols'] else 1

        shelves = {
            'north': float(data['north_shelf']) if data['north_shelf'] else 0.0,
            'south': float(data['south_shelf']) if data['south_shelf'] else 0.0,
            'east': float(data['east_shelf']) if data['east_shelf'] else 0.0,
            'west': float(data['west_shelf']) if data['west_shelf'] else 0.0
        }

        custom_distances = {
            'top_bottom': float(data['top_bottom_distance']) if data['top_bottom_distance'] else 0.0,
            'left_right': float(data['left_right_distance']) if data['left_right_distance'] else 0.0
        }

        x_positions, y_positions = calculate_positions(room_length, room_width, rows, cols, shelves, custom_distances)
        fig = create_plot(x_positions, y_positions, room_length, room_width, shelves)
        graph_json = fig.to_json()

        return jsonify(graph_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
