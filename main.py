from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import subprocess
import asyncio
from typing import List
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDB Interface Analysis", description="Upload PDB files and get interface analysis")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories (matching your config.yaml)
INPUT_DIR = "input"
INTERFACE_DIR = "interface"
SPLIT_DIR = "split_chains"
RSA_DIR = "rsa"

# Create directories if they don't exist
for directory in [INPUT_DIR, INTERFACE_DIR, SPLIT_DIR, RSA_DIR]:
    os.makedirs(directory, exist_ok=True)

# Store job status
job_status = {}

class JobManager:
    def __init__(self):
        self.jobs = {}
    
    def create_job(self, job_id: str, pdb_files: List[str]):
        self.jobs[job_id] = {
            "status": "pending",
            "pdb_files": pdb_files,
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "message": "Job created",
            "output_files": []
        }
    
    def update_job(self, job_id: str, status: str, progress: int = None, message: str = None):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            if progress is not None:
                self.jobs[job_id]["progress"] = progress
            if message is not None:
                self.jobs[job_id]["message"] = message
    
    def get_job(self, job_id: str):
        return self.jobs.get(job_id)

job_manager = JobManager()

async def run_snakemake_workflow(job_id: str, pdb_ids: List[str]):
    """Run the Snakemake workflow for given PDB IDs"""
    try:
        job_manager.update_job(job_id, "running", 10, "Starting Snakemake workflow...")
        
        # Create PDB IDs string for snakemake
        pdb_ids_str = ",".join(pdb_ids)
        
        # Run snakemake command
        cmd = [
            "snakemake", 
            "--cores", "1",
            "--config", f"pdb_ids={pdb_ids_str}",
            "-f"  # Force re-run
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        job_manager.update_job(job_id, "running", 30, "Processing PDB files...")
        
        # Run the subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            job_manager.update_job(job_id, "running", 80, "Workflow completed, checking outputs...")
            
            # Check for output files
            output_files = []
            for pdb_id in pdb_ids:
                interface_file = f"{pdb_id}_interface_summary.csv"
                propensity_file = f"{pdb_id}_residue_propensity.csv"
                
                interface_path = os.path.join(INTERFACE_DIR, interface_file)
                propensity_path = os.path.join(INTERFACE_DIR, propensity_file)
                
                if os.path.exists(interface_path):
                    output_files.append({
                        "filename": interface_file,
                        "type": "interface_summary",
                        "pdb_id": pdb_id,
                        "path": interface_path
                    })
                
                if os.path.exists(propensity_path):
                    output_files.append({
                        "filename": propensity_file,
                        "type": "residue_propensity", 
                        "pdb_id": pdb_id,
                        "path": propensity_path
                    })
            
            job_manager.jobs[job_id]["output_files"] = output_files
            job_manager.update_job(job_id, "completed", 100, f"Analysis completed! Generated {len(output_files)} files.")
            
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Snakemake failed: {error_msg}")
            job_manager.update_job(job_id, "failed", 0, f"Workflow failed: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        job_manager.update_job(job_id, "failed", 0, f"Error: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the frontend HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDB Interface Analysis</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .header p {
                color: #666;
                font-size: 1.1em;
            }
            
            .upload-section {
                margin-bottom: 40px;
                padding: 30px;
                border: 2px dashed #ddd;
                border-radius: 15px;
                text-align: center;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.7);
            }
            
            .upload-section:hover {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.1);
            }
            
            .upload-section.dragover {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.2);
                transform: scale(1.02);
            }
            
            .upload-icon {
                font-size: 3em;
                color: #667eea;
                margin-bottom: 20px;
            }
            
            .file-input {
                display: none;
            }
            
            .upload-btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 25px;
                font-size: 1.1em;
                cursor: pointer;
                transition: all 0.3s ease;
                margin: 10px;
            }
            
            .upload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .file-list {
                margin: 20px 0;
                text-align: left;
            }
            
            .file-item {
                background: rgba(102, 126, 234, 0.1);
                padding: 10px 15px;
                margin: 5px 0;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .remove-file {
                background: #ff4757;
                color: white;
                border: none;
                border-radius: 50%;
                width: 25px;
                height: 25px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .process-btn {
                background: linear-gradient(45deg, #2ed573, #1e90ff);
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 25px;
                font-size: 1.2em;
                cursor: pointer;
                transition: all 0.3s ease;
                margin: 20px 0;
            }
            
            .process-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(46, 213, 115, 0.3);
            }
            
            .process-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .status-section {
                margin-top: 30px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 15px;
                display: none;
            }
            
            .progress-bar {
                width: 100%;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin: 15px 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(45deg, #2ed573, #1e90ff);
                width: 0%;
                transition: width 0.3s ease;
                border-radius: 10px;
            }
            
            .results-section {
                margin-top: 30px;
                display: none;
            }
            
            .result-files {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .file-card {
                background: rgba(255, 255, 255, 0.9);
                padding: 20px;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
                transition: all 0.3s ease;
            }
            
            .file-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
            }
            
            .download-btn {
                background: linear-gradient(45deg, #ff6b6b, #ffa726);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
                margin-top: 10px;
            }
            
            .download-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(255, 107, 107, 0.3);
            }
            
            .error-message {
                background: #ff4757;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
                display: none;
            }
            
            .success-message {
                background: #2ed573;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧬 PDB Interface Analysis</h1>
                <p>Upload your PDB files and get comprehensive interface analysis results</p>
            </div>
            
            <div class="upload-section" id="uploadSection">
                <div class="upload-icon">📁</div>
                <h3>Drop PDB files here or click to browse</h3>
                <p>Support for multiple PDB files (max 15 files)</p>
                <input type="file" id="fileInput" class="file-input" multiple accept=".pdb">
                <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                    Choose Files
                </button>
                
                <div class="file-list" id="fileList"></div>
                
                <button class="process-btn" id="processBtn" onclick="processFiles()" disabled>
                    🚀 Start Analysis
                </button>
            </div>
            
            <div class="error-message" id="errorMessage"></div>
            <div class="success-message" id="successMessage"></div>
            
            <div class="status-section" id="statusSection">
                <h3>Processing Status</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p id="statusMessage">Initializing...</p>
            </div>
            
            <div class="results-section" id="resultsSection">
                <h3>📊 Analysis Results</h3>
                <div class="result-files" id="resultFiles"></div>
            </div>
        </div>
        
        <script>
            let selectedFiles = [];
            let currentJobId = null;
            
            // File upload handling
            const fileInput = document.getElementById('fileInput');
            const fileList = document.getElementById('fileList');
            const processBtn = document.getElementById('processBtn');
            const uploadSection = document.getElementById('uploadSection');
            
            fileInput.addEventListener('change', handleFileSelect);
            
            // Drag and drop functionality
            uploadSection.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadSection.classList.add('dragover');
            });
            
            uploadSection.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadSection.classList.remove('dragover');
            });
            
            uploadSection.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadSection.classList.remove('dragover');
                const files = Array.from(e.dataTransfer.files).filter(file => file.name.endsWith('.pdb'));
                handleFiles(files);
            });
            
            function handleFileSelect(e) {
                const files = Array.from(e.target.files);
                handleFiles(files);
            }
            
            function handleFiles(files) {
                if (selectedFiles.length + files.length > 15) {
                    showError('Maximum 15 PDB files allowed');
                    return;
                }
                
                const pdbFiles = files.filter(file => file.name.endsWith('.pdb'));
                if (pdbFiles.length !== files.length) {
                    showError('Please select only PDB files (.pdb extension)');
                    return;
                }
                
                selectedFiles = selectedFiles.concat(pdbFiles);
                updateFileList();
                updateProcessButton();
            }
            
            function updateFileList() {
                fileList.innerHTML = '';
                selectedFiles.forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <span>📄 ${file.name}</span>
                        <button class="remove-file" onclick="removeFile(${index})">×</button>
                    `;
                    fileList.appendChild(fileItem);
                });
            }
            
            function removeFile(index) {
                selectedFiles.splice(index, 1);
                updateFileList();
                updateProcessButton();
            }
            
            function updateProcessButton() {
                processBtn.disabled = selectedFiles.length === 0;
            }
            
            async function processFiles() {
                if (selectedFiles.length === 0) return;
                
                showStatusSection();
                processBtn.disabled = true;
                
                try {
                    const formData = new FormData();
                    selectedFiles.forEach(file => {
                        formData.append('files', file);
                    });
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        currentJobId = result.job_id;
                        showSuccess(`Files uploaded successfully! Job ID: ${currentJobId}`);
                        pollJobStatus();
                    } else {
                        showError(result.detail || 'Upload failed');
                        processBtn.disabled = false;
                    }
                } catch (error) {
                    showError('Network error: ' + error.message);
                    processBtn.disabled = false;
                }
            }
            
            async function pollJobStatus() {
                if (!currentJobId) return;
                
                try {
                    const response = await fetch(`/status/${currentJobId}`);
                    const status = await response.json();
                    
                    updateProgress(status.progress, status.message);
                    
                    if (status.status === 'completed') {
                        showResults(status.output_files);
                        processBtn.disabled = false;
                    } else if (status.status === 'failed') {
                        showError('Processing failed: ' + status.message);
                        processBtn.disabled = false;
                    } else {
                        setTimeout(pollJobStatus, 2000); // Poll every 2 seconds
                    }
                } catch (error) {
                    showError('Error checking status: ' + error.message);
                    processBtn.disabled = false;
                }
            }
            
            function updateProgress(progress, message) {
                const progressFill = document.getElementById('progressFill');
                const statusMessage = document.getElementById('statusMessage');
                
                progressFill.style.width = progress + '%';
                statusMessage.textContent = message;
            }
            
            function showResults(outputFiles) {
                const resultsSection = document.getElementById('resultsSection');
                const resultFiles = document.getElementById('resultFiles');
                
                resultFiles.innerHTML = '';
                
                outputFiles.forEach(file => {
                    const fileCard = document.createElement('div');
                    fileCard.className = 'file-card';
                    
                    const fileType = file.type === 'interface_summary' ? '🔬 Interface Summary' : '🧪 Residue Propensity';
                    
                    fileCard.innerHTML = `
                        <h4>${fileType}</h4>
                        <p><strong>PDB ID:</strong> ${file.pdb_id}</p>
                        <p><strong>Filename:</strong> ${file.filename}</p>
                        <a href="/download/${file.filename}" class="download-btn" download>
                            ⬇️ Download
                        </a>
                    `;
                    
                    resultFiles.appendChild(fileCard);
                });
                
                resultsSection.style.display = 'block';
            }
            
            function showStatusSection() {
                document.getElementById('statusSection').style.display = 'block';
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('errorMessage');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
                setTimeout(() => {
                    errorDiv.style.display = 'none';
                }, 5000);
            }
            
            function showSuccess(message) {
                const successDiv = document.getElementById('successMessage');
                successDiv.textContent = message;
                successDiv.style.display = 'block';
                setTimeout(() => {
                    successDiv.style.display = 'none';
                }, 5000);
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/upload")
async def upload_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """Upload PDB files and start processing"""
    
    if len(files) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 files allowed")
    
    # Validate file extensions
    pdb_files = []
    for file in files:
        if not file.filename.endswith('.pdb'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDB file")
        pdb_files.append(file)
    
    if not pdb_files:
        raise HTTPException(status_code=400, detail="No valid PDB files provided")
    
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save files to input directory
    saved_files = []
    pdb_ids = []
    
    try:
        for file in pdb_files:
            file_path = os.path.join(INPUT_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append(file.filename)
            # Extract PDB ID (filename without extension, preserving case)
            pdb_id = os.path.splitext(file.filename)[0]
            pdb_ids.append(pdb_id)
        
        # Create job
        job_manager.create_job(job_id, saved_files)
        
        # Start background task
        background_tasks.add_task(run_snakemake_workflow, job_id, pdb_ids)
        
        return {
            "message": "Files uploaded successfully",
            "job_id": job_id,
            "files": saved_files,
            "pdb_ids": pdb_ids
        }
        
    except Exception as e:
        # Clean up on error
        for file_name in saved_files:
            file_path = os.path.join(INPUT_DIR, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error saving files: {str(e)}")

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download result file"""
    file_path = os.path.join(INTERFACE_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/csv'
    )

@app.get("/files")
async def list_output_files():
    """List all available output files"""
    if not os.path.exists(INTERFACE_DIR):
        return {"files": []}
    
    files = []
    for filename in os.listdir(INTERFACE_DIR):
        if filename.endswith('.csv'):
            file_path = os.path.join(INTERFACE_DIR, filename)
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    return {"files": files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
