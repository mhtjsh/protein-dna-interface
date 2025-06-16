import os
import glob
import yaml

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

input_dir       = config["input_dir"]
split_dir       = config["split_dir"]
rsa_dir         = config["rsa_dir"]
interface_dir   = config["interface_dir"]
scripts         = config["scripts"]

# Dynamic PDB list passed via CLI config (e.g., --config pdb_ids="8ucu,1A3Q")
if "pdb_ids" in config:
    pdb_ids = config["pdb_ids"].split(",")
else:
    # fallback: find all .pdb files in input folder
    pdb_files = glob.glob(os.path.join(input_dir, "*.pdb"))
    pdb_ids = [os.path.splitext(os.path.basename(pdb))[0] for pdb in pdb_files]

# Ensure sequential execution by setting ruleorder priorities
ruleorder: compute_summary > generate_ints > run_naccess_chains > run_naccess_complex > split_chains

rule all:
    input:
        expand(os.path.join(interface_dir, "{pdb}_interface_summary.csv"), pdb=pdb_ids)

rule split_chains:
    input:
        pdb_file = lambda wildcards: os.path.join(input_dir, f"{wildcards.pdb}.pdb")
    output:
        temp(os.path.join(split_dir, "{pdb}_SPLIT.done"))
    shell:
        """
        python3 {scripts[split_chains]} {input.pdb_file} {split_dir} && \
        touch {output}
        """

rule run_naccess_chains:
    input:
        split_done = os.path.join(split_dir, "{pdb}_SPLIT.done")
    output:
        temp(os.path.join(rsa_dir, "{pdb}_CHAINS.done"))
    shell:
        """
        python3 {scripts[naccess_chains]} --pdb-id {wildcards.pdb} --chains-dir {split_dir} --out-dir {rsa_dir} && \
        touch {output}
        """

rule run_naccess_complex:
    input:
        pdb_file = lambda wildcards: os.path.join(input_dir, f"{wildcards.pdb}.pdb")
    output:
        temp(os.path.join(rsa_dir, "{pdb}_COMPLEX.done"))
    shell:
        """
        python3 {scripts[naccess_complex]} --pdb-id {wildcards.pdb} --input-dir {input_dir} --out-dir {rsa_dir} && \
        touch {output}
        """

rule generate_ints:
    input:
        complex_done = os.path.join(rsa_dir, "{pdb}_COMPLEX.done"),
        chains_done  = os.path.join(rsa_dir, "{pdb}_CHAINS.done")
    output:
        temp(os.path.join(rsa_dir, "{pdb}_INTS.done"))
    shell:
        """
        bash {scripts[generate_ints]} {wildcards.pdb} && \
        touch {output}
        """

rule compute_summary:
    input:
        ints_done = os.path.join(rsa_dir, "{pdb}_INTS.done")
    output:
        summary_csv = os.path.join(interface_dir, "{pdb}_interface_summary.csv")
    shell:
        """
        python3 {scripts[compute_summary]} --pdb-id {wildcards.pdb} --rsa-dir {rsa_dir} --out-dir {interface_dir}
        """

