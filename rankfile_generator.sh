#!/bin/bash
 
# Usage: ./rankfile_generator <comma_separated_node_names> <ppr> <max_slots>
# Example: ./rankfile_generator node0,node1,node2 16 72
 
# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <comma_separated_node_names> <ppr> <max_slots>"
    exit 1
fi
 
# Read script arguments
node_names=$1
ppr=$2
max_slots=$3
 
# Convert comma-separated node names into an array
IFS=',' read -r -a nodes <<< "$node_names"
 
# Number of nodes
num_nodes=${#nodes[@]}
 
# Calculate slot spacing (to evenly distribute ranks across the slots)
slot_spacing=$(( max_slots / ppr ))
 
# Create or overwrite the rankfile
rankfile="rankfile.txt"
> $rankfile
 
# Generate rankfile for each node
rank=0
for (( node_idx=0; node_idx<num_nodes; node_idx++ )); do
    node=${nodes[$node_idx]}
    for (( i=0; i<ppr; i++ )); do
        slot=$(( i * slot_spacing ))
        echo "rank $rank=$node slot=$slot" >> $rankfile
        rank=$(( rank + 1 ))
    done
done
 
# Output completion message
echo "Rankfile 'rankfile.txt' generated successfully."

