import pandas as pd
import io

def parse_latency_output(output):
    # Split the output into lines
    lines = output.strip().split('\n')
    
    # Find the index of the line with column headers
    header_index = next(i for i, line in enumerate(lines) if line.startswith('# Size'))
    
    # Extract the data lines (skipping headers)
    data_lines = lines[header_index + 1:]
    
    # Create a string that looks like a CSV, with the header
    csv_string = "Size(B) Lat(us)\n" + '\n'.join(data_lines)
    
    # Use pandas to read the CSV-like string
    df = pd.read_csv(io.StringIO(csv_string), sep=r'\s+')

    # Set size to be the index
    df.set_index('Size(B)', inplace=True)

    return df

def create_stat_df(df_list):
    all = pd.concat(df_list, axis=1)
    all["AvgLat(us)"] = all.filter(regex=r'^Lat').mean(axis=1)
    all["MinLat(us)"] = all.filter(regex=r'^Lat').min(axis=1)
    all["MaxLat(us)"] = all.filter(regex=r'^Lat').max(axis=1)
    all["StdLat(us)"] = all.filter(regex=r'^Lat').std(axis=1)

    return all