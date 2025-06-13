#!/bin/bash
set -euo pipefail

INTF_EXE="scripts/intf_new"
RSA_DIR="rsa"

# Check if intf_new exists and is executable
if [[ ! -x "$INTF_EXE" ]]; then
  echo "❌ ERROR: intf_new not found or not executable at $INTF_EXE"
  exit 1
fi

# Loop through all *_X.asa files in RSA_DIR (chain-specific)
for chain_asa in "$RSA_DIR"/*_?.asa; do
  chain_file=$(basename "$chain_asa")
  pdb_id=${chain_file:0:4}
  chain_id=${chain_file:5:1}
  complex_asa="$RSA_DIR/${pdb_id}.asa"
  output_int="$RSA_DIR/${pdb_id}${chain_id}.int"

  # Check that complex ASA exists
  if [[ ! -f "$complex_asa" ]]; then
    echo "❌ Skipping chain $chain_file: missing complex file $complex_asa"
    continue
  fi

  # Delete existing .int file if it exists (avoid Fortran crash)
  if [[ -f "$output_int" ]]; then
    echo "🗑️  Removing old $output_int"
    rm -f "$output_int"
  fi

  echo "🔄 Generating $output_int from $chain_file and ${pdb_id}.asa"

  # Feed filenames and chain ID to intf_new (run inside rsa directory)
  (
    cd "$RSA_DIR"
    "$OLDPWD/$INTF_EXE" <<EOF
$chain_file
${pdb_id}.asa
${chain_id}
EOF
  )

  # Move result to match naming (from inside rsa dir)
  mv "$RSA_DIR/${pdb_id}${chain_id}.int" "$output_int" 2>/dev/null || true
done

echo "✅ All .int files regenerated in $RSA_DIR"

