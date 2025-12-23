#!/bin/bash

# Display memory usage
free -h

# Become root user
sudo su <<EOF
sync
echo 3 > /proc/sys/vm/drop_caches
EOF

# Display memory usage again
free -h