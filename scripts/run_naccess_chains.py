#!/usr/bin/env python3
import subprocess, argparse, os, shutil, glob

def run_naccess(pdb_path, out_dir):
    if not os.path.isfile(pdb_path):
        raise FileNotFoundError(f"Missing chain PDB file: {pdb_path}")
    
    print(f"→ Running NACCESS on {os.path.basename(pdb_path)}")
    subprocess.run(["naccess", pdb_path], check=True)

    base = os.path.basename(pdb_path).rsplit(".", 1)[0]
    for ext in ("rsa", "asa", "log"):
        src = f"{base}.{ext}"
        if os.path.exists(src):
            dst = os.path.join(out_dir, f"{base}.{ext}")
            shutil.move(src, dst)
        else:
            print(f"  ⚠️  Warning: Expected {src} not found.")

def run_all_chains(pdb_id, chains_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    pattern = os.path.join(chains_dir, f"{pdb_id}_*.pdb")
    chain_paths = sorted(glob.glob(pattern))
    
    if not chain_paths:
        raise FileNotFoundError(f"No chains found for {pdb_id} in {chains_dir}")
    
    print(f"Found {len(chain_paths)} chains for {pdb_id} → {', '.join(os.path.basename(p) for p in chain_paths)}")

    for chain_pdb in chain_paths:
        run_naccess(chain_pdb, out_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NACCESS on all chains for a PDB ID")
    parser.add_argument("--pdb-id", required=True, help="PDB ID prefix (e.g. 8ucu)")
    parser.add_argument("--chains-dir", default="split_chains", help="Directory with split chain PDBs")
    parser.add_argument("--out-dir", default="rsa", help="Output directory for .asa/.rsa/.log files")

    args = parser.parse_args()
    run_all_chains(args.pdb_id, args.chains_dir, args.out_dir)

