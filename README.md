## 🚀 Protein-DNA Interface Generation: Docker Usage

We provide a ready-to-use Docker image to make your experience effortless and reproducible across any system.  
You can build the image yourself, or pull the pre-built image from [Docker Hub](https://hub.docker.com/r/mhtjsh/protein-dna-interface).

---

### 🐋 **Pull the Pre-built Image (Recommended)**

Simply pull the image directly from Docker Hub:

```bash
docker pull mhtjsh/protein-dna-interface
```

---

### 🛠️ **Build the Image Yourself (Optional)**

If you want to build the image from source, first clone this repo and then run:

```bash
git clone https://github.com/mhtjsh/Protein_DNA_Interface_Generation.git
cd Protein_DNA_Interface_Generation
docker build -t mhtjsh/protein-dna-interface .
```

---

### ▶️ **Running the Container**

#### **Basic Run (using included example data):**

```bash
docker run --rm -it mhtjsh/protein-dna-interface
```

#### **Mounting Input and Output Folders**

You can provide your own input PDB files by mounting a local folder to `/app/input` inside the container.  
Output files can similarly be accessed by mounting an output directory.

Suppose your local folder structure is:

```
/home/mhtjsh/Protein_DNA_Interface_Generation/
│
├── input/     # Place your PDB files here
├── Interface/    # Output files will be written here
├── Snakemake  # Snakemake workflow file
├── ...        # Other files
```

Run the container with:

```bash
docker run --rm -it \
  -v /home/mhtjsh/Protein_DNA_Interface_Generation/input:/app/input \
  -v /home/mhtjsh/Protein_DNA_Interface_Generation/output:/app/output \
  mhtjsh/protein-dna-interface
```

- Place your PDB input files in the `input/` folder before running.
- Processed output will appear in the `output/` folder.

**Note:**  
- Adjust the `/home/mhtjsh/Protein_DNA_Interface_Generation` part if your repo is in a different location.
- The container expects inputs in `/app/input` and writes outputs to `/app/output`.

---

### 📜 **Workflow Details**

- The provided `Snakefile` (Snakemake workflow) orchestrates the interface generation.
- You can customize the workflow or parameters by editing the `Snakefile` and config files in the repo.

---

### 🌐 **Resources**

- **Docker Hub Image:** [mhtjsh/protein-dna-interface](https://hub.docker.com/r/mhtjsh/protein-dna-interface)
- **GitHub Repository:** [Protein_DNA_Interface_Generation](https://github.com/mhtjsh/Protein_DNA_Interface_Generation)

---

### ❓ **Need Help?**

Open an [issue](https://github.com/mhtjsh/Protein_DNA_Interface_Generation/issues) on GitHub!
