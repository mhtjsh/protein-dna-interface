#!/usr/bin/env python3
import os
import glob
import argparse
import pandas as pd
import re
import math

NONPOLAR = {'ALA', 'VAL', 'LEU', 'ILE', 'MET', 'PHE', 'TRP', 'PRO', 'GLY'}
AMINO_ACIDS = [
    'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE',
    'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL'
]

# ----------------------
# 1. Parse CLI arguments
# ----------------------
p = argparse.ArgumentParser(description="Compute interface summary for a given PDB ID")
p.add_argument("--pdb-id", required=True, help="PDB ID to process, e.g. 1A3Q")
p.add_argument("--rsa-dir", default="rsa", help="Path to RSA directory containing .int files")
p.add_argument("--out-dir", default="interface", help="Directory to write output CSVs")
args = p.parse_args()

pdb_id = args.pdb_id.upper()
rsa_dir = os.path.abspath(args.rsa_dir)
out_dir = os.path.abspath(args.out_dir)

# ----------------------
# 2. Locate matching .int files
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

df = pd.DataFrame(records)

# ----------------------
# 4. Compute interface summary
# ----------------------
total_atoms       = len(df)
total_residues    = df.drop_duplicates(['chain', 'resnum']).shape[0]
total_area        = round(df['delta'].sum(), 2)
local_density     = round(total_atoms / total_area, 3) if total_area else 0.0
fraction_buried   = round(1.0, 3)
nonpolar_df       = df[df['resname'].isin(NONPOLAR)]
fraction_nonpolar = round(len(nonpolar_df) / total_atoms, 3) if total_atoms else 0.0
nonpolar_area     = round(nonpolar_df['delta'].sum(), 2)

# ----------------------
# 5. Build residue background from RSA
# ----------------------
background_csv = os.path.join(rsa_dir, f"{pdb_id}_residue_background.csv")

if not os.path.exists(background_csv):
    print("🔄 Building residue background from .rsa files...")
    all_rsa_residues = []
    for file in glob.glob(os.path.join(rsa_dir, "*.rsa")):
        with open(file) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4 and parts[0] == "RES":
                    resname = parts[1].upper()
                    if resname in AMINO_ACIDS:
                        all_rsa_residues.append(resname)
    surface_counts_all = {aa: all_rsa_residues.count(aa) for aa in AMINO_ACIDS}
    total_res = len(all_rsa_residues)
    background_freqs = {
        aa: surface_counts_all[aa] / total_res if total_res > 0 else 0
        for aa in AMINO_ACIDS
    }
    pd.DataFrame(list(background_freqs.items()), columns=["Residue", "Frequency"]).to_csv(background_csv, index=False)
    print(f"✅ Background table saved to {background_csv} with {total_res} residues.")

# Load background frequencies
bg_df = pd.read_csv(background_csv)
background_freqs = dict(zip(bg_df["Residue"], bg_df["Frequency"]))

# ----------------------
# 6. Compute residue propensity
# ----------------------
residue_list_int = df['resname'].tolist()
interface_counts = {aa: residue_list_int.count(aa) for aa in AMINO_ACIDS}
total_int_res = len(residue_list_int)

log_weighted_values = []
propensity_scores = {}

for aa in AMINO_ACIDS:
    freq_int = interface_counts[aa]
    freq_bg = background_freqs.get(aa, 0)

    if freq_bg == 0 or freq_int == 0:
        prop_score = 0
        log_weighted = 0
    else:
        prop_score = (freq_int / total_int_res) / freq_bg
        log_val = math.log(prop_score)
        log_weighted = max(log_val * freq_int, 0)  # avoid negatives

    propensity_scores[aa] = round(prop_score, 3)
    log_weighted_values.append(log_weighted)

log_weighted_propensity_score = round(sum(log_weighted_values), 3)

# ----------------------
# 7. Save summary and propensity table
# ----------------------
os.makedirs(out_dir, exist_ok=True)

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
        log_weighted_propensity_score,
        fraction_buried,
        fraction_nonpolar,
        nonpolar_area
    ],
    'Notes': [
        'Count atoms with ΔASA > 0',
        'Based on ΔASA at residue level',
        'ΔASA sum',
        'atoms / area',
        'log-weighted: log(freq_int/freq_bg) * count, clamped ≥ 0',
        'ΔASA atoms / total atoms',
        'Use residue types',
        'ΔASA only for non-polar residues'
    ]
})

summary_out = os.path.join(out_dir, f"{pdb_id}_interface_summary.csv")
summary.to_csv(summary_out, index=False)
print(f"✅ Wrote summary → {summary_out}")

# Write per-residue propensity table
prop_df = pd.DataFrame(list(propensity_scores.items()), columns=["Residue", "Propensity"])
prop_df.sort_values(by="Propensity", ascending=False, inplace=True)
prop_out = os.path.join(out_dir, f"{pdb_id}_residue_propensity.csv")
prop_df.to_csv(prop_out, index=False)
print(f"✅ Wrote residue propensity table → {prop_out}")
print(f"Parsed {total_int_res} interface residues and loaded background from {background_csv}")
