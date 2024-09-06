#!/usr/bin/env python

import argparse
import subprocess
import pandas as pd
import sys
from omb.parse_lat import *
from tqdm import tqdm

def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print("Error output:")
        print(e.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run OMB and parse the output to excel")
    parser.add_argument("-i", "--iters", type=int, default=2, help="number of iterations to run the command")
    parser.add_argument("-c", "--command", nargs=1, required=True, help="The command to run")
    parser.add_argument("-o", "--output", nargs=1, required=False, help="Output *.xlsx file to save to (.xlsx will be appended automatically)")
    args = parser.parse_args()

    dfs = []
    for _ in tqdm(range(args.iters), desc=f"Running command {args.iters} times"):
        out = run_command(args.command[0].split(' '))
        df = parse_latency_output(out)
        dfs.append(df)

    stats = create_stat_df(dfs)
    print(stats)
    if args.output:
        name = args.output[0]
        print(f"Saving to {name}.xlsx")
        stats.to_excel(name + ".xlsx")

if __name__ == "__main__":
    main()
