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
			"max_output_tokens": 8192,  # Increased from 2048 for larger files
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
				"max_output_tokens": 4000,  # Increased from 1500
				"temperature": 0.05,  # Lower temperature for more focused output
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
		print(f"DEBUG: Creating project at {project_path}")
		try:
			plan = await self.analyze_and_plan(idea, project_name)
		except Exception as e:
			print(f"ERROR: Failed to analyze and plan: {e}")
			raise
			
		project_path.mkdir(parents=True, exist_ok=True)
		files_created: List[str] = []
		errors_encountered: List[str] = []
		
		# Generate backend files one by one to avoid token limits
		backend_path = project_path / "backend"
		backend_path.mkdir(parents=True, exist_ok=True)
		
		# Generate models.py
		try:
			models_code = await self.generate_single_file("backend_models", plan, project_name)
			(backend_path / "models.py").write_text(models_code, encoding="utf-8")
			files_created.append("backend/models.py")
			print(f"✅ DEBUG: Wrote file {backend_path / 'models.py'}")
		except Exception as e:
			error_msg = f"Failed to generate backend/models.py: {e}"
			print(f"❌ ERROR: {error_msg}")
			errors_encountered.append(error_msg)
			
		# Generate routes.py
		try:
			routes_code = await self.generate_single_file("backend_routes", plan, project_name)
			(backend_path / "routes.py").write_text(routes_code, encoding="utf-8")
			files_created.append("backend/routes.py")
			print(f"✅ DEBUG: Wrote file {backend_path / 'routes.py'}")
		except Exception as e:
			error_msg = f"Failed to generate backend/routes.py: {e}"
			print(f"❌ ERROR: {error_msg}")
			errors_encountered.append(error_msg)

		# Generate main.py
		try:
			main_code = await self.generate_single_file("backend_main", plan, project_name)
			(backend_path / "main.py").write_text(main_code, encoding="utf-8")
			files_created.append("backend/main.py")
			print(f"✅ DEBUG: Wrote file {backend_path / 'main.py'}")
		except Exception as e:
			error_msg = f"Failed to generate backend/main.py: {e}"
			print(f"❌ ERROR: {error_msg}")
			errors_encountered.append(error_msg)

		# Generate requirements.txt
		try:
			requirements = "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\npython-multipart==0.0.6\n"
			(backend_path / "requirements.txt").write_text(requirements, encoding="utf-8")
			files_created.append("backend/requirements.txt")
			print(f"✅ DEBUG: Wrote file {backend_path / 'requirements.txt'}")
		except Exception as e:
			error_msg = f"Failed to generate backend/requirements.txt: {e}"
			print(f"❌ ERROR: {error_msg}")
			errors_encountered.append(error_msg)
			
		# Generate frontend files
		frontend_path = project_path / "frontend"
		frontend_src = frontend_path / "src"
		frontend_src.mkdir(parents=True, exist_ok=True)
		print(f"DEBUG: Created frontend directory at {frontend_path}")
		
		# Generate App.jsx
		try:
			app_code = await self.generate_single_file("frontend_app", plan, project_name)
			(frontend_src / "App.jsx").write_text(app_code, encoding="utf-8")
			files_created.append("frontend/src/App.jsx")
			print(f"✅ DEBUG: Wrote file {frontend_src / 'App.jsx'}")
		except Exception as e:
			error_msg = f"Failed to generate frontend/src/App.jsx: {e}"
			print(f"❌ ERROR: {error_msg}")
			errors_encountered.append(error_msg)
			
		# Generate supporting files
		try:
			self._create_supporting_files(frontend_path, project_name)
			files_created.extend([
				"frontend/package.json", 
				"frontend/index.html",
				"frontend/src/main.jsx",
				"frontend/src/index.css",
				"frontend/tailwind.config.js",
				"frontend/postcss.config.js",
				"frontend/vite.config.js"
			])
			print(f"✅ DEBUG: Created all supporting files and React Bits components")
		except Exception as e:
			error_msg = f"Failed to create supporting files: {e}"
			print(f"❌ ERROR: {error_msg}")
			errors_encountered.append(error_msg)
		
		# Report summary
		print(f"\n🎯 GENERATION SUMMARY:")
		print(f"✅ Files created: {len(files_created)}")
		print(f"❌ Errors encountered: {len(errors_encountered)}")
		
		if errors_encountered:
			print("❌ ERRORS:")
			for error in errors_encountered:
				print(f"  - {error}")
				
		if not files_created:
			raise ModelGenerationError("No files were successfully generated")
		
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
				"max_output_tokens": 8000,  # Significantly increased from 2000
				"temperature": 0.05,  # Lower temperature for more focused output
			},
		)
		
		return self._strip_code_fences(self._run_generation(request))

	def _create_supporting_files(self, frontend_path: Path, project_name: str):
		"""Create supporting files with hardcoded content and React Bits components"""
		# Enhanced package.json with React Bits dependencies
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
				"react-dom": "^18.2.0",
				"framer-motion": "^10.16.4",
				"lucide-react": "^0.292.0",
				"react-hook-form": "^7.47.0",
				"axios": "^1.6.0"
			},
			"devDependencies": {
				"@vitejs/plugin-react": "^4.0.0",
				"vite": "^4.4.0",
				"tailwindcss": "^3.3.5",
				"postcss": "^8.4.31",
				"autoprefixer": "^10.4.16"
			}
		}
		
		import json
		(frontend_path / "package.json").write_text(json.dumps(package_json, indent=2), encoding="utf-8")
		
		# Enhanced index.html with custom Tailwind config
		html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
      tailwind.config = {{
        theme: {{
          extend: {{
            animation: {{
              'float': 'float 3s ease-in-out infinite',
              'shimmer': 'shimmer 2s linear infinite',
              'glow': 'glow 2s ease-in-out infinite alternate'
            }},
            keyframes: {{
              float: {{
                '0%, 100%': {{ transform: 'translateY(0px)' }},
                '50%': {{ transform: 'translateY(-10px)' }}
              }},
              shimmer: {{
                '0%': {{ backgroundPosition: '-200% 0' }},
                '100%': {{ backgroundPosition: '200% 0' }}
              }},
              glow: {{
                '0%': {{ boxShadow: '0 0 5px rgba(59, 130, 246, 0.4)' }},
                '100%': {{ boxShadow: '0 0 20px rgba(59, 130, 246, 0.8)' }}
              }}
            }}
          }}
        }}
      }}
    </script>
  </head>
  <body class="bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
		(frontend_path / "index.html").write_text(html, encoding="utf-8")
		
		# Create src directory and enhanced main.jsx
		src_path = frontend_path / "src"
		src_path.mkdir(parents=True, exist_ok=True)
		
		main_jsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)'''
		(src_path / "main.jsx").write_text(main_jsx, encoding="utf-8")
		
		# Create index.css with custom styles
		index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

@layer components {
  .glass-morphism {
    background: rgba(255, 255, 255, 0.25);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.18);
  }
  
  .gradient-text {
    @apply bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent;
  }
  
  .shadow-glow {
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
  }
}'''
		(src_path / "index.css").write_text(index_css, encoding="utf-8")
		
		# Create React Bits UI components
		react_bits_components = self._get_react_bits_components()
		for file_path, content in react_bits_components.items():
			# Remove 'frontend/' prefix since we're already in frontend_path
			relative_path = file_path.replace("frontend/", "")
			full_path = frontend_path / relative_path
			full_path.parent.mkdir(parents=True, exist_ok=True)
			full_path.write_text(content, encoding="utf-8")
			print(f"✨ Created React Bits component: {relative_path}")
		
		# Create Tailwind config
		tailwind_config = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.5s ease-out",
        "slide-in": "slide-in 0.3s ease-out",
        "bounce-in": "bounce-in 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
        "fade-in": {
          "0%": { opacity: 0, transform: "translateY(10px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        "slide-in": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "bounce-in": {
          "0%": { opacity: 0, transform: "scale(0.3)" },
          "50%": { opacity: 1, transform: "scale(1.05)" },
          "70%": { transform: "scale(0.9)" },
          "100%": { opacity: 1, transform: "scale(1)" },
        },
      },
    },
  },
  plugins: [],
}'''
		(frontend_path / "tailwind.config.js").write_text(tailwind_config, encoding="utf-8")
		
		# Create PostCSS config
		postcss_config = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''
		(frontend_path / "postcss.config.js").write_text(postcss_config, encoding="utf-8")
		
		# Create Vite config
		vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
})'''
		(frontend_path / "vite.config.js").write_text(vite_config, encoding="utf-8")
		
		print(f"🎨 Created enhanced frontend setup with React Bits components for {project_name}")

	async def generate_backend_bundle(
		self, plan: Dict[str, Any], project_name: str
	) -> Dict[str, str]:
		request = GenerationRequest(
			prompt=self._build_backend_bundle_prompt(plan, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 8000,  # Increased from 4000
				"temperature": 0.05,  # Lower temperature for more concise output
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
				"max_output_tokens": 3000,  # Increased from 1200
				"temperature": 0.1,
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
			f"Create a project plan in JSON for: {idea}\n"
			f"Project: {project_name}\n\n"
			"JSON format:\n"
			"{\n"
			"  \"app_type\": \"brief type\",\n"
			"  \"description\": \"short description\",\n"
			"  \"features\": [\"feature1\", \"feature2\", \"feature3\"],\n"
			"  \"frontend\": {\n"
			"    \"stack\": \"React+Vite+Tailwind\",\n"
			"    \"components\": [{\"name\": \"Component\", \"purpose\": \"purpose\"}]\n"
			"  },\n"
			"  \"backend\": {\n"
			"    \"stack\": \"FastAPI\",\n"
			"    \"models\": [{\"name\": \"Model\", \"fields\": [\"field1\", \"field2\"]}],\n"
			"    \"endpoints\": [{\"method\": \"GET\", \"path\": \"/api/items\", \"purpose\": \"list items\"}]\n"
			"  }\n"
			"}\n\n"
			"Respond with valid JSON only. Keep it concise."
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
			"You are generating a complete, beautiful React frontend (Vite + Tailwind) with premium design quality. "
			"Return a JSON object mapping POSIX file paths to file contents. \n"
			"All strings must be valid JSON strings; escape newlines as \\n. \n"
			"Do not wrap anything in markdown fences.\n\n"
			f"Project name: {project_name}\n"
			"Frontend plan: \n"
			+ json.dumps(frontend_plan, indent=2)
			+ "\n\n🎨 PREMIUM DESIGN REQUIREMENTS:\n"
			"* Create STUNNING, professional-grade UI with modern design principles\n"
			"* Use React Bits style components with advanced animations and interactions\n"
			"* Implement micro-interactions, hover effects, and smooth transitions\n"
			"* Use sophisticated color palettes, gradients, and modern typography\n"
			"* Include glass morphism, neumorphism, or other modern design trends\n"
			"* Add subtle shadows, rounded corners, and layered depth\n"
			"* Implement dark mode support with seamless transitions\n\n"
			"📚 REACT BITS INSPIRATION (implement similar patterns):\n"
			"* Text animations: Split text reveal, typewriter effects, gradient text\n"
			"* Interactive buttons: Ripple effects, morphing shapes, 3D transforms\n"
			"* Card components: Hover lifts, tilt effects, content reveals\n"
			"* Navigation: Floating tabs, animated indicators, smooth scrolling\n"
			"* Loading states: Skeleton loaders, pulse effects, progress animations\n"
			"* Form elements: Floating labels, validation animations, success states\n\n"
			"🛠️ TECHNICAL REQUIREMENTS:\n"
			"* Use React 18 functional components with hooks and Suspense\n"
			"* TailwindCSS with custom animations and variants\n"
			"* Framer Motion for advanced animations (add to package.json)\n"
			"* React Hook Form for smooth form handling\n"
			"* Lucide React for consistent, beautiful icons\n"
			"* App.jsx must orchestrate layout with navigation and theme context\n"
			"* Each component should be a masterpiece of modern UI design\n"
			"* main.jsx must bootstrap React with ReactDOM.createRoot and import index.css\n"
			"* package.json must include: react, react-dom, vite, tailwindcss, framer-motion, lucide-react, react-hook-form, axios\n"
			"* Include custom Tailwind config with extended colors, animations, and utilities\n"
			"* Create a frontend/src/api/client.js helper for backend communication\n"
			"* Implement responsive design that looks amazing on all devices\n"
			"* Add proper loading states, error boundaries, and accessibility features\n\n"
			"🎭 COMPONENT DESIGN PATTERNS:\n"
			"* Hero sections with animated backgrounds and call-to-actions\n"
			"* Interactive cards with hover transforms and reveals\n"
			"* Smooth page transitions and route animations\n"
			"* Floating action buttons with ripple effects\n"
			"* Toast notifications with slide-in animations\n"
			"* Modal dialogs with backdrop blur and scale transitions\n"
			"* Form inputs with floating labels and validation feedback\n"
			"* Navigation bars with active state indicators\n\n"
			+ "Output JSON schema example:\n"
			+ json.dumps(prompt_payload, indent=2)
			+ "\n\nMAKE IT ABSOLUTELY BEAUTIFUL! Every pixel should delight users. 🚀"
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
		models = backend_plan.get('models', [])[:3]  # Limit to 3 models
		return f"""
Create FastAPI models.py with Pydantic v2.
Models: {models}

Requirements:
- BaseModel with ConfigDict(from_attributes=True)
- Proper type hints and validation
- Create/Update/Response model variants

Return Python code only.
"""

	@staticmethod  
	def _build_routes_prompt(plan: Dict[str, Any]) -> str:
		backend_plan = plan.get("backend", {})
		endpoints = backend_plan.get('endpoints', [])[:4]  # Limit to 4 endpoints
		return f"""
Create FastAPI routes.py file.
Endpoints: {endpoints}

Requirements:
- APIRouter with CRUD operations
- In-memory storage (lists/dicts)
- Import models from .models
- /api/v1 prefix for all routes
- Proper error handling

Return Python code only.
"""

	@staticmethod
	def _build_main_prompt(plan: Dict[str, Any], project_name: str) -> str:
		return f"""
Create FastAPI main.py for: {project_name}

Requirements:
- FastAPI app with CORS
- Include routes.py with /api/v1 prefix
- Health check at "/"

Return Python code only.
"""

	@staticmethod
	def _get_react_bits_components() -> Dict[str, str]:
		"""Returns a collection of React Bits-inspired component patterns"""
		return {
			"frontend/src/components/ui/Button.jsx": '''import React from 'react';
import { motion } from 'framer-motion';

export const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  onClick, 
  className = '',
  ...props 
}) => {
  const baseClasses = 'relative inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl focus:ring-blue-500',
    secondary: 'bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-700 hover:text-gray-900 shadow-sm hover:shadow-md',
    ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 hover:text-gray-900'
  };
  
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  };

  return (
    <motion.button
      whileHover={{ y: -2 }}
      whileTap={{ y: 0 }}
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      <span className="relative z-10">{children}</span>
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
    </motion.button>
  );
};''',

			"frontend/src/components/ui/Card.jsx": '''import React from 'react';
import { motion } from 'framer-motion';

export const Card = ({ children, className = '', hover = true, ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hover ? { 
        y: -8, 
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)" 
      } : {}}
      className={`bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden transition-all duration-300 ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const CardHeader = ({ children, className = '' }) => (
  <div className={`px-6 py-4 border-b border-gray-100 ${className}`}>
    {children}
  </div>
);

export const CardBody = ({ children, className = '' }) => (
  <div className={`px-6 py-4 ${className}`}>
    {children}
  </div>
);

export const CardFooter = ({ children, className = '' }) => (
  <div className={`px-6 py-4 border-t border-gray-100 bg-gray-50 ${className}`}>
    {children}
  </div>
);''',

			"frontend/src/components/ui/AnimatedText.jsx": '''import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export const SplitText = ({ text, className = '', delay = 0 }) => {
  const words = text.split(' ');
  
  return (
    <div className={className}>
      {words.map((word, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ 
            duration: 0.5, 
            delay: delay + i * 0.1 
          }}
          className="inline-block mr-2"
        >
          {word}
        </motion.span>
      ))}
    </div>
  );
};

export const TypeWriter = ({ text, speed = 50, className = '' }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, speed);

      return () => clearTimeout(timeout);
    }
  }, [currentIndex, text, speed]);

  return (
    <span className={className}>
      {displayText}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.8, repeat: Infinity }}
        className="ml-1"
      >
        |
      </motion.span>
    </span>
  );
};

export const GradientText = ({ children, gradient = 'from-blue-600 to-purple-600', className = '' }) => (
  <span className={`bg-gradient-to-r ${gradient} bg-clip-text text-transparent ${className}`}>
    {children}
  </span>
);''',

			"frontend/src/components/ui/Loading.jsx": '''import React from 'react';
import { motion } from 'framer-motion';

export const SkeletonLoader = ({ className = '', lines = 3 }) => (
  <div className={`animate-pulse space-y-3 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className="h-4 bg-gray-200 rounded-md"></div>
    ))}
  </div>
);

export const SpinnerLoader = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12'
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className={`${sizes[size]} border-2 border-gray-200 border-t-blue-600 rounded-full ${className}`}
    />
  );
};

export const PulseLoader = ({ className = '' }) => (
  <div className={`flex space-x-2 ${className}`}>
    {[0, 1, 2].map(i => (
      <motion.div
        key={i}
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ 
          duration: 0.8, 
          repeat: Infinity, 
          delay: i * 0.2 
        }}
        className="w-3 h-3 bg-blue-600 rounded-full"
      />
    ))}
  </div>
);''',

			"frontend/src/components/ui/Input.jsx": '''import React, { useState } from 'react';
import { motion } from 'framer-motion';

export const Input = ({ 
  label, 
  error, 
  className = '',
  type = 'text',
  ...props 
}) => {
  const [focused, setFocused] = useState(false);
  const [hasValue, setHasValue] = useState(props.value || props.defaultValue);

  return (
    <div className={`relative ${className}`}>
      <input
        type={type}
        className={`peer w-full px-4 py-3 border-2 rounded-lg bg-white transition-all duration-200 placeholder-transparent focus:outline-none ${
          error 
            ? 'border-red-300 focus:border-red-500' 
            : 'border-gray-200 focus:border-blue-500'
        }`}
        placeholder=" "
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => {
          setHasValue(e.target.value);
          props.onChange?.(e);
        }}
        {...props}
      />
      {label && (
        <motion.label
          className={`absolute left-4 transition-all duration-200 pointer-events-none ${
            focused || hasValue
              ? '-top-2 text-xs bg-white px-2 text-blue-600'
              : 'top-3 text-gray-500'
          }`}
          animate={{
            y: focused || hasValue ? -8 : 0,
            scale: focused || hasValue ? 0.85 : 1,
          }}
        >
          {label}
        </motion.label>
      )}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-sm text-red-500"
        >
          {error}
        </motion.div>
      )}
    </div>
  );
};

export const TextArea = ({ label, error, rows = 4, className = '', ...props }) => {
  const [focused, setFocused] = useState(false);
  const [hasValue, setHasValue] = useState(props.value || props.defaultValue);

  return (
    <div className={`relative ${className}`}>
      <textarea
        rows={rows}
        className={`peer w-full px-4 py-3 border-2 rounded-lg bg-white transition-all duration-200 placeholder-transparent focus:outline-none resize-none ${
          error 
            ? 'border-red-300 focus:border-red-500' 
            : 'border-gray-200 focus:border-blue-500'
        }`}
        placeholder=" "
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => {
          setHasValue(e.target.value);
          props.onChange?.(e);
        }}
        {...props}
      />
      {label && (
        <motion.label
          className={`absolute left-4 transition-all duration-200 pointer-events-none ${
            focused || hasValue
              ? '-top-2 text-xs bg-white px-2 text-blue-600'
              : 'top-3 text-gray-500'
          }`}
          animate={{
            y: focused || hasValue ? -8 : 0,
            scale: focused || hasValue ? 0.85 : 1,
          }}
        >
          {label}
        </motion.label>
      )}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-sm text-red-500"
        >
          {error}
        </motion.div>
      )}
    </div>
  );
};''',

			"frontend/src/components/ui/Navigation.jsx": '''import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Menu, X } from 'lucide-react';

export const NavBar = ({ children, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className={`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {children}
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ 
          opacity: isOpen ? 1 : 0, 
          height: isOpen ? 'auto' : 0 
        }}
        className="md:hidden bg-white border-t border-gray-200"
      >
        <div className="px-2 pt-2 pb-3 space-y-1">
          {children}
        </div>
      </motion.div>
    </nav>
  );
};

export const NavLink = ({ children, active = false, className = '', ...props }) => (
  <motion.a
    whileHover={{ y: -2 }}
    className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
      active
        ? 'text-blue-600 bg-blue-50'
        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
    } ${className}`}
    {...props}
  >
    {children}
  </motion.a>
);

export const FloatingTabs = ({ tabs, activeTab, onTabChange, className = '' }) => (
  <div className={`flex bg-gray-100 p-1 rounded-lg ${className}`}>
    {tabs.map((tab) => (
      <motion.button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className={`relative px-6 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
          activeTab === tab.id
            ? 'text-blue-600'
            : 'text-gray-600 hover:text-gray-900'
        }`}
        whileHover={{ y: -1 }}
        whileTap={{ y: 0 }}
      >
        {activeTab === tab.id && (
          <motion.div
            layoutId="activeTab"
            className="absolute inset-0 bg-white rounded-md shadow-sm"
            transition={{ type: "spring", duration: 0.3 }}
          />
        )}
        <span className="relative z-10">{tab.label}</span>
      </motion.button>
    ))}
  </div>
);'''
		}

	@staticmethod
	def _build_app_prompt(plan: Dict[str, Any], project_name: str) -> str:
		features = plan.get('features', [])[:3]
		components = plan.get('frontend', {}).get('components', [])[:2]
		
		return f"""
Create React App.jsx for: {project_name}
Features: {features}
Components: {components}

Requirements:
- React functional component with hooks (NO classes)
- ONLY use existing React Bits components: Button, Card, SplitText, SpinnerLoader, NavBar, NavLink, GradientText
- Use Lucide React icons (Download, Github, ExternalLink, X, etc.)
- API calls to http://localhost:8000/api/v1
- Initialize arrays as [] always
- Safe error handling with try/catch
- Modern TailwindCSS styling with animations
- Responsive design

Critical patterns:
- Always check Array.isArray() before .map()
- Safe localStorage with try/catch around JSON.parse()
- NO ErrorBoundary classes - use functional error handling
- DO NOT import non-existent components
- Create inline components for simple elements like tags

EXACT imports to use:
```jsx
import React, {{useState, useEffect}} from 'react';

// Import all React Bits components with comprehensive fallbacks
let Button, Card, CardHeader, CardBody;
try {{
  const ButtonModule = require('./components/ui/Button');
  Button = ButtonModule.Button;
}} catch (error) {{
  // Fallback Button
  Button = ({{ children, variant = 'primary', size = 'md', className = '', ...props }}) => {{
    const variants = {{
      primary: 'bg-blue-600 hover:bg-blue-700 text-white',
      secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
      outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700'
    }};
    const sizes = {{
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base', 
      lg: 'px-6 py-3 text-lg'
    }};
    return (
      <button 
        className={{`inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${{variants[variant]}} ${{sizes[size]}} ${{className}}`}}
        {{...(props || {{}})}}
      >
        {{children}}
      </button>
    );
  }};
}}

try {{
  const CardModule = require('./components/ui/Card');
  Card = CardModule.Card;
  CardHeader = CardModule.CardHeader;
  CardBody = CardModule.CardBody;
}} catch (error) {{
  // Fallback Card components
  Card = ({{ children, className = '' }}) => (
    <div className={{`bg-white rounded-lg border border-gray-200 shadow-sm ${{className}}`}}>
      {{children}}
    </div>
  );
  CardHeader = ({{ children, className = '' }}) => (
    <div className={{`px-6 py-4 border-b border-gray-200 ${{className}}`}}>
      {{children}}
    </div>
  );
  CardBody = ({{ children, className = '' }}) => (
    <div className={{`px-6 py-4 ${{className}}`}}>
      {{children}}
    </div>
  );
}}

// Import AnimatedText with fallback for reliability
let SplitText, GradientText;
try {{
  const AnimatedTextModule = require('./components/ui/AnimatedText');
  SplitText = AnimatedTextModule.SplitText;
  GradientText = AnimatedTextModule.GradientText;
}} catch (error) {{
  // Fallback SplitText
  SplitText = ({{ text, className = '' }}) => (
    <span className={{`inline-block ${{className}}`}}>{{text}}</span>
  );
  // Fallback GradientText  
  GradientText = ({{ text, className = '' }}) => (
    <span className={{`bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent ${{className}}`}}>
      {{text}}
    </span>
  );
}}

// Import Navigation with fallback for reliability
let NavBar, NavLink;
try {{
  const NavigationModule = require('./components/ui/Navigation');
  NavBar = NavigationModule.NavBar;
  NavLink = NavigationModule.NavLink;
}} catch (error) {{
  // Fallback NavBar
  NavBar = ({{ children, className = '' }}) => (
    <nav className={{`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${{className}}`}}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">{{children}}</div>
      </div>
    </nav>
  );
  NavLink = ({{ href, children, isActive, className = '' }}) => (
    <a href={{href}} className={{`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${{isActive ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}} ${{className}}`}}>
      {{children}}
    </a>
  );
}}

// Import Lucide React icons with fallbacks
let Download, Github, ExternalLink, X;
try {{
  const LucideModule = require('lucide-react');
  Download = LucideModule.Download;
  Github = LucideModule.Github;
  ExternalLink = LucideModule.ExternalLink;
  X = LucideModule.X;
}} catch (error) {{
  // Fallback icon components using Unicode symbols
  Download = ({{ className = '', ...props }}) => (
    <span className={{`inline-block ${{className}}`}} {{...(props || {{}})}} >⬇</span>
  );
  Github = ({{ className = '', ...props }}) => (
    <span className={{`inline-block ${{className}}`}} {{...(props || {{}})}} >⚡</span>
  );
  ExternalLink = ({{ className = '', ...props }}) => (
    <span className={{`inline-block ${{className}}`}} {{...(props || {{}})}} >↗</span>
  );
  X = ({{ className = '', ...props }}) => (
    <span className={{`inline-block ${{className}}`}} {{...(props || {{}})}} >✕</span>
  );
}}

// Include inline SpinnerLoader to avoid import issues
const SpinnerLoader = ({{ size = 'md', className = '' }}) => {{
  const sizes = {{ sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }};
  return <div className={{`${{sizes[size]}} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin ${{className}}`}} />;
}};
```

Return JSX code only, no markdown fences. Make it beautiful!
"""

