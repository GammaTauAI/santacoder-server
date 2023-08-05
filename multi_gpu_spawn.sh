#!/bin/bash

# this script spawns $1 santacoder instances on $1 GPUs,
# each instance will be listening on their /tmp/santa[$1].sock,
# and will create a tmux session named santa[$1]
# WARNING: it will delete any /tmp/santa[$1].sock files found

# usage: ./multi_gpu_spawn.sh [num_of_gpus] [model_name] [context size]

# check args
if [ $# -ne 3 ]; then
    echo "usage: ./multi_gpu_spawn.sh [num_of_gpus] [model_name] [context size]"
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
    # check if socket file exists
    if [ -e /tmp/santa$i.sock ]; then
        # print stderr
        echo "Error: /tmp/santa$i.sock already exists. Want to delete it? (y/n)" >&2
        read -r answer
        if [ "$answer" = "y" ]; then
            rm /tmp/santa$i.sock
        else
            echo "Error: /tmp/santa$i.sock already exists." >&2
            exit 1
        fi
    fi

    # create tmux session
    tmux new-session -d -s santa$i

    # run santa
    tmux send-keys -t santa$i "MODEL_NAME=$2 python3 main.py --socket_path /tmp/santa$i.sock --device $i --max_length $3" C-m

    # detach from tmux session
    tmux detach -s santa$i
done

# return the socket paths, comma separated
for i in $(seq 0 $(($1-1)))
do
    if [ $i -eq 0 ]; then
        echo -n "/tmp/santa$i.sock"
    else
        echo -n ",/tmp/santa$i.sock"
    fi
done
echo "" # newline
