#!/usr/bin/env python

import argparse
import re
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import colorsys

# Function to handle debug printing
def debug_print(debug_flag, message):
    if debug_flag:
        print(message)

# Function to convert size strings to bytes
def size_to_bytes(size_str):
    units = {"b": 1, "k": 1024, "m": 1024**2, "g": 1024**3}
    match = re.match(r"(\d+)([bkmgt]?)", size_str.lower())
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")
    size, unit = match.groups()
    return int(size) * units.get(unit, 1)

# Function to parse raw runtime data with dynamic columns
def parse_runtime_data(file_path, debug=False):
    data = {}
    sizes = set()

    # Regex patterns to capture necessary information
    mpirun_pattern = re.compile(r'.*/mpirun.*--np (\d+).*--mca coll ([^ ]+),')
    header_pattern = re.compile(r'# Size\s+(.+)')  # Capturing the correct header line with 'Size'
    size_latency_pattern = re.compile(r'(\d+)\s+(.+)')

    current_np = None
    columns = []
    header_detected = False

    with open(file_path, 'r') as file:
        for line in file:
            # Check if line contains mpirun command
            mpirun_match = mpirun_pattern.match(line)
            if mpirun_match:
                current_np = int(mpirun_match.group(1))  # Capture np value
                debug_print(debug, f"Detected mpirun command with NP={current_np}")
                if current_np not in data:
                    data[current_np] = {}

            # Identify the header line that defines the column names
            header_match = header_pattern.match(line)
            if header_match:
                columns = re.split(r'\s{2,}', header_match.group(1).strip())
                header_detected = True
                debug_print(debug, f"Detected columns in file '{file_path}': {columns}")
                continue

            # Only process data lines after the header has been detected
            if header_detected:
                size_latency_match = size_latency_pattern.match(line)
                if size_latency_match and current_np:
                    size = int(size_latency_match.group(1))
                    latencies = [float(v) for v in re.split(r'\s{2,}', size_latency_match.group(2).strip())]
                    sizes.add(size)

                    if len(latencies) == len(columns):
                        data[current_np][size] = dict(zip(columns, latencies))
                        debug_print(debug, f"Size {size} latencies: {data[current_np][size]}")
                    else:
                        debug_print(debug, f"Error: Mismatch in column count for size {size} in file {file_path}")

    debug_print(debug, f"Parsed data for file '{file_path}' - Sizes: {sorted(sizes)}")
    return data, sizes, columns

# Function to save parsed data to CSV with fallback to Avg Latency if the target column is missing
def save_to_file(data, sizes, columns, input_file, target_column, fallback_column="Avg Latency(us)", debug=False):
    sizes = sorted(sizes)
    df = pd.DataFrame({'Size': sizes})

    if target_column not in columns:
        print(f"Warning: Specified column '{target_column}' not found in file '{input_file}', defaulting to '{fallback_column}'")
        target_column = fallback_column
    else:
        print(f"Using column '{target_column}' for file '{input_file}'.")

    for np, latency_data in sorted(data.items()):
        latency_list = []
        for size in sizes:
            try:
                latency_value = latency_data[size].get(target_column, None)
                latency_list.append(latency_value)
                debug_print(debug, f"NP={np}, Size={size}, {target_column}={latency_value}")
            except KeyError:
                print(f"Warning: Size {size} not found in NP={np} for file {input_file}")
                latency_list.append(None)
        df[f'NP={np}'] = latency_list

    output_filename = f'{input_file}.parsed.csv'
    df.to_csv(output_filename, index=False)
    print(f"Data successfully written to {output_filename}")

def read_files(file_list, debug=False):
    data_frames = {}
    color_mapping = {}
    base_colors = {
        'r': 'red', 'b': 'blue', 'y': 'yellow', 'o': 'orange', 'g': 'green',
        'p': 'purple', 'c': 'cyan', 'm': 'magenta', 'w': 'white', 'k': 'black',
        'a': 'aqua', 'n': 'navy', 'l': 'lime', 't': 'teal', 'v': 'violet'
    }
    color_counts = {color: 0 for color in base_colors.values()}

    def get_color_shade(base_color, count):
        rgb = mcolors.to_rgb(base_color)
        h, s, v = colorsys.rgb_to_hsv(*rgb)

        # Adjust hue slightly to create more distinct shades
        h_shift = 0.05 * count  # Shift hue by 5% for each repetition
        h = (h + h_shift) % 1.0

        # Adjust saturation and value more dramatically
        s = max(0.3, min(1.0, s - 0.3 * count))
        v = max(0.3, min(1.0, v + 0.3 * count))

        # Ensure the color change is very noticeable
        if count > 0:
            if count % 2 == 1:
                v = max(0.7, v)  # Make odd counts brighter
            else:
                s = min(0.8, s)  # Make even counts more saturated

        new_rgb = colorsys.hsv_to_rgb(h, s, v)
        return new_rgb

    for file_entry in file_list:
        if ':' in file_entry:
            file, color_code = file_entry.split(':')
            base_color = base_colors.get(color_code.lower())
            if not base_color:
                raise ValueError(f"Invalid color code '{color_code}' specified.")
        else:
            file = file_entry
            base_color = None

        parsed_csv = f"{file}.parsed.csv"
        if not os.path.isfile(parsed_csv):
            raise FileNotFoundError(f"Parsed CSV file '{parsed_csv}' not found. Please check if the parsing step completed successfully.")

        if not base_color:
            available_colors = [col for col in base_colors.values() if color_counts[col] == 0]
            if available_colors:
                base_color = available_colors[0]
            else:
                base_color = sns.color_palette("husl", sum(color_counts.values()) + 1)[-1]

        color_count = color_counts[base_color]
        color = get_color_shade(base_color, color_count)
        color_counts[base_color] += 1

        coll_name = os.path.basename(file).split('.')[1]
        df = pd.read_csv(parsed_csv)

        debug_print(debug, f"Available columns in '{parsed_csv}': {df.columns.tolist()}")

        if 'Size' not in df.columns:
            raise KeyError(f"Error: 'Size' column not found in '{parsed_csv}'. Available columns: {df.columns.tolist()}")

        data_frames[coll_name] = df.set_index('Size')
        color_mapping[coll_name] = color

    return data_frames, color_mapping

# Function to generate grid plot from the parsed data
def generate_grid_plot(data_frames, color_mapping, output_file, plot_title, annotate_limit, latency_type_label, min_size=None, max_size=None, debug=False):
    sizes = sorted(list(data_frames[next(iter(data_frames))].index), reverse=True)

    if min_size or max_size:
        sizes = [size for size in sizes if (not min_size or size >= min_size) and (not max_size or size <= max_size)]

    np_values = [col.replace("NP=", "") for col in data_frames[next(iter(data_frames))].columns.tolist()]

    grid = np.zeros((len(sizes), len(np_values)))
    collective_counts = {coll: 0 for coll in data_frames}

    total_cells = len(sizes) * len(np_values)
    annotations = np.full((len(sizes), len(np_values)), "", dtype=object)

    for i, size in enumerate(sizes):
        for j, np_val in enumerate(np_values):
            values = {}
            for coll, df in data_frames.items():
                val = df.loc[size, f"NP={np_val}"]
                values[coll] = val

            sorted_values = sorted(values.items(), key=lambda x: x[1])
            min_coll, min_val = sorted_values[0]
            grid[i, j] = list(data_frames.keys()).index(min_coll)
            collective_counts[min_coll] += 1

            if len(sorted_values) > 1:
                next_coll, next_val = sorted_values[1]
                fractional_diff = (next_val - min_val) / min_val
                if annotate_limit == "max" or fractional_diff <= float(annotate_limit):
                    annotations[i, j] = f"{fractional_diff:.1f}"

    plt.rc('font', size=11)
    plt.figure(figsize=(15, 10))
    sns.heatmap(grid, annot=annotations, fmt='', cmap=list(color_mapping.values()), cbar=False, xticklabels=np_values,
                yticklabels=sizes, linewidths=0.5, linecolor='black', annot_kws={"size": 9})

    plt.xticks(rotation=90, ha='center')
    plt.text(0.5, 1.08, latency_type_label, fontsize=13, ha='center', transform=plt.gca().transAxes, weight='bold')

    legend_patches = [mpatches.Patch(color=color, label=f"{coll} ({(collective_counts[coll] * 100) // total_cells}%)")
                      for coll, color in color_mapping.items()]
    plt.legend(handles=legend_patches, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=len(color_mapping), title='Collective')

    if annotate_limit:
        current_y_pos = len(sizes) - 0.5
        plt.text(len(np_values) + 1.5, current_y_pos, "Latency diff", fontsize=11, weight='bold')
        current_y_pos -= 1.0
        step = 1.0
        for i in range(0, 11):
            upper_bound = i / 10
            if i == 0:
                plt.text(len(np_values) + 1.5, current_y_pos, f"0.0 = less than 0.01", fontsize=10)
            else:
                lower_bound = (i - 1) / 10
                plt.text(len(np_values) + 1.5, current_y_pos, f"{upper_bound:.1f} = {lower_bound:.1f} - {upper_bound:.1f}", fontsize=10)
            current_y_pos -= step

    plt.xlabel("NP")
    plt.ylabel("Size (bytes)")
    plt.title(plot_title)

    plt.savefig(output_file, format='png', bbox_inches='tight')
    print(f"Plot successfully saved as {output_file}")

# Main function to handle parsing, saving CSVs, and generating plot
def main():
    parser = argparse.ArgumentParser(description='Parse runtime data, generate CSVs, and create a grid plot. Color codes: r (red), b (blue), y (yellow), o (orange), g (green), p (purple), c (cyan), m (magenta), w (white), k (black), a (aqua), n (navy), l (lime), t (teal), v (violet).')
    parser.add_argument('-f', '--files', required=True, help='Comma-separated list of raw input data files, optionally with color codes (e.g., file1:r,file2:g,file3).')
    parser.add_argument('-o', '--output', default='plot.png', help='Output PNG file name (default: plot.png)')
    parser.add_argument('-t', '--title', default='Title', help='Title of the plot (default: "Title")')
    parser.add_argument('-latency', '--latency', choices=['avg', 'min', 'max'], default='avg', help='Specify which latency column to use for plotting (default: avg)')
    parser.add_argument('-an', '--annotate', help='Annotate the grid with fractional differences up to a specified value (e.g., 0.5 or "max" for all)')
    parser.add_argument('-m', '--size-range', help='Specify size range to plot (e.g., "256k" or "2k:1mb")')
    parser.add_argument('-debug', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    file_list = args.files.split(',')

    column_mapping = {'avg': 'Avg Latency(us)', 'min': 'Min Latency(us)', 'max': 'Max Latency(us)'}
    latency_type_label = column_mapping[args.latency]
    target_column = latency_type_label

    min_size = None
    max_size = None
    if args.size_range:
        if ':' in args.size_range:
            min_size_str, max_size_str = args.size_range.split(':')
            min_size = size_to_bytes(min_size_str)
            max_size = size_to_bytes(max_size_str)
        else:
            max_size = size_to_bytes(args.size_range)

    parsed_files = []
    for file_entry in file_list:
        file = file_entry.split(':')[0].strip()
        if os.path.isfile(file):
            print(f"Processing file: {file}")
            data, sizes, columns = parse_runtime_data(file, debug=args.debug)
            save_to_file(data, sizes, columns, file, target_column, debug=args.debug)
            parsed_files.append(file_entry)
        else:
            print(f"File not found: {file}")

    data_frames, color_mapping = read_files(parsed_files, debug=args.debug)

    annotate_limit = args.annotate if args.annotate is not None else None

    generate_grid_plot(data_frames, color_mapping, args.output, args.title, annotate_limit, latency_type_label, min_size, max_size, debug=args.debug)

if __name__ == "__main__":
    main()

