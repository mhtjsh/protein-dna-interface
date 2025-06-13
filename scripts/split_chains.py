#!/usr/bin/env python3
import argparse
import os
from Bio.PDB import PDBParser, PDBIO, Select

class ChainSelect(Select):
    def __init__(self, chain_id):
        self.chain_id = chain_id
    def accept_chain(self, chain):
        return chain.id == self.chain_id


def detect_and_split(pdb_path, out_dir):
    parser    = PDBParser(QUIET=True)
    structure = parser.get_structure("complex", pdb_path)

    # 1) Collect all unique chain IDs
    chains = sorted({
        chain.id
        for model in structure
        for chain in model
    })
    if not chains:
        raise RuntimeError("No chains found in " + pdb_path)

    # 2) Determine base name without extension
    base = os.path.splitext(os.path.basename(pdb_path))[0]

    # 3) Write one PDB per chain: <base>_<chain>.pdb
    os.makedirs(out_dir, exist_ok=True)
    io = PDBIO()
    io.set_structure(structure)
    for ch in chains:
        sel = ChainSelect(ch)
        out_file = os.path.join(out_dir, f"{base}_{ch}.pdb")
        io.save(out_file, sel)

    return chains


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Split a PDB into one file per chain, named <base>_<chain>.pdb"
    )
    p.add_argument("pdb",     help="Path to input PDB (e.g. input/8ucu.pdb)")
    p.add_argument("out_dir", help="Directory where split chains will be written")
    args = p.parse_args()

    chains = detect_and_split(args.pdb, args.out_dir)
    print("FOUND_CHAINS=" + ",".join(chains))

