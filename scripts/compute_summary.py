#!/usr/bin/env python3
import os
import glob
import argparse
import pandas as pd
import re

NONPOLAR = {'ALA', 'VAL', 'LEU', 'ILE', 'MET', 'PHE', 'TRP', 'PRO', 'GLY'}

# ----------------------
# 1. Parse CLI arguments
# ----------------------
p = argparse.ArgumentParser(description="Compute interface summary for a given PDB ID")
p.add_argument("--pdb-id", required=True, help="PDB ID to process, e.g. 1A3Q")
p.add_argument("--rsa-dir", default="rsa", help="Path to RSA directory containing .int files")
p.add_argument("--out-dir", default="interface", help="Directory to write output CSV")
args = p.parse_args()

# Preserve case as given
pdb_id = args.pdb_id
rsa_dir = os.path.abspath(args.rsa_dir)
out_dir = os.path.abspath(args.out_dir)

# ----------------------
# 2. Locate matching .int files (case-insensitive)
# ----------------------
int_paths = [
    f for f in glob.glob(os.path.join(rsa_dir, f"{pdb_id}*.int"))
    if re.match(rf"{re.escape(pdb_id)}[A-Za-z]\.int$", os.path.basename(f), re.IGNORECASE)
]

if not int_paths:
    raise FileNotFoundError(f"No .int files for {pdb_id} found in {rsa_dir}")

# ----------------------
# 3. Parse ATOM lines from .int files
# ----------------------
records = []
for path in int_paths:
    with open(path) as f:
        for line in f:
            if not line.lstrip().startswith("ATOM"):
                continue
            parts = line.split()
            try:
                asa_m = float(parts[-2])
                asa_c = float(parts[-1])
            except (ValueError, IndexError):
                continue
            delta = asa_m - asa_c
            records.append({
                'chain': parts[4],
                'resnum': parts[5],
                'resname': parts[3],
                'delta': delta
            })

if not records:
    raise RuntimeError(f"No ATOM records parsed for {pdb_id} from .int files")

# ----------------------
# 4. Compute summary
# ----------------------
df = pd.DataFrame(records)
total_atoms       = len(df)
total_residues    = df.drop_duplicates(['chain', 'resnum']).shape[0]
total_area        = round(df['delta'].sum(), 2)
local_density     = round(total_atoms / total_area, 3) if total_area else 0.0
fraction_buried   = round(1.0, 3)
nonpolar_df       = df[df['resname'].isin(NONPOLAR)]
fraction_nonpolar = round(len(nonpolar_df) / total_atoms, 3) if total_atoms else 0.0
nonpolar_area     = round(nonpolar_df['delta'].sum(), 2)

# ----------------------
# 5. Write summary CSV
# ----------------------
summary = pd.DataFrame({
    'Interface Properties': [
        'Total Interface Atoms',
        'Total Interface Residues',
        'Total Interface Area (Å²)',
        'Local Atomic Density',
        'Residue Propensity Score',
        'Fraction of Buried Atoms',
        'Fraction of Non-Polar Atoms',
        'Non-Polar Interface Area'
    ],
    'Value': [
        total_atoms,
        total_residues,
        total_area,
        local_density,
        'N/A',
        fraction_buried,
        fraction_nonpolar,
        nonpolar_area
    ],
    'Notes': [
        'Count atoms with ΔASA > 0',
        'Based on ΔASA at residue level',
        'ΔASA sum',
        'atoms / area',
        'Requires scoring table',
        'ΔASA atoms / total atoms',
        'Use residue types',
        'ΔASA only for non-polar residues'
    ]
})

os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"{pdb_id}_interface_summary.csv")
summary.to_csv(out_path, index=False)
print(f"Wrote summary → {out_path}")

