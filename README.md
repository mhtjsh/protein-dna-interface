# Protein DNA Interface Generation with Residue Propensity Map 

Welcome to the Protein_DNA_Interface_Generation repository, where we provide a comprehensive, production-ready pipeline for analyzing and generating protein-DNA interfaces. This README explains the repository structure, installation, usage, and the main workflow powered by Snakemake. 🚀

---

## Table of Contents
1. [Introduction](#introduction)
2. [Repository Structure](#repository-structure)
3. [Workflow Stages](#workflow-stages)
4. [Installation and Dependencies](#installation-and-dependencies)
5. [Usage](#usage)
6. [Testing](#testing)
7. [Contributing](#contributing)
8. [License](#license)

---

## Introduction
This project provides a pipeline to:
- Process multi-chain PDB structures in the [input/](#repository-structure) folder.  
- Split them into chain-specific files and place them in [split_chain/](#repository-structure).  
- Run Naccess for both the complex and each chain, storing results in [rsa/](#repository-structure).  
- Generate final residue propensity maps in CSV format, placed in [interface/](#repository-structure).  

The workflow leverages:
- **Python** (for data parsing and scripting),
- **Fortran** (for performance-intensive operations),
- **Shell** scripts (for automation),
- **Docker** (for consistent runtimes),
- **Snakemake** (for orchestrating the automated workflow).

---

## Repository Structure
```
Protein_DNA_Interface_Generation/
├── input/                  # Raw PDB or other input files
├── split_chain/            # Contains split chain PDB files
├── rsa/                    # Naccess outputs (.asa, .rsa, .int) for complex & chains
├── interface/              # Final residue propensity maps (CSV) & summary outputs
├── scripts/                # Python, Shell, Fortran scripts
├── docker/                 # Docker setup/resources
├── Snakefile               # Main Snakemake workflow definition
└── README.md               # Documentation (this file)
```
- **input/**: Put your raw PDB files here.  
- **split_chain/**: Generated chain-specific PDB files.  
- **rsa/**: Stores all Naccess outputs for both complex and individual chains.  
- **interface/**: Houses final CSV results on interface residue propensities, plus summary data.  
- **scripts/**: Various scripts for chain splitting, running Naccess, and interface calculations.  

---

## Workflow Stages
1. **Input Parsing**  
   - Reads one or more `.pdb` files from `input/`.
2. **Chain Splitting**  
   - Generates chain-specific `.pdb` files in `split_chain/`.
3. **Run Naccess**  
   - Analyzes both the entire complex and each chain, outputting `.asa`, `.rsa`, and `.int` files in `rsa/`.
4. **Interface Computation**  
   - Processes the Naccess files to define interface residues and metrics.
5. **Results Aggregation**  
   - Produces CSV-formatted residue propensity results stored in `interface/`.

---

## Installation and Dependencies

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/mhtjsh/Protein_DNA_Interface_Generation.git
   cd Protein_DNA_Interface_Generation
   ```

2. **Install Dependencies**  
   - **Python** (3.7 or higher)  
   - **Snakemake** (via `pip` or `conda`):
     ```bash
     pip install snakemake
     ```
   - **Fortran Compiler** (e.g., gfortran)  
   - **Shell** environment  
   - **Docker** (optional, for containerization)

3. **Check Installation**  
   ```bash
   snakemake --version
   ```
   Should output a valid Snakemake version.

---

## Usage

1. **Prepare Your Inputs**  
   - Place raw PDB files in `input/`.

2. **Run Snakemake**  
   ```bash
   snakemake --cores 4
   ```
   This command orchestrates the entire workflow, from splitting chains to producing final interface CSVs.

3. **Customizing** (Optional)  
   - Modify the `Snakefile` or scripts in `scripts/` to tweak parameters (e.g., Naccess paths, chain filtering options, etc.).

### Common Snakemake Options
- **Dry Run**  
  ```bash
  snakemake --cores 4 --dry-run
  ```
  Lists which steps will be executed without actually running them.

- **Force All Steps**  
  ```bash
  snakemake --cores 4 --forceall
  ```
  Re-executes every rule regardless of file timestamps.

- **Workflow Visualization**  
  ```bash
  snakemake --dag | dot -Tpng > workflow_dag.png
  ```
  Generates a DAG image showing rule dependencies.

---

## Testing
1. **Manual Testing**  
   - Place a test `.pdb` file in `input/`.
   - Run Snakemake and validate that outputs are generated in `split_chain/`, `rsa/`, and `interface/`.
2. **Automated Testing**  
   - Consider adding a lightweight test dataset and a test rule to confirm correct function on each commit or pull request.

---

## Contributing
1. **Fork** this repository.  
2. Create a feature branch for your changes.  
3. Submit a **pull request** to propose your updates.

Contributions that enhance clarity, functionality, or general performance are greatly appreciated.

---

## License
This project is under an open-source license. See [LICENSE](LICENSE) for details.
