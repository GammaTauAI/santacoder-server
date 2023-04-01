#!/bin/bash

# this script closes $1 santacoder instances on $1 GPUs,
# spawned by multi_gpu_spawn.sh


# check args
if [ $# -ne 1 ]; then
    echo "usage: ./multi_gpu_spawn.sh [num_of_gpus]" >&2
    exit 1
fi

# check if tmux is installed
if ! [ -x "$(command -v tmux)" ]; then
    echo "Error: tmux is not installed." >&2;
    exit 1
fi

# check if num_of_gpus is a number
re='^[0-9]+$'
if ! [[ $1 =~ $re ]] ; then
   echo "Error: num_of_gpus is not a number" >&2; exit 1
fi

for i in $(seq 0 $(($1-1)))
do
  # close tmux session
  tmux kill-session -t santa$i
  # delete socket file
  rm /tmp/santa$i.sock
done

