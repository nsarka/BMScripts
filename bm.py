#!/usr/bin/env python

import argparse
import subprocess
import sys
from omb.parse_lat import *
from excel.excel import *
from tqdm import tqdm
from jinja2 import Environment, FileSystemLoader

def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print("Error output:")
        print(e.stderr)
        sys.exit(1)

def get_cmd_dfs(iters, command_str):
    dfs = []
    #for _ in tqdm(range(iters), desc=f"Running command {iters} times"):
    for _ in range(iters):
        out = run_command(command_str.split(' '))
        df = parse_latency_output(out)
        dfs.append(df)
    return dfs

def run_and_save(command, iters, sheetname, output):
    dfs = get_cmd_dfs(iters, command)
    stats = create_stat_df(dfs)
    print()
    print(command)
    print(stats)
    save_to_excel(output, command, stats, sheetname)

# Runfile takes in ';'-separated lines. Lines starting with # are comments. Whitespace lines allowed
# Each line has:
#  - A command
#  - Number of iterations for this command
#  - The name of the excel sheet this command's stats should be appended to
def parse_and_run_runfile(runfile, outfile, dry_run):
    jinja_env = Environment(loader = FileSystemLoader('.'))
    template = jinja_env.get_template('runfile')
    output = template.render()

    if dry_run is True:
        print(output)
        sys.exit(0)

    output = output.split('\n')
    output = list(filter(None, output)) # Remove everything that doesnt evaluate to True in each line, e.g. elements like ''
    for line in tqdm(output, desc=f"Running commands from {runfile}", unit="cmd"):
        if line.startswith('#') or line.isspace():
            continue

        # Strip whitespace and split the line by semicolon
        parts = line.strip().split(';')

        # Check if the line has the correct number of parts
        if len(parts) != 3:
            print(f"Warning: Skipping invalid line: {line}")
            continue
        
        # Unpack the parts
        command, iters_str, sheetname = parts
        
        # Try to convert the second part to an integer
        try:
            iters = int(iters_str.strip())
        except ValueError:
            print(f"Warning: Invalid integer in line: {line}")
            continue

        run_and_save(command.strip(), iters, sheetname.strip(), outfile)

def main():
    parser = argparse.ArgumentParser(description="Run OMB and parse the output to excel")
    parser.add_argument("-o", "--outfile", nargs=1, required=True, help="Output *.xlsx file to save to (.xlsx will be appended automatically)")
    parser.add_argument("-r", "--runfile", nargs=1, required=True, help="Parse and run this file")
    parser.add_argument("--dryrun", action='store_true', help="Just print parsed runfile")
    args = parser.parse_args()

    parse_and_run_runfile(args.runfile[0], args.outfile[0], args.dryrun)

if __name__ == "__main__":
    main()
