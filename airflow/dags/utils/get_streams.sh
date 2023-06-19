#!/bin/bash

# Usage: ./get_streams.sh <tap_name>
if [ "$#" -ne 1 ]; then
    echo "Usage: ./get_streams.sh <tap_name>"
    exit 1
fi

tap_name="$1"

# Run the meltano invoke command with --discover
meltano_output=$(meltano invoke "$tap_name" --discover)

# Use jq to parse the JSON output and extract the stream names
stream_names=$(echo "$meltano_output" | jq -r '.streams[].stream' | jq -sR 'split("\n")[:-1]')

# Create the XCom output JSON object and write it to the required file
xcom_output=$(echo "{\"return_value\": $stream_names}")
echo "$xcom_output" > /airflow/xcom/return.json

# Print the stream names
echo "$stream_names"