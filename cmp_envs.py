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

def create_cmp_df(df_list):
    all = pd.concat(df_list, axis=1)
    all['Best'] = all.idxmin(axis=1)
    all['Best_val'] = pd.concat(df_list, axis=1).min(axis=1)
    return all

def run_and_print(command, iters, columnname):
    dfs = get_cmd_dfs(iters, command)
    stats = create_stat_df(dfs)
    print()
    print(command)
    print(stats)
    avglat = stats[["AvgLat(us)"]]
    return avglat.rename(columns={"AvgLat(us)" : "AvgLat(us)," + columnname})

# Runfile takes in ';'-separated lines. Lines starting with # are comments. Whitespace lines allowed
# Each line has:
#  - A command
#  - Number of iterations for this command
#  - The name of the excel sheet this command's stats should be appended to
def parse_and_run_runfile(runfile, dry_run, no_save):
    jinja_env = Environment(loader = FileSystemLoader('.'))
    template = jinja_env.get_template(runfile)
    output = template.render()

    if dry_run is True:
        print(output)
        sys.exit(0)

    output = output.split('\n')
    output = list(filter(None, output)) # Remove everything that doesnt evaluate to True in each line, e.g. elements like ''
    output = list(filter(lambda line: not line.strip().startswith('#') and not line.isspace(), output)) # Remove comments and whitespace lines
    output = [line.strip() for line in output]

    cmd_dfs = []
    has_saved = 0
    for line in tqdm(output, desc=f"Running commands from {runfile}", unit="cmd"):
        # Strip whitespace and split the line by semicolon
        parts = line.split(';')
        parts = [part.strip() for part in parts]

        # If there wasnt a save command, run whatever the line says
        if parts[0] != "save":
            # Check if the line has the correct number of parts
            if len(parts) != 3:
                print(f"Warning: Skipping invalid line: {line}")
                continue
            
            # Unpack the parts
            command, iters_str, columnname = parts
            
            # Try to convert the second part to an integer
            try:
                iters = int(iters_str)
            except ValueError:
                print(f"Warning: Invalid integer in line: {line}")
                continue

            cmd_dfs.append(run_and_print(command, iters, columnname))
        else:
            print("Found save command: ", parts)
            cmp_df = create_cmp_df(cmd_dfs)
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(cmp_df)
            comparison_name = ""
            if len(parts) > 2:
                comparison_name = parts[2]
            if not no_save:
                save_to_excel("cmp_df", comparison_name, cmp_df, parts[1])
                print("Saved to cmp_df.xlsx in sheet " + parts[1] + " with the name " + parts[2])
            has_saved = 1
            cmd_dfs = []

    # If the runfile didnt specify any save commands, save the dataframe now that we've reached the end
    if has_saved == 0:
        cmp_df = create_cmp_df(cmd_dfs)
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(cmp_df)
        if not no_save:
            save_to_excel("cmp_df", "", cmp_df, "cmp_df")

def main():
    parser = argparse.ArgumentParser(description="Run OMB and compare the output in a dataframe")
    parser.add_argument("-r", "--runfile", nargs=1, required=True, help="Parse and run this file")
    parser.add_argument("--dryrun", action='store_true', help="Just print parsed runfile")
    parser.add_argument("--nosave", action='store_true', help="Dont save to excel")
    args = parser.parse_args()

    print("comparing ", args.runfile[0])
    parse_and_run_runfile(args.runfile[0], args.dryrun, args.nosave)

if __name__ == "__main__":
    main()
