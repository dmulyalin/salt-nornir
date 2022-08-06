#!/bin/bash
  
# turn on bash's job control
set -m
  
# Start the master - primary process and put it in the background
salt-master -l debug &

# Start the salt-api - helper process
salt-api -l debug  
  
# now we bring the primary process back into the foreground
# and leave it there
fg %1