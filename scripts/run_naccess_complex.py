#!/usr/bin/env python3
import subprocess, argparse, os, shutil

def run_naccess(pdb_path, out_dir):
    if not os.path.isfile(pdb_path):
        raise FileNotFoundError(f"❌ Input PDB file not found: {pdb_path}")
    
    print(f"🔄 Running NACCESS on: {pdb_path}")
    subprocess.run(["naccess", pdb_path], check=True)

    base = os.path.basename(pdb_path).rsplit(".", 1)[0]
    for ext in ("rsa", "asa", "log"):
        src = f"{base}.{ext}"
        if os.path.exists(src):
            dst = os.path.join(out_dir, f"{base}.{ext}")
            shutil.move(src, dst)
            print(f"✅ Moved {src} → {dst}")
        else:
            print(f"⚠️  Warning: expected {src} not found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NACCESS on a complex PDB structure")
    parser.add_argument("--pdb-id", required=True,
                        help="PDB ID of the input file, e.g. 8ucu (looks for input/8ucu.pdb)")
    parser.add_argument("--input-dir", default="input",
                        help="Directory containing the input .pdb file")
    parser.add_argument("--out-dir", default="rsa",
                        help="Directory to write .asa, .rsa, .log output")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    
    pdb_path = os.path.join(args.input_dir, f"{args.pdb_id}.pdb")
    run_naccess(pdb_path, args.out_dir)

