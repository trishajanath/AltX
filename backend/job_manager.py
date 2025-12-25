"""
Asynchronous Job Manager for Long-Running Tasks
Handles AI project generation without holding HTTP connections open
"""

import asyncio
import uuid
import time
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, job_id: str, job_type: str, params: Dict[str, Any], user_email: str):
        self.job_id = job_id
        self.job_type = job_type
        self.params = params
        self.user_email = user_email
        self.status = JobStatus.PENDING
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.logs = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "logs": self.logs[-10:]  # Last 10 log entries
        }

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker_task = None
    
    def create_job(self, job_type: str, params: Dict[str, Any], user_email: str) -> str:
        """Create a new job and add it to the queue"""
        job_id = str(uuid.uuid4())
        job = Job(job_id, job_type, params, user_email)
        self.jobs[job_id] = job
        
        # Add to queue for processing
        asyncio.create_task(self.queue.put(job))
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    async def start_worker(self):
        """Start background worker to process jobs"""
        if self.worker_task is None:
            self.worker_task = asyncio.create_task(self._process_jobs())
    
    async def _process_jobs(self):
        """Background worker that processes jobs from the queue"""
        while True:
            try:
                job = await self.queue.get()
                await self._execute_job(job)
                self.queue.task_done()
            except Exception as e:
                print(f"❌ Worker error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_job(self, job: Job):
        """Execute a job"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            job.logs.append(f"Started at {job.started_at.isoformat()}")
            
            # Route to appropriate handler
            if job.job_type == "project_generation":
                await self._handle_project_generation(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 100
            job.logs.append(f"Completed at {job.completed_at.isoformat()}")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            job.logs.append(f"Failed: {str(e)}")
            print(f"❌ Job {job.job_id} failed: {e}")
    
    async def _handle_project_generation(self, job: Job):
        """Handle AI project generation"""
        # Import here to avoid circular dependency
        from pathlib import Path
        import main
        
        params = job.params
        user_email = job.user_email
        
        project_name = params.get("project_name")
        idea = params.get("idea", "")
        tech_stack = params.get("tech_stack", [])
        project_type = params.get("project_type", "web app")
        features = params.get("features", [])
        requirements = params.get("requirements", {})
        user_id = params.get("user_id", user_email)  # Get user_id from params
        
        try:
            # Step 1: Create project structure
            job.progress = 10
            job.logs.append("Creating project structure with AI...")
            
            # Send WebSocket update
            await main.manager.send_to_project(project_name, {
                "type": "status",
                "phase": "create",
                "message": "Creating project structure with AI..."
            })
            
            create_resp = await main.create_project_structure({
                "project_name": project_name,
                "idea": idea,
                "tech_stack": tech_stack,
                "project_type": project_type,
                "features": features,
                "requirements": requirements,
                "user_id": user_id  # Pass user_id for S3 organization
            })
            
            if not create_resp.get("success"):
                raise Exception(f"Project creation failed: {create_resp.get('error', 'Unknown error')}")
            
            # Step 2: Install dependencies
            job.progress = 40
            job.logs.append("Installing dependencies...")
            
            await main.manager.send_to_project(project_name, {
                "type": "status",
                "phase": "install",
                "message": "Installing dependencies..."
            })
            
            await main.install_dependencies_endpoint({
                "project_name": project_name,
                "tech_stack": tech_stack
            })
            
            # Step 3: Validate and fix
            job.progress = 60
            job.logs.append("Validating project files...")
            
            await main.manager.send_to_project(project_name, {
                "type": "status",
                "phase": "validate",
                "message": "Validating project for errors..."
            })
            
            project_slug = project_name.lower().replace(" ", "-")
            project_path = Path("generated_projects") / project_slug
            
            await main.validate_and_fix_project_files(project_path, project_name)
            check1 = await main.check_project_errors(project_name)
            
            errors = check1.get("errors", []) if check1.get("success") else []
            if errors:
                job.logs.append(f"Auto-fixing {len(errors)} issues...")
                
                await main.manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "fix",
                    "message": f"Auto-fixing {len(errors)} issues..."
                })
                
                await main.auto_fix_errors({
                    "project_name": project_name,
                    "errors": errors,
                    "tech_stack": tech_stack
                })
                
                # Re-validate once more
                check2 = await main.check_project_errors(project_name)
                errors = check2.get("errors", []) if check2.get("success") else errors
            
            # Step 4: Run project
            job.progress = 80
            job.logs.append("Starting development servers...")
            
            await main.manager.send_to_project(project_name, {
                "type": "status",
                "phase": "run",
                "message": "Starting development servers..."
            })
            
            run_resp = await main.run_project({
                "project_name": project_name,
                "tech_stack": tech_stack
            })
            
            preview_url = run_resp.get("preview_url") if isinstance(run_resp, dict) else None
            
            if preview_url:
                await main.manager.send_to_project(project_name, {
                    "type": "preview_ready",
                    "url": preview_url
                })
            
            # Files already uploaded to S3
            await main.manager.send_to_project(project_name, {
                "type": "status",
                "phase": "cloud_ready",
                "message": "☁️ Project files already in cloud storage (S3)"
            })
            
            # Step 5: Complete
            job.progress = 95
            job.logs.append("Project generation complete!")
            
            await main.manager.send_to_project(project_name, {
                "type": "status",
                "phase": "ready",
                "message": "✅ Build complete. Live preview is ready.",
                "preview_url": preview_url,
                "errors_remaining": errors
            })
            
            job.result = {
                "success": True,
                "project_name": project_name,
                "preview_url": preview_url,
                "errors": errors
            }
            
        except Exception as e:
            job.logs.append(f"Error: {str(e)}")
            raise

# Global job manager instance
job_manager = JobManager()
