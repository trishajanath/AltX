"""Pure AI generator that relies exclusively on Gemini outputs.

This module intentionally avoids deterministic fallbacks. If Gemini declines
to produce content, the requ		# Check if the response was blocked (anything other than STOP/1 is problematic)
		if finish_reason is not None and finish_reason != 1:
			# Handle specific cases
			if finish_reason == 2:  # MAX_TOKENS
				# For debugg			+ "* Use React 18 functional components with hooks.\n"
			"* TailwindCSS utility classes for styling (CDN version in HTML).\n"
			"* App.jsx must orchestrate layout and import all generated components.\n"
			"* Each component file should default-export a component whose name matches the sanitized component identifier (see JSON payload) and implement the described purpose.\n"
			"* main.jsx must bootstrap React with ReactDOM.createRoot and import index.css.\n"
			"* package.json must include scripts (dev, build, preview) and dependencies for React, ReactDOM, Vite.\n"
			"* Include inline TailwindCSS via CDN in index.html.\n"
			"* Components should make direct fetch calls to `http://localhost:8000/api`.\n"
			"* Provide responsive design and loading/error states.\n"
			"* Keep code concise but functional.\n\n" see what we got before the truncation
				text = self._candidate_text(candidate)
				print(f"DEBUG: Truncated response length: {len(text)} chars")
				print(f"DEBUG: Response preview: {text[:500]}...")
				print(f"DEBUG: Response ending: ...{text[-500:]}")
				raise ModelGenerationError("Gemini response was truncated due to token limit. Try reducing the request complexity.")
			
			# Try to get the FinishReason enum for better error messages
			try:
				finish_reason_name = getattr(candidate, "FinishReason", None)
				if finish_reason_name:
					for attr_name in dir(finish_reason_name):
						if not attr_name.startswith('_') and getattr(finish_reason_name, attr_name) == finish_reason:
							raise ModelGenerationError(f"Gemini blocked the request (finish_reason={attr_name})")
			except:
				pass
			raise ModelGenerationError(f"Gemini blocked the request (finish_reason={finish_reason})")e caller must handle the error.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import google.generativeai as genai
from google.generativeai.types import (
    HarmBlockThreshold,
    HarmCategory,
)
class ModelGenerationError(RuntimeError):
	"""Raised when Gemini refuses to generate the requested content."""


@dataclass
class GenerationRequest:
	prompt: str
	config_overrides: Dict[str, Any] | None = None


class PureAIGenerator:
	"""Gemini-only generator that produces code without fallbacks."""

	def __init__(self, model_name: str = "gemini-2.5-pro") -> None:
		api_key = os.getenv("GOOGLE_API_KEY")
		if not api_key:
			raise ValueError("❌ GOOGLE_API_KEY environment variable is required")

		genai.configure(api_key=api_key)
		self.model = genai.GenerativeModel(model_name)

		self.base_config: Dict[str, Any] = {
			"temperature": 0.25,
			"top_p": 0.8,
			"candidate_count": 1,
			"max_output_tokens": 2048,
		}

		self.safety_settings = [
			{
				"category": HarmCategory.HARM_CATEGORY_HARASSMENT,
				"threshold": HarmBlockThreshold.BLOCK_NONE,
			},
			{
				"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
				"threshold": HarmBlockThreshold.BLOCK_NONE,
			},
			{
				"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
				"threshold": HarmBlockThreshold.BLOCK_NONE,
			},
			{
				"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
				"threshold": HarmBlockThreshold.BLOCK_NONE,
			},
		]

		print("🤖 Pure AI Generator initialized (Gemini only, no fallbacks)")

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------

	async def analyze_and_plan(self, idea: str, project_name: str) -> Dict[str, Any]:
		request = GenerationRequest(
			prompt=self._build_plan_prompt(idea, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 2500,
				"temperature": 0.15,
			},
		)

		response_text = self._run_generation(request)

		try:
			plan = json.loads(response_text)
		except json.JSONDecodeError as exc:  # pragma: no cover - depends on API output
			raise ModelGenerationError(
				"AI returned invalid JSON for the project plan"
			) from exc

		self._validate_plan(plan)
		return plan

	async def generate_project_structure(
		self, project_path: Path, idea: str, project_name: str
	) -> List[str]:
		plan = await self.analyze_and_plan(idea, project_name)
		project_path.mkdir(parents=True, exist_ok=True)
		
		files_created: List[str] = []
		
		# Generate backend files one by one to avoid token limits
		backend_path = project_path / "backend"
		backend_path.mkdir(parents=True, exist_ok=True)
		
		# Generate models.py
		models_code = await self.generate_single_file("backend_models", plan, project_name)
		(backend_path / "models.py").write_text(models_code, encoding="utf-8")
		files_created.append("backend/models.py")
		
		# Generate routes.py
		routes_code = await self.generate_single_file("backend_routes", plan, project_name)
		(backend_path / "routes.py").write_text(routes_code, encoding="utf-8")
		files_created.append("backend/routes.py")
		
		# Generate main.py
		main_code = await self.generate_single_file("backend_main", plan, project_name)
		(backend_path / "main.py").write_text(main_code, encoding="utf-8")
		files_created.append("backend/main.py")
		
		# Generate requirements.txt
		requirements = "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\npython-multipart==0.0.6\n"
		(backend_path / "requirements.txt").write_text(requirements, encoding="utf-8")
		files_created.append("backend/requirements.txt")
		
		# Generate frontend files
		frontend_path = project_path / "frontend"
		frontend_src = frontend_path / "src"
		frontend_src.mkdir(parents=True, exist_ok=True)
		
		# Generate App.jsx
		app_code = await self.generate_single_file("frontend_app", plan, project_name)
		(frontend_src / "App.jsx").write_text(app_code, encoding="utf-8")
		files_created.append("frontend/src/App.jsx")
		
		# Generate supporting files
		self._create_supporting_files(frontend_path, project_name)
		files_created.extend([
			"frontend/package.json", 
			"frontend/index.html",
			"frontend/src/main.jsx"
		])
		
		return files_created

	async def generate_single_file(self, file_type: str, plan: Dict[str, Any], project_name: str) -> str:
		"""Generate a single file based on type"""
		if file_type == "backend_models":
			prompt = self._build_models_prompt(plan)
		elif file_type == "backend_routes":
			prompt = self._build_routes_prompt(plan)
		elif file_type == "backend_main":
			prompt = self._build_main_prompt(plan, project_name)
		elif file_type == "frontend_app":
			prompt = self._build_app_prompt(plan, project_name)
		else:
			raise ValueError(f"Unknown file type: {file_type}")
			
		request = GenerationRequest(
			prompt=prompt,
			config_overrides={
				"max_output_tokens": 4000,  # Increased from 2000
				"temperature": 0.1,
			},
		)
		
		return self._strip_code_fences(self._run_generation(request))

	def _create_supporting_files(self, frontend_path: Path, project_name: str):
		"""Create supporting files with hardcoded content"""
		# package.json
		package_json = {
			"name": project_name.lower().replace(" ", "-"),
			"version": "1.0.0",
			"type": "module",
			"scripts": {
				"dev": "vite",
				"build": "vite build", 
				"preview": "vite preview"
			},
			"dependencies": {
				"react": "^18.2.0",
				"react-dom": "^18.2.0"
			},
			"devDependencies": {
				"@vitejs/plugin-react": "^4.0.0",
				"vite": "^4.4.0"
			}
		}
		
		import json
		(frontend_path / "package.json").write_text(json.dumps(package_json, indent=2), encoding="utf-8")
		
		# index.html
		html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
		(frontend_path / "index.html").write_text(html, encoding="utf-8")
		
		# main.jsx
		main_jsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)'''
		(frontend_path / "src" / "main.jsx").write_text(main_jsx, encoding="utf-8")

	async def generate_backend_bundle(
		self, plan: Dict[str, Any], project_name: str
	) -> Dict[str, str]:
		request = GenerationRequest(
			prompt=self._build_backend_bundle_prompt(plan, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 4000,  # Reduced further
				"temperature": 0.1,  # Lower temperature for more concise output
			},
		)

		return self._generate_json_bundle(request)

	async def generate_frontend_bundle(
		self, plan: Dict[str, Any], project_name: str
	) -> Dict[str, str]:
		request = GenerationRequest(
			prompt=self._build_frontend_bundle_prompt(plan, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 8000,  # Increased from 3400
				"temperature": 0.25,
			},
		)

		return self._generate_json_bundle(request)

	async def generate_documentation_bundle(
		self, plan: Dict[str, Any], project_name: str
	) -> Dict[str, str]:
		request = GenerationRequest(
			prompt=self._build_docs_bundle_prompt(plan, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 1200,
				"temperature": 0.15,
			},
		)

		return self._generate_json_bundle(request)

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------

	def _run_generation(self, request: GenerationRequest) -> str:
		config = dict(self.base_config)
		if request.config_overrides:
			config.update(request.config_overrides)

		response = self.model.generate_content(
			contents=request.prompt,
			generation_config=config,
			safety_settings=self.safety_settings,
		)

		if not response.candidates:
			raise ModelGenerationError("Gemini returned no candidates")

		candidate = response.candidates[0]
		finish_reason = getattr(candidate, "finish_reason", None)

		# Check if the response was blocked (anything other than STOP/1 is problematic)
		if finish_reason is not None and finish_reason != 1:
			# Handle specific cases
			if finish_reason == 2:  # MAX_TOKENS
				raise ModelGenerationError("Gemini response was truncated due to token limit. Try reducing the request complexity.")
			
			# Try to get the FinishReason enum for better error messages
			try:
				finish_reason_name = getattr(candidate, "FinishReason", None)
				if finish_reason_name:
					for attr_name in dir(finish_reason_name):
						if not attr_name.startswith('_') and getattr(finish_reason_name, attr_name) == finish_reason:
							raise ModelGenerationError(f"Gemini blocked the request (finish_reason={attr_name})")
			except:
				pass
			raise ModelGenerationError(f"Gemini blocked the request (finish_reason={finish_reason})")

		text = self._candidate_text(candidate)
		if not text.strip():
			raise ModelGenerationError("Gemini returned an empty response")

		return text.strip()

	@staticmethod
	def _candidate_text(candidate: Any) -> str:
		if hasattr(candidate, "text") and getattr(candidate, "text"):
			return candidate.text

		content = getattr(candidate, "content", None)
		if not content:
			return ""

		parts = getattr(content, "parts", None)
		if not parts:
			return ""

		return "".join(getattr(part, "text", "") for part in parts)

	@staticmethod
	def _strip_code_fences(text: str) -> str:
		stripped = text.strip()
		if stripped.startswith("```"):
			stripped = stripped.split("\n", 1)[1]
		if stripped.endswith("```"):
			stripped = stripped.rsplit("\n", 1)[0]
		return stripped.strip()

	def _generate_json_bundle(self, request: GenerationRequest) -> Dict[str, str]:
		raw = self._run_generation(request)
		try:
			bundle = json.loads(raw)
		except json.JSONDecodeError as exc:
			raise ModelGenerationError("Gemini returned invalid JSON bundle") from exc

		if not isinstance(bundle, dict):
			raise ModelGenerationError("Bundle response must be a JSON object")

		normalized: Dict[str, str] = {}
		for path, content in bundle.items():
			if not isinstance(path, str):
				raise ModelGenerationError("Bundle keys must be strings")
			if not isinstance(content, str):
				raise ModelGenerationError(f"Bundle content for {path!r} must be a string")
			normalized[path.replace("\\", "/")] = self._strip_code_fences(content)

		return normalized

	@staticmethod
	def _write_bundle(project_path: Path, bundle: Dict[str, str]) -> List[str]:
		files_created: List[str] = []
		for relative_path, content in bundle.items():
			target_path = project_path / Path(relative_path)
			target_path.parent.mkdir(parents=True, exist_ok=True)
			target_path.write_text(content, encoding="utf-8", newline="\n")
			files_created.append(relative_path)
		return files_created

	@staticmethod
	def _build_plan_prompt(idea: str, project_name: str) -> str:
		return (
			"You are a senior solutions architect. Produce a comprehensive project plan "
			"in strict JSON (no prose, no markdown). Use double-quoted keys and values.\n\n"
			f"Project name: {project_name}\n"
			f"High-level idea: {idea}\n\n"
			"Required JSON schema:\n"
			"{\n"
			"  \"app_type\": \"short descriptor\",\n"
			"  \"description\": \"one paragraph\",\n"
			"  \"features\": [\"feature string\", ...],\n"
			"  \"frontend\": {\n"
			"    \"stack\": \"framework or tools\",\n"
			"    \"components\": [\n"
			"      {\"name\": \"Name\", \"purpose\": \"Detailed purpose\"},\n"
			"      ...\n"
			"    ]\n"
			"  },\n"
			"  \"backend\": {\n"
			"    \"stack\": \"frameworks\",\n"
			"    \"models\": [\n"
			"      {\"name\": \"ModelName\", \"fields\": [\"field\", ...]}\n"
			"    ],\n"
			"    \"endpoints\": [\n"
			"      {\"method\": \"HTTP_METHOD\", \"path\": \"/api/example\", \"purpose\": \"what it does\"}\n"
			"    ]\n"
			"  }\n"
			"}\n\n"
			"Respond with valid JSON only."
		)

	@staticmethod
	def _build_backend_bundle_prompt(plan: Dict[str, Any], project_name: str) -> str:
		backend_plan = plan.get("backend", {})
		endpoints = backend_plan.get("endpoints", [])
		models = backend_plan.get("models", [])

		schema = {
			"required_paths": [
				"backend/main.py",
				"backend/routes.py", 
				"backend/models.py",
				"backend/requirements.txt",
			],
			"optional_paths": [
				"backend/database.py",
			],
		}

		return (
			"You are generating the complete FastAPI backend for a project. "
			"Return a JSON object that maps POSIX file paths to file contents. "
			"Do not include markdown or code fences; encode newlines with \n as required by JSON string rules.\n\n"
			f"Project name: {project_name}\n"
			+ "Backend plan context:\n"
			+ json.dumps({
				"stack": backend_plan.get("stack", "FastAPI + Pydantic"),
				"models": models,
				"endpoints": endpoints,
				"features": plan.get("features", []),
			}, indent=2)
			+ "\n\nRequirements:\n"
			"* Use FastAPI with Pydantic v2 models and ConfigDict(from_attributes=True).\n"
			"* Implement in-memory persistence in models.py with simple lists/dicts.\n"
			"* Ensure main.py creates the FastAPI app, configures CORS, and includes routes from routes.py.\n"
			"* routes.py must wire CRUD endpoints that align exactly with the plan endpoints.\n"
			"* requirements.txt must list precise dependencies needed to run the backend.\n"
			"* Keep files concise but functional - avoid over-engineering.\n"
			"* Every file must be production-quality Python (or plaintext for requirements).\n\n"
			"Output JSON schema:\n"
			+ json.dumps(schema, indent=2)
			+ "\nEnsure every required path is present."
		)

	@staticmethod
	def _build_frontend_bundle_prompt(plan: Dict[str, Any], project_name: str) -> str:
		frontend_plan = plan.get("frontend", {})
		components = frontend_plan.get("components", [])
		sanitized_components = []
		for index, component in enumerate(components, start=1):
			original_name = component.get("name") or f"Feature{index}"
			sanitized = "".join(part for part in original_name.title().split()) or f"Feature{index}"
			sanitized_components.append(
				{
					"original": original_name,
					"sanitized": sanitized,
					"purpose": component.get("purpose", ""),
				}
			)

		if not sanitized_components:
			sanitized_components.append(
				{"original": "MainView", "sanitized": "MainView", "purpose": "Primary screen"}
			)

		component_paths = [
			f"frontend/src/components/{component['sanitized']}.jsx"
			for component in sanitized_components
		]

		required_paths = [
			"frontend/package.json",
			"frontend/index.html", 
			"frontend/src/main.jsx",
			"frontend/src/App.jsx", 
		] + component_paths[:2]  # Even fewer components

		prompt_payload = {
			"components": sanitized_components,
			"required_paths": required_paths,
			"frontend_overview": frontend_plan,
			"backend_api_base": "http://localhost:8000/api",
			"features": plan.get("features", []),
		}

		return (
			"You are generating the complete React frontend (Vite + Tailwind) for the project. "
			"Return a JSON object mapping POSIX file paths to file contents. \n"
			"All strings must be valid JSON strings; escape newlines as \\n. \n"
			"Do not wrap anything in markdown fences.\n\n"
			f"Project name: {project_name}\n"
			"Frontend plan: \n"
			+ json.dumps(frontend_plan, indent=2)
			+ "\n\nDetailed requirements:\n"
			"* Use React 18 functional components with hooks.\n"
			"* TailwindCSS utility classes for styling.\n"
			"* App.jsx must orchestrate layout and import all generated components.\n"
			"* Each component file should default-export a component whose name matches the sanitized component identifier (see JSON payload) and implement the described purpose.\n"
			"* main.jsx must bootstrap React with ReactDOM.createRoot and import index.css.\n"
			"* package.json must include scripts (dev, build, preview) and dependencies for React, ReactDOM, Vite, Tailwind, autoprefixer, postcss, axios.\n"
			"* Include Tailwind and PostCSS config files configured for Vite.\n"
			"* Provide a frontend/src/api/client.js helper that wraps fetch calls to the backend base URL.\n"
			"* Ensure components use the API helper to talk to `http://localhost:8000/api`.\n"
			"* Provide responsive design and loading/error states.\n\n"
			+ "Output JSON schema example:\n"
			+ json.dumps(prompt_payload, indent=2)
			+ "\nEnsure every required path exists and components paths are unique."
		)

	@staticmethod
	def _build_docs_bundle_prompt(plan: Dict[str, Any], project_name: str) -> str:
		return (
			"Create documentation files as JSON mapping file paths to content. "
			"Include at least README.md and project_plan.json. Do not include markdown fences.\n\n"
			f"Project name: {project_name}\n"
			"Plan summary:\n"
			+ json.dumps(plan, indent=2)
			+ "\nRequirements:\n"
			"* README.md must summarize the project, list features, and provide setup steps for backend and frontend.\n"
			"* project_plan.json should re-emit the structured plan with no additional commentary.\n"
			"* Optionally include docs/architecture.md with deeper technical notes.\n"
			"* Ensure JSON mapping is valid and uses POSIX paths such as README.md or docs/architecture.md."
		)

	@staticmethod
	def _validate_plan(plan: Dict[str, Any]) -> None:
		required_root_keys = {"app_type", "description", "features", "frontend", "backend"}
		missing = required_root_keys - plan.keys()
		if missing:
			raise ModelGenerationError(f"Plan is missing keys: {sorted(missing)}")

		features = plan.get("features")
		if not isinstance(features, Sequence) or isinstance(features, (str, bytes)):
			raise ModelGenerationError("Plan features must be a list")

		backend = plan.get("backend") or {}
		if not backend.get("models"):
			raise ModelGenerationError("Backend section must include models")

		if not backend.get("endpoints"):
			raise ModelGenerationError("Backend section must include endpoints")

	@staticmethod
	def _build_models_prompt(plan: Dict[str, Any]) -> str:
		backend_plan = plan.get("backend", {})
		return f"""
Generate a complete FastAPI models.py file using Pydantic v2.
Project: {plan.get('app_type', 'Web Application')}
Models needed: {backend_plan.get('models', [])}

Requirements:
- Use Pydantic BaseModel with ConfigDict(from_attributes=True)
- Include proper type hints
- Add validation where appropriate
- Keep it simple and functional

Return only Python code, no markdown fences.
"""

	@staticmethod  
	def _build_routes_prompt(plan: Dict[str, Any]) -> str:
		backend_plan = plan.get("backend", {})
		return f"""
Generate concise FastAPI routes.py file.
Endpoints: {backend_plan.get('endpoints', [])}

Requirements:
- APIRouter with basic CRUD
- In-memory storage (simple list)
- Import models from .models
- Essential endpoints only

Return only Python code, no markdown fences.
"""

	@staticmethod
	def _build_main_prompt(plan: Dict[str, Any], project_name: str) -> str:
		return f"""
Generate FastAPI main.py file.
Project: {project_name}
App type: {plan.get('app_type', 'Web Application')}

Requirements:
- Create FastAPI app instance
- Configure CORS middleware
- Include router from routes.py
- Keep it simple and clean

Return only Python code, no markdown fences.
"""

	@staticmethod
	def _build_app_prompt(plan: Dict[str, Any], project_name: str) -> str:
		features = plan.get('features', [])[:3]  # Limit to 3 features
		return f"""
Generate simple React App.jsx component.
Features: {features}

Requirements:
- React functional component
- TailwindCSS styling
- API calls to http://localhost:8000/api
- Basic UI for the features
- Keep it concise

Return only JSX code, no markdown fences.
"""

