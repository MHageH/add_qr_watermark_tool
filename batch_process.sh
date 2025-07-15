#!/bin/bash

INPUT_DIR="input_dir"
OUTPUT_DIR="output_dir"
PYTHON_SCRIPT="add_qr_watermark.py"  

mkdir -p "$OUTPUT_DIR"

for input_file in "$INPUT_DIR"/*.pdf; do
  if [[ -f "$input_file" ]]; then
    filename=$(basename "$input_file")
    echo "Processing $filename ..."

    python3 "$PYTHON_SCRIPT" "$input_file" "$OUTPUT_DIR"

    base="${filename%.pdf}"
    output_file="${OUTPUT_DIR}/${base}_with_qr.pdf"

    if [[ -f "$output_file" ]]; then
      echo "Output saved: $output_file"
    fi
  fi
done

echo "Batch processing complete."
