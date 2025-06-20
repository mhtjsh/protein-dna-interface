FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gfortran \
        build-essential \
        bash \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files (including naccess binary)
COPY . /app

# Copy naccess binary to a directory in PATH and make it executable
RUN cp /app/naccess /usr/local/bin/naccess && chmod +x /usr/local/bin/naccess

RUN pip install --upgrade pip && \
    pip install biopython pandas pyyaml snakemake 'pulp<2.7'
    
# (Optional, since /usr/local/bin is already in PATH, but you can explicitly set it)
ENV PATH="/usr/local/bin:${PATH}"

CMD ["snakemake", "--cores", "1"]
