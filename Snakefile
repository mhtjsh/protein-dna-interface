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

# Map real file paths to their PDB IDs (case sensitive)
pdb_files = glob.glob(os.path.join(input_dir, "*.pdb"))
pdb_map = {
    os.path.splitext(os.path.basename(pdb))[0]: pdb
    for pdb in pdb_files
}
pdb_ids = list(pdb_map.keys())

rule all:
    input:
        expand(os.path.join(interface_dir, "{pdb}_interface_summary.csv"), pdb=pdb_ids)

rule split_chains:
    input:
        lambda wildcards: pdb_map[wildcards.pdb]
    output:
        temp(os.path.join(split_dir, "{pdb}_SPLIT.done"))
    shell:
        """
        python3 {scripts[split_chains]} {input} {split_dir} && \
        touch {output}
        """

rule run_naccess_chains:
    input:
        os.path.join(split_dir, "{pdb}_SPLIT.done")
    output:
        temp(os.path.join(rsa_dir, "{pdb}_CHAINS.done"))
    shell:
        """
        python3 {scripts[naccess_chains]} --pdb-id {wildcards.pdb} && \
        touch {output}
        """

rule run_naccess_complex:
    input:
        lambda wildcards: pdb_map[wildcards.pdb]
    output:
        temp(os.path.join(rsa_dir, "{pdb}_COMPLEX.done"))
    shell:
        """
        python3 {scripts[naccess_complex]} --pdb-id {wildcards.pdb} && \
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
        os.path.join(rsa_dir, "{pdb}_INTS.done")
    output:
        os.path.join(interface_dir, "{pdb}_interface_summary.csv")
    shell:
        """
        python3 {scripts[compute_summary]} --pdb-id {wildcards.pdb}
        """

