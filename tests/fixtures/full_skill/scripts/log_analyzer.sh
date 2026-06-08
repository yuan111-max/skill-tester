#!/bin/bash
# Analyze log files for error patterns

if [ $# -lt 1 ]; then
    echo "Usage: $0 <logfile>"
    exit 1
fi

ERROR_COUNT=$(grep -c "ERROR" "$1" 2>/dev/null || echo 0)
echo "Found $ERROR_COUNT errors in $1"
