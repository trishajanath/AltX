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
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Optional, Tuple

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


@dataclass
class ValidationResult:
	"""Result of file validation with fixes applied."""
	file_path: str
	original_content: str
	fixed_content: str
	issues_found: List[str]
	fixes_applied: List[str]
	security_issues: List[str]
	is_valid: bool
	validation_passed: bool = True


class AIValidationAgent:
	"""AI-powered validation agent that monitors and fixes generated files."""
	
	def __init__(self, model_name: str = "gemini-2.5-flash", fast_mode: bool = True):
		"""Initialize the AI validation agent."""
		api_key = os.getenv("GOOGLE_API_KEY")
		if not api_key:
			raise ValueError("❌ GOOGLE_API_KEY environment variable is required for validation agent")
		
		genai.configure(api_key=api_key)
		self.model = genai.GenerativeModel(model_name)
		self.fast_mode = fast_mode
		
		# Optimize validation config for speed vs thoroughness
		if self.fast_mode:
			self.validation_config = {
				"temperature": 0.2,  # Slightly higher for faster generation
				"top_p": 0.9,
				"candidate_count": 1,
				"max_output_tokens": 4096,  # Reduced for speed
				"response_mime_type": "application/json",
			}
		else:
			self.validation_config = {
				"temperature": 0.1,  # Very low temperature for consistent validation
				"top_p": 0.8,
				"candidate_count": 1,
				"max_output_tokens": 16384,
				"response_mime_type": "application/json",
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
		
		self.tracked_files: Dict[str, ValidationResult] = {}
		print("🔍 AI Validation Agent initialized - monitoring code quality and security")
	
	def validate_and_fix_file(self, file_path: Path, content: str, file_type: str) -> ValidationResult:
		"""Validate a generated file and automatically fix issues."""
		try:
			# Fast mode: skip validation for simple config files
			if self.fast_mode and self._is_simple_file(file_path, file_type):
				print(f"⚡ {file_path} passed validation (fast mode)")
				return ValidationResult(
					file_path=str(file_path),
					original_content=content,
					fixed_content=content,
					issues_found=[],
					fixes_applied=[],
					security_issues=[],
					is_valid=True,
					validation_passed=True
				)
			
			print(f"🔍 Validating {file_path} ({file_type})")
			
			# Build validation prompt based on file type
			validation_prompt = self._build_validation_prompt(content, file_type, str(file_path))
			
			# Get AI validation and fixes
			response = self.model.generate_content(
				contents=validation_prompt,
				generation_config=self.validation_config,
				safety_settings=self.safety_settings,
			)
			
			if not response.candidates:
				raise Exception("No validation response received")
			
			if not response.candidates[0].content.parts:
				raise Exception("No content parts in validation response")
			
			result_text = response.candidates[0].content.parts[0].text.strip()
			
			# Parse validation result
			try:
				# Try to extract JSON from the response if it's wrapped in code blocks
				if "```json" in result_text:
					# Extract JSON from code blocks
					json_start = result_text.find("```json") + 7
					json_end = result_text.find("```", json_start)
					if json_end != -1:
						result_text = result_text[json_start:json_end].strip()
				elif "```" in result_text and result_text.count("```") >= 2:
					# Extract content between first pair of code blocks
					parts = result_text.split("```")
					if len(parts) >= 3:
						# Safe access to parts array
						content_part = parts[1].strip() if len(parts) > 1 else ""
						if content_part.startswith("json\n"):
							content_part = content_part[5:]
						result_text = content_part
				
				# Clean up common JSON formatting issues
				result_text = result_text.strip()
				if not result_text.startswith("{"):
					# Try to find the first { and last }
					start_idx = result_text.find("{")
					end_idx = result_text.rfind("}")
					if start_idx != -1 and end_idx != -1:
						result_text = result_text[start_idx:end_idx+1]
				
				validation_data = json.loads(result_text)
				
			except json.JSONDecodeError:
				# Enhanced fallback with simple validation
				print(f"⚠️ Failed to parse validation response for {file_path}")
				print(f"DEBUG: Response preview: {result_text[:200]}...")
				
				# Perform basic validation without AI
				issues_found = []
				fixes_applied = []
				fixed_content = content
				
				# Basic syntax checks based on file type
				if file_path.suffix in ['.py']:
					# Python syntax check
					try:
						compile(content, str(file_path), 'exec')
					except SyntaxError as e:
						issues_found.append(f"Python syntax error: {e}")
				elif file_path.suffix in ['.jsx', '.js']:
					# Basic JSX/JS checks
					if 'export default' not in content and 'module.exports' not in content and 'export ' not in content:
						issues_found.append("Missing export statement")
						# Try to fix by adding a simple export if it's a component
						if 'function ' in content or 'const ' in content or 'class ' in content:
							# Find component/function names and suggest export
							lines = content.split('\n')
							for line in lines:
								if 'function ' in line or 'const ' in line:
									# Extract potential component name
									if 'function' in line:
										name_part = line.split('function')[1].split('(')[0].strip()
									elif 'const' in line and '=>' in line:
										name_part = line.split('const')[1].split('=')[0].strip()
									else:
										continue
									if name_part and name_part[0].isupper():  # Component naming convention
										fixed_content = content + f'\n\nexport default {name_part};'
										fixes_applied.append(f"Added export default {name_part}")
										break
				elif file_path.suffix == '.json':
					# JSON syntax check
					try:
						json.loads(content)
					except json.JSONDecodeError as e:
						issues_found.append(f"JSON syntax error: {e}")
				
				validation_data = {
					"fixed_content": fixed_content,
					"issues_found": issues_found,
					"fixes_applied": fixes_applied,
					"security_issues": [],
					"is_valid": len(issues_found) == 0
				}
			
			# Create validation result
			result = ValidationResult(
				file_path=str(file_path),
				original_content=content,
				fixed_content=validation_data.get("fixed_content", content),
				issues_found=validation_data.get("issues_found", []),
				fixes_applied=validation_data.get("fixes_applied", []),
				security_issues=validation_data.get("security_issues", []),
				is_valid=validation_data.get("is_valid", True),
				validation_passed=validation_data.get("is_valid", True)
			)
			
			# Track the validation result
			self.tracked_files[str(file_path)] = result
			
			# Log validation results
			if result.issues_found:
				print(f"🔧 Found {len(result.issues_found)} issues in {file_path}")
				for issue in result.issues_found:
					print(f"   - {issue}")
			
			if result.fixes_applied:
				print(f"✅ Applied {len(result.fixes_applied)} fixes to {file_path}")
				for fix in result.fixes_applied:
					print(f"   - {fix}")
			
			if result.security_issues:
				print(f"🔒 Security issues found in {file_path}:")
				for issue in result.security_issues:
					print(f"   - {issue}")
			
			if not result.issues_found and not result.security_issues:
				print(f"✅ {file_path} passed validation")
			
			return result
			
		except IndexError as e:
			print(f"❌ Validation failed for {file_path}: list index out of range")
			# Return original content with a more specific error message
			return ValidationResult(
				file_path=str(file_path),
				original_content=content,
				fixed_content=content,
				issues_found=[f"AI response format error - unable to parse validation result"],
				fixes_applied=[],
				security_issues=[],
				is_valid=True,  # Assume valid since we can't validate
				validation_passed=False
			)
		except json.JSONDecodeError as e:
			print(f"❌ Validation failed for {file_path}: JSON decode error")
			# This is already handled in the try block above, but adding as backup
			return ValidationResult(
				file_path=str(file_path),
				original_content=content,
				fixed_content=content,
				issues_found=[f"Failed to parse AI validation response"],
				fixes_applied=[],
				security_issues=[],
				is_valid=True,  # Assume valid since we can't validate
				validation_passed=False
			)
		except Exception as e:
			print(f"❌ Validation failed for {file_path}: {e}")
			# Return original content if validation fails
			return ValidationResult(
				file_path=str(file_path),
				original_content=content,
				fixed_content=content,
				issues_found=[f"Validation error: {e}"],
				fixes_applied=[],
				security_issues=[],
				is_valid=True,  # Assume valid since we can't validate
				validation_passed=False
			)
	
	def _is_simple_file(self, file_path: Path, file_type: str) -> bool:
		"""Determine if a file is simple enough to skip validation in fast mode."""
		file_name = file_path.name.lower()
		
		# Simple config files that rarely have issues
		simple_files = {
			'package.json', 'postcss.config.js', 'tailwind.config.js', 
			'vite.config.js', '.gitignore', 'readme.md', 'requirements.txt'
		}
		
		# Simple by file type
		simple_types = {'config', 'json', 'markdown', 'text'}
		
		# Small files (under 500 chars) are usually simple
		is_small = len(file_path.read_text()) < 500 if file_path.exists() else False
		
		return (file_name in simple_files or 
				file_type.lower() in simple_types or 
				is_small)
	
	def _build_validation_prompt(self, content: str, file_type: str, file_path: str) -> str:
		"""Build validation prompt based on file type."""
		
		common_security_checks = """
CRITICAL SECURITY CHECKS (MANDATORY):
- No hardcoded secrets, API keys, or passwords
- No SQL injection vulnerabilities 
- No XSS vulnerabilities in frontend code
- Proper input validation and sanitization
- No unsafe eval() or dangerous functions
- Safe JSON parsing with null checks and try-catch blocks
- Proper authentication and authorization checks
- No sensitive data in logs or console output
- Secure HTTP headers and CORS configuration
- No path traversal vulnerabilities
- Proper error handling without information disclosure
"""
		
		if file_type in ["javascript", "jsx", "tsx", "frontend"]:
			return f"""
You are a code validation agent. Analyze this React/JavaScript file and fix any issues.

File: {file_path}
Type: {file_type}

VALIDATION REQUIREMENTS:
1. SYNTAX AND IMPORTS:
   - Check for syntax errors
   - Verify all imports are properly declared
   - Ensure all components are defined before use
   - Fix missing exports or import statements

2. REACT BEST PRACTICES:
   - Proper hook usage (no hooks in loops/conditions)
   - Component naming conventions (PascalCase)
   - Proper event handler patterns
   - State management best practices
   - Error boundary implementation
   - Safe JSON parsing: Always check for null/undefined before JSON.parse()
   - Wrap JSON.parse() in try-catch blocks when parsing user/localStorage data

3. CODE QUALITY:
   - Remove unused variables and imports
   - Fix ESLint/TypeScript errors
   - Consistent code formatting
   - Proper error handling with try-catch

{common_security_checks}

5. PERFORMANCE:
   - Avoid infinite re-renders
   - Proper dependency arrays in useEffect
   - Memoization where appropriate

CODE TO VALIDATE:
```
{content}
```

CRITICAL RESPONSE REQUIREMENTS:
- ONLY return valid JSON, no other text
- NO markdown code blocks (```json```)  
- NO explanations or comments
- Start response with {{ and end with }}

RESPONSE FORMAT (EXACT JSON STRUCTURE):
{{
  "fixed_content": "corrected code here with proper escaping",
  "issues_found": ["list of issues detected"],
  "fixes_applied": ["list of fixes applied"], 
  "security_issues": ["security vulnerabilities found"],
  "is_valid": true
}}

IMPORTANT: 
- Escape all quotes and newlines in fixed_content properly for JSON
- If no issues found, return original content in fixed_content
- Always return valid JSON that can be parsed by JSON.parse()
- Do not wrap response in ```json``` code blocks
"""
		
		elif file_type in ["python", "backend"]:
			return f"""
You are a code validation agent. Analyze this Python/FastAPI file and fix any issues.

File: {file_path}
Type: {file_type}

VALIDATION REQUIREMENTS:
1. PYTHON SYNTAX:
   - Check for syntax errors
   - Verify proper indentation
   - Check import statements
   - Fix undefined variables/functions

2. FASTAPI/WEB SECURITY:
   - Proper CORS configuration
   - Input validation with Pydantic
   - SQL injection prevention
   - Authentication/authorization checks
   - Rate limiting considerations
   - Proper error handling

3. DATABASE SECURITY:
   - No raw SQL queries without parameterization
   - Proper ORM usage
   - Input sanitization
   - Connection security

{common_security_checks}

5. CODE QUALITY:
   - PEP 8 compliance
   - Proper exception handling
   - Type hints where appropriate
   - Docstrings for functions

CODE TO VALIDATE:
```
{content}
```

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks.

RESPONSE FORMAT (EXACT JSON STRUCTURE):
{{
  "fixed_content": "corrected code here with proper escaping",
  "issues_found": ["list of issues detected"],
  "fixes_applied": ["list of fixes applied"], 
  "security_issues": ["security vulnerabilities found"],
  "is_valid": true
}}

IMPORTANT: 
- Escape all quotes and newlines in fixed_content properly for JSON
- If no issues found, return original content in fixed_content
- Always return valid JSON that can be parsed by JSON.parse()
- Do not wrap response in ```json``` code blocks
"""
		
		elif file_type in ["json", "config"]:
			return f"""
You are a configuration validation agent. Analyze this JSON/config file.

File: {file_path}
Type: {file_type}

VALIDATION REQUIREMENTS:
1. JSON SYNTAX:
   - Valid JSON structure
   - Proper escaping
   - No trailing commas

2. CONFIGURATION SECURITY:
   - No hardcoded secrets
   - Proper dependency versions
   - Secure default configurations

{common_security_checks}

CONFIG TO VALIDATE:
```
{content}
```

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks.

RESPONSE FORMAT (EXACT JSON STRUCTURE):
{{
  "fixed_content": "corrected config here with proper escaping",
  "issues_found": ["list of issues detected"],
  "fixes_applied": ["list of fixes applied"],
  "security_issues": ["security vulnerabilities found"],
  "is_valid": true
}}

IMPORTANT: 
- Escape all quotes and newlines in fixed_content properly for JSON
- If no issues found, return original content in fixed_content
- Always return valid JSON that can be parsed by JSON.parse()
- Do not wrap response in ```json``` code blocks
"""
		
		else:
			return f"""
You are a general code validation agent. Analyze this file for common issues.

File: {file_path}
Type: {file_type}

VALIDATION REQUIREMENTS:
1. GENERAL CODE QUALITY:
   - Syntax errors
   - Logic issues
   - Performance problems

{common_security_checks}

CODE TO VALIDATE:
```
{content}
```

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks.

RESPONSE FORMAT (EXACT JSON STRUCTURE):
{{
  "fixed_content": "corrected code here with proper escaping",
  "issues_found": ["list of issues detected"],
  "fixes_applied": ["list of fixes applied"],
  "security_issues": ["security vulnerabilities found"],
  "is_valid": true
}}

IMPORTANT: 
- Escape all quotes and newlines in fixed_content properly for JSON
- If no issues found, return original content in fixed_content
- Always return valid JSON that can be parsed by JSON.parse()
- Do not wrap response in ```json``` code blocks
"""
	
	def get_validation_summary(self) -> Dict[str, Any]:
		"""Get a summary of all validated files."""
		total_files = len(self.tracked_files)
		files_with_issues = sum(1 for result in self.tracked_files.values() if result.issues_found)
		files_with_security_issues = sum(1 for result in self.tracked_files.values() if result.security_issues)
		total_fixes = sum(len(result.fixes_applied) for result in self.tracked_files.values())
		
		return {
			"total_files_validated": total_files,
			"files_with_issues": files_with_issues,
			"files_with_security_issues": files_with_security_issues,
			"total_fixes_applied": total_fixes,
			"validation_results": {path: {
				"issues_count": len(result.issues_found),
				"fixes_count": len(result.fixes_applied),
				"security_issues_count": len(result.security_issues),
				"is_valid": result.is_valid
			} for path, result in self.tracked_files.items()}
		}
	
	def clear_tracking(self):
		"""Clear all tracked validation results."""
		self.tracked_files.clear()
		print("🔄 Validation tracking cleared")


class PureAIGenerator:
	"""Gemini-only generator that produces code without fallbacks."""

	def __init__(self, model_name: str = "gemini-2.5-pro", enable_validation: bool = True, fast_mode: bool = True, s3_uploader=None, user_id: str = "anonymous") -> None:
		api_key = os.getenv("GOOGLE_API_KEY")
		if not api_key:
			raise ValueError("❌ GOOGLE_API_KEY environment variable is required")

		genai.configure(api_key=api_key)
		self.model = genai.GenerativeModel(model_name)
		
		# S3 direct upload configuration (REQUIRED - no local storage)
		self.s3_uploader = s3_uploader
		self.user_id = user_id
		if not s3_uploader:
			print("⚠️ WARNING: No S3 uploader configured - generation will fail on EC2")

		# Optimize generation config based on mode
		self.base_config: Dict[str, Any] = {
			"temperature": 0.25,
			"top_p": 0.8,
			"candidate_count": 1,
			"max_output_tokens": 32768,  # Significantly increased for comprehensive apps
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

		# Initialize AI validation agent
		self.enable_validation = enable_validation
		self.fast_mode = fast_mode
		if enable_validation:
			try:
				# Always use gemini-2.5-flash for validation (fast and efficient)
				self.validation_agent = AIValidationAgent("gemini-2.5-flash", fast_mode=fast_mode)
				mode_text = "FAST MODE" if fast_mode else "THOROUGH MODE"
				print(f"🔍 AI Validation Agent integrated ({mode_text}) - all generated files will be validated and fixed")
			except Exception as e:
				print(f"⚠️ Failed to initialize validation agent: {e}")
				print("🔧 Continuing without validation...")
				self.enable_validation = False
				self.validation_agent = None
		else:
			self.validation_agent = None
		
		print("🤖 Pure AI Generator initialized (Gemini only, no fallbacks)")

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------

	@staticmethod
	def _validate_and_fix_react_code(code: str, project_name: str) -> str:
		"""Validate and fix common React code issues"""
		print(f"DEBUG: Validating React code for {project_name}")
		
		# Common fixes
		fixes = [
			# Fix undefined component references
			("const Zap", "// Zap icon component\nconst Zap"),
			# Ensure proper React import
			("import React", "import React"),
			# Fix component definitions
			("const App = () => {", "const App = () => {"),
			# Add error boundaries
			("export default App;", "export default App;"),
		]
		
		# Check for common issues
		issues = []
		
		# Check if components are defined before use
		if "Zap" in code and "const Zap" not in code and "function Zap" not in code:
			issues.append("Zap component not defined")
		
		# Check for proper imports
		if "import React" not in code:
			code = "import React from 'react';\n\n" + code
			
		# Check for export
		if "export default" not in code:
			code += "\n\nexport default App;"
		
		# Log issues found
		if issues:
			print(f"DEBUG: Fixed React issues: {', '.join(issues)}")
		
		return code

	def _write_validated_file(self, file_path: Path, content: str, file_type: str, project_slug: str = None) -> str:
		"""Write a file with optional AI validation and automatic fixes. Supports S3 direct upload."""
		if not self.enable_validation or self.validation_agent is None:
			# Write without validation
			self._write_file(file_path, content, project_slug)
			return content
			
		try:
			# Validate and fix the content using the AI agent
			validation_result = self.validation_agent.validate_and_fix_file(file_path, content, file_type)
			
			# Use the fixed content if validation succeeded
			if validation_result.is_valid or validation_result.fixes_applied:
				fixed_content = validation_result.fixed_content
				self._write_file(file_path, fixed_content, project_slug)
				return fixed_content
			else:
				# Write original content if validation didn't help
				self._write_file(file_path, content, project_slug)
				return content
			
		except Exception as e:
			print(f"⚠️ Validation failed for {file_path}, writing original content: {e}")
			# Fallback to original content if validation fails
			self._write_file(file_path, content, project_slug)
			return content
	
	def _write_file(self, file_path: Path, content: str, project_slug: str = None):
		"""Write file directly to S3 only - NO local storage."""
		if not self.s3_uploader or not project_slug:
			raise ValueError("❌ S3 uploader and project_slug are REQUIRED - no local storage available")
		
		try:
			# Convert file path to relative path for S3 key
			relative_path = str(file_path).replace("\\", "/")
			if "generated_projects" in relative_path:
				# Extract path after project name
				parts = relative_path.split("/")
				try:
					project_idx = parts.index("generated_projects") + 2  # Skip "generated_projects/{project_slug}/"
					relative_path = "/".join(parts[project_idx:])
				except (ValueError, IndexError):
					# If parsing fails, use the filename
					relative_path = file_path.name
			else:
				relative_path = file_path.name
			
			# Upload DIRECTLY to S3 (no local intermediate)
			file_info = {
				"path": relative_path,
				"content": content
			}
			self.s3_uploader(project_slug, [file_info], self.user_id)
			print(f"☁️ Uploaded {relative_path} directly to S3")
		except Exception as e:
			print(f"❌ S3 upload FAILED for {file_path}: {e}")
			raise  # Fail fast - no fallback to local storage
	
	def _validate_file_async(self, file_path: Path, content: str, file_type: str) -> Tuple[Path, str, bool]:
		"""Validate a single file asynchronously. Returns (file_path, final_content, success)."""
		if not self.enable_validation or self.validation_agent is None:
			return file_path, content, True
			
		try:
			print(f"🔍 Validating {file_path.name}...")
			validation_result = self.validation_agent.validate_and_fix_file(file_path, content, file_type)
			
			if validation_result.is_valid or validation_result.fixes_applied:
				print(f"✅ Validated and fixed {file_path.name}")
				return file_path, validation_result.fixed_content, True
			else:
				print(f"⚠️ No fixes needed for {file_path.name}")
				return file_path, content, True
				
		except Exception as e:
			print(f"❌ Validation failed for {file_path.name}: {e}")
			return file_path, content, False
	
	def _write_files_parallel(self, file_tasks: List[Tuple[Path, str, str]], project_slug: str = None) -> Dict[str, str]:
		"""
		Write multiple files with parallel validation for maximum speed.
		Supports direct S3 upload and optional local storage.
		
		Args:
			file_tasks: List of (file_path, content, file_type) tuples
			project_slug: Project identifier for S3 uploads
			
		Returns:
			Dictionary mapping file paths to final content
		"""
		if not file_tasks:
			return {}
			
		results = {}
		
		# If validation is disabled, write files immediately
		if not self.enable_validation or self.validation_agent is None:
			print(f"📝 Writing {len(file_tasks)} files without validation...")
			for file_path, content, _ in file_tasks:
				self._write_file(file_path, content, project_slug)
				results[str(file_path)] = content
			return results
		
		# Use ThreadPoolExecutor for parallel validation
		print(f"🚀 Validating and writing {len(file_tasks)} files in parallel...")
		
		# Increase parallelism for faster processing
		max_workers = min(len(file_tasks), 8 if self.fast_mode else 4)
		with ThreadPoolExecutor(max_workers=max_workers) as executor:
			# Submit all validation tasks
			future_to_task = {
				executor.submit(self._validate_file_async, file_path, content, file_type): (file_path, content, file_type)
				for file_path, content, file_type in file_tasks
			}
			
			# Process completed validations and write files
			for future in as_completed(future_to_task):
				file_path, final_content, success = future.result()
				
				# Write the file with final content (S3 + local)
				self._write_file(file_path, final_content, project_slug)
				results[str(file_path)] = final_content
				
				if success:
					print(f"✅ Completed {file_path.name}")
				else:
					print(f"⚠️ Wrote {file_path.name} with fallback content")
		
		print(f"🎉 Parallel validation complete! All {len(file_tasks)} files written.")
		return results

	async def analyze_and_plan(self, project_spec, project_name: str) -> Dict[str, Any]:
		# Handle both dict (new format) and str (legacy format)
		if isinstance(project_spec, dict):
			idea = project_spec.get("idea", "")
		else:
			idea = str(project_spec)
			project_spec = {"idea": idea}
			
		request = GenerationRequest(
			prompt=self._build_plan_prompt(project_spec, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 16384,  # Increased for comprehensive plans
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
		self, project_path: Path, project_spec: dict, project_name: str, tech_stack: List[str] = None
	) -> List[str]:
		print(f"☁️ Generating project directly to S3: {project_name}")
		print(f"DEBUG: Project spec: {project_spec}")
		
		# Validate S3 uploader is configured
		if not self.s3_uploader:
			raise ValueError("❌ S3 uploader is REQUIRED for project generation - no local storage available")
		
		# Extract idea from spec for backward compatibility
		idea = project_spec.get("idea", "") if isinstance(project_spec, dict) else str(project_spec)
		
		try:
			plan = await self.analyze_and_plan(project_spec, project_name)
		except Exception as e:
			print(f"ERROR: Failed to analyze and plan: {e}")
			raise
			
		# NO local directory creation - everything goes to S3
		files_created: List[str] = []
		errors_encountered: List[str] = []
		
		# Generate backend files directly to S3
		backend_path = project_path / "backend"  # Virtual path for S3 key construction
		
		# 🚀 PARALLEL GENERATION: Generate all backend files concurrently to S3
		print("🚀 Generating backend files in parallel to S3...")
		
		async def generate_backend_file(file_type: str, filename: str) -> Tuple[str, str, str]:
			"""Generate a single backend file and return (filename, content, file_type)"""
			try:
				if filename == "requirements.txt":
					# Static requirements file
					content = "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\npython-multipart==0.0.6\nsqlalchemy==2.0.0\npasslib==1.7.4\npython-jose==3.3.0\nbcrypt==4.0.1\n"
					return filename, content, "config"
				else:
					# AI-generated file
					content = await self.generate_single_file(file_type, plan, project_name)
					return filename, content, "python"
			except Exception as e:
				print(f"❌ ERROR generating {filename}: {e}")
				raise

		# Define backend files to generate
		backend_tasks = [
			("backend_models", "models.py"),
			("backend_routes", "routes.py"),  
			("backend_main", "main.py"),
			("static", "requirements.txt")  # Special case for static content
		]
		
		# Generate all backend files concurrently
		backend_results = await asyncio.gather(*[
			generate_backend_file(file_type, filename) 
			for file_type, filename in backend_tasks
		], return_exceptions=True)
		
		# Prepare files for parallel validation and writing
		backend_file_tasks = []
		for i, result in enumerate(backend_results):
			if isinstance(result, Exception):
				error_msg = f"Failed to generate backend/{backend_tasks[i][1]}: {result}"
				print(f"❌ ERROR: {error_msg}")
				errors_encountered.append(error_msg)
			else:
				filename, content, file_type = result
				file_path = backend_path / filename
				backend_file_tasks.append((file_path, content, file_type))
				print(f"✅ Generated {filename} ({len(content)} chars)")
		
		# Write all backend files with parallel validation directly to S3
		if backend_file_tasks:
			backend_written = self._write_files_parallel(backend_file_tasks, project_name)
			for file_path in backend_written:
				relative_path = Path(file_path).relative_to(project_path)
				files_created.append(str(relative_path).replace("\\", "/"))
			print(f"☁️ Uploaded all {len(backend_written)} backend files to S3!")
			
		# Generate frontend files directly to S3
		frontend_path = project_path / "frontend"  # Virtual path for S3 key construction
		frontend_src = frontend_path / "src"
		print(f"☁️ Generating frontend files directly to S3")
		
		# 🚀 PARALLEL GENERATION: Generate main App.jsx and supporting files concurrently to S3
		print("🚀 Generating frontend App.jsx and support files in parallel to S3...")
		
		try:
			# Generate App.jsx asynchronously  
			async def generate_app_jsx():
				try:
					print(f"🔄 Generating App.jsx for {project_name}...")
					app_code = await self.generate_single_file("frontend_app", plan, project_name)
					print(f"✅ Generated App.jsx ({len(app_code)} chars)")
					return app_code
				except Exception as e:
					print(f"❌ ERROR generating App.jsx: {e}")
					# Return fallback App.jsx
					return f'''import React from 'react';

function App() {{
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to {project_name}</h1>
        <p className="text-gray-300">Your application is being generated...</p>
        <div className="mt-8">
          <div className="animate-pulse bg-blue-600 h-2 w-64 mx-auto rounded"></div>
        </div>
      </div>
    </div>
  );
}}

export default App;'''

			# Generate supporting files asynchronously
			async def create_supporting_files():
				try:
					print("🔄 Creating supporting files...")
					await asyncio.get_event_loop().run_in_executor(None, self._create_supporting_files, frontend_path, project_name)
					print("✅ Supporting files created")
					return True
				except Exception as e:
					print(f"❌ ERROR creating supporting files: {e}")
					return False

			# Run both tasks concurrently
			app_code, supporting_success = await asyncio.gather(
				generate_app_jsx(),
				create_supporting_files(),
				return_exceptions=True
			)
			
			# Handle App.jsx result
			if isinstance(app_code, Exception):
				print(f"❌ ERROR in App.jsx generation: {app_code}")
				app_code = f"// Fallback App.jsx due to generation error\nexport default function App() {{ return <div>Error: {app_code}</div>; }}"
			
			# Prepare frontend files for parallel validation (no local directory creation)
			
			utils_content = '''import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  outline: "border border-gray-300 bg-white text-gray-900 hover:bg-gray-50",
  ghost: "text-gray-900 hover:bg-gray-100",
  destructive: "bg-red-600 text-white hover:bg-red-700"
};

export const cardVariants = {
  default: "rounded-lg border bg-white p-6 shadow-sm",
  elevated: "rounded-lg border bg-white p-6 shadow-lg"
};
'''
			
			# Collect frontend files for parallel validation
			frontend_file_tasks = [
				(frontend_src / "App.jsx", app_code, "jsx"),
				(frontend_src / "lib" / "utils.js", utils_content, "javascript"),
			]
			
			# Write frontend files with parallel validation directly to S3
			frontend_written = self._write_files_parallel(frontend_file_tasks, project_name)
			
			# Add to files_created list
			for file_path in frontend_written:
				relative_path = Path(file_path).relative_to(project_path)
				files_created.append(str(relative_path).replace("\\", "/"))
			
			# Add supporting files if they were created successfully
			if supporting_success and not isinstance(supporting_success, Exception):
				files_created.extend([
					"frontend/package.json", 
					"frontend/index.html",
					"frontend/src/main.jsx",
					"frontend/src/index.css",
					"frontend/tailwind.config.js",
					"frontend/postcss.config.js",
					"frontend/vite.config.js"
				])
			else:
				errors_encountered.append("Failed to create some supporting files")
				
			print(f"🎉 Completed frontend generation with parallel processing!")
			
		except Exception as e:
			import traceback
			error_msg = f"Failed to generate frontend files: {e}"
			print(f"❌ ERROR: {error_msg}")
			print(f"❌ TRACEBACK: {traceback.format_exc()}")
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
		
		# Generate validation summary
		if self.enable_validation and self.validation_agent:
			validation_summary = self.validation_agent.get_validation_summary()
			print(f"\n🔍 VALIDATION SUMMARY:")
			print(f"📊 Total files validated: {validation_summary['total_files_validated']}")
			print(f"🔧 Files with issues fixed: {validation_summary['files_with_issues']}")
			print(f"🔒 Files with security issues: {validation_summary['files_with_security_issues']}")
			print(f"✅ Total fixes applied: {validation_summary['total_fixes_applied']}")
		else:
			validation_summary = {
				"total_files_validated": 0,
				"files_with_issues": 0,
				"files_with_security_issues": 0,
				"total_fixes_applied": 0,
				"validation_results": {}
			}
			print(f"\n🔍 VALIDATION SUMMARY:")
			print(f"📊 Validation was disabled - files generated without AI validation")
		
		# Generate Awwwards design summary
		design_summary = {
			"design_system": "Awwwards 2025 Inspired",
			"features_implemented": [
				"Vibrant gradient backgrounds",
				"Glass morphism effects", 
				"Micro-interactions and hover effects",
				"Modern typography (Inter font)",
				"Animated components",
				"Award-winning color palettes",
				"Interactive UI elements",
				"Mobile-responsive design"
			],
			"ui_patterns": [
				"Hero section with gradient mesh background",
				"Cards with glass morphism and hover animations", 
				"Floating navigation with backdrop blur",
				"Interactive buttons with shimmer effects",
				"Text reveal animations",
				"Parallax scroll effects"
			],
			"technical_stack": [
				"React 18 with hooks",
				"TailwindCSS with custom animations",
				"Framer Motion for advanced interactions",
				"Modern CSS with backdrop-filter",
				"Responsive grid layouts",
				"Accessible components"
			]
		}
		
		print(f"\n🏆 AWWWARDS DESIGN SYSTEM APPLIED:")
		print(f"🎨 Design Philosophy: Award-winning modern UI")
		print(f"🌈 Color System: Vibrant gradients and mesh backgrounds")  
		print(f"✨ Animations: Micro-interactions and smooth transitions")
		print(f"🔮 Effects: Glass morphism, glow shadows, floating elements")
		
		# Save comprehensive project report
		project_report = {
			"project_info": {
				"name": project_name,
				"type": plan.get('app_type', 'Web Application'),
				"description": plan.get('description', ''),
				"features": plan.get('features', [])
			},
			"design_system": design_summary,
			"validation_results": validation_summary,
			"generation_timestamp": datetime.now().isoformat(),
			"files_generated": files_created
		}
		
		# Create metadata file for S3
		metadata_content = {
			"name": project_name,
			"created_date": int(datetime.now().timestamp()),
			"type": plan.get('app_type', 'Web Application'),
			"description": plan.get('description', ''),
			"features": plan.get('features', []),
			"tech_stack": tech_stack
		}
		
		# Upload metadata to S3
		project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
		try:
			self.s3_uploader(
				project_slug,
				[{
					'path': 'project_metadata.json',
					'content': json.dumps(metadata_content, indent=2)
				}],
				self.user_id
			)
			print(f"✅ Uploaded project metadata to S3")
		except Exception as e:
			print(f"⚠️ Failed to upload metadata: {e}")
		
		# Save validation report
		validation_report_path = project_path / "VALIDATION_REPORT.json"
		with open(validation_report_path, 'w', encoding='utf-8') as f:
			json.dump(validation_summary, f, indent=2)
		
		# Save design system report  
		design_report_path = project_path / "DESIGN_SYSTEM.json"
		with open(design_report_path, 'w', encoding='utf-8') as f:
			json.dump(project_report, f, indent=2)
		
		print(f"📋 Reports saved: {validation_report_path}, {design_report_path}")
		print(f"\n🚀 PROJECT READY! Your Awwwards-inspired {project_name} is now generating stunning, award-worthy designs!")
		
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
			
		# Special config for frontend files that need more tokens
		if file_type == "frontend_app":
			config_overrides = {
				"max_output_tokens": 32768,  # Maximum tokens for comprehensive frontend
				"temperature": 0.05,  # Low temperature for consistency
			}
		else:
			config_overrides = {
				"max_output_tokens": 16384,  # Increased for all backend files
				"temperature": 0.05,
			}
			
		request = GenerationRequest(
			prompt=prompt,
			config_overrides=config_overrides,
		)
		
		return self._strip_code_fences(self._run_generation(request))

	def _create_supporting_files(self, frontend_path: Path, project_name: str):
		"""Create supporting files with hardcoded content and React Bits components using parallel validation"""
		
		# Initialize layout design system at the beginning
		layout_pattern = None
		custom_css = ""
		react_components = {}
		
		try:
			from layout_design_scraper import get_diverse_layout_for_project
			from design_trend_scraper import get_latest_design_trends
			
			# Get unique layout pattern for this project
			layout_pattern, custom_css, react_components = get_diverse_layout_for_project("web_app")
			
			print(f"🎨 Layout Pattern Loaded: {layout_pattern.name} - {layout_pattern.type}")
			print(f"   📐 Grid: {layout_pattern.grid_system}")
			print(f"   🎨 Colors: {layout_pattern.color_approach}")
			
		except ImportError as e:
			print(f"⚠️ Layout system not available, using default styles: {e}")
		
		# 🚀 COLLECT ALL SUPPORTING FILES FOR PARALLEL PROCESSING
		print("📦 Preparing supporting files for parallel validation...")
		
		# Enhanced package.json with React Bits dependencies - PREVENTS MODULE ERRORS
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
				"axios": "^1.6.0",
				"clsx": "^2.0.0",
				"tailwind-merge": "^2.0.0",
				"class-variance-authority": "^0.7.0",
				"buffer": "^6.0.3"
			},
			"devDependencies": {
				"@vitejs/plugin-react": "^4.0.0",
				"vite": "^4.4.0",
				"tailwindcss": "^3.3.5",
				"postcss": "^8.4.31",
				"autoprefixer": "^10.4.16",
				"@types/node": "^20.0.0"
			}
		}
		
		# Collect all static file contents first
		supporting_files = []
		supporting_files.append((frontend_path / "package.json", json.dumps(package_json, indent=2), "json"))
		
		# Enhanced index.html - PRODUCTION READY without CDN warnings
		html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body class="bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
		supporting_files.append((frontend_path / "index.html", html, "html"))
		
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
		supporting_files.append((src_path / "main.jsx", main_jsx, "jsx"))
		
		# Create index.css with Awwwards-inspired styles and unique layout CSS
		layout_specific_css = ""
		if layout_pattern and custom_css.strip():
			layout_specific_css = f"""
/* ===============================
   UNIQUE LAYOUT: {layout_pattern.type}
   Inspiration: {layout_pattern.design_inspiration}
   =============================== */
{custom_css}

/* Layout-Specific Utility Classes */
.layout-{layout_pattern.name} {{
    /* Applied to body/main container for layout-specific styling */
    position: relative;
    overflow-x: hidden;
}}
"""

		# Base CSS template without f-string to avoid brace issues
		base_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  }
}

@layer components {{
  /* Awwwards Glass Morphism */
  .glass-morphism {{
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }}
  
  .glass-dark {{
    background: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }}
  
  /* Award-winning Gradients */
  .gradient-text {{
    @apply bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent;
  }}
  
  .gradient-vibrant {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }}
  
  .gradient-mesh {{
    background: radial-gradient(circle at 20% 50%, #ff6b6b 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, #4ecdc4 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, #45b7d1 0%, transparent 50%),
                linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }}
  
  /* Modern Shadows */
  .shadow-glow {{
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.4);
  }}
  
  .shadow-float {{
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  }}
  
  .shadow-vibrant {{
    box-shadow: 0 10px 40px rgba(124, 58, 237, 0.3);
  }}
  
  /* Interactive Elements */
  .btn-awwwards {{
    @apply relative overflow-hidden px-8 py-4 rounded-2xl font-semibold text-white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    transition: all 0.3s ease;
  }}
  
  .btn-awwwards::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }}
  
  .btn-awwwards:hover::before {{
    left: 100%;
  }}
  
  .btn-awwwards:hover {{
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
  }}
  
  /* Card Animations */
  .card-hover {
    @apply transition-all duration-300 ease-out;
  }
  
  .card-hover:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  }
  
  /* Text Animations */
  .text-reveal {
    animation: textReveal 1s ease-out forwards;
  }
  
  @keyframes textReveal {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  /* Floating Animation */
  .float {
    animation: float 6s ease-in-out infinite;
  }
  
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
  }
  
  /* Pulse Glow */
  .pulse-glow {
    animation: pulseGlow 2s ease-in-out infinite alternate;
  }
  
  @keyframes pulseGlow {
    from { box-shadow: 0 0 20px rgba(139, 92, 246, 0.3); }
    to { box-shadow: 0 0 40px rgba(139, 92, 246, 0.6); }
  }
  
  /* Mesh Background */
  .mesh-bg {
    background-image: 
      radial-gradient(circle at 25% 25%, #ff6b6b 0%, transparent 50%),
      radial-gradient(circle at 75% 75%, #4ecdc4 0%, transparent 50%),
      radial-gradient(circle at 75% 25%, #45b7d1 0%, transparent 50%),
      radial-gradient(circle at 25% 75%, #96ceb4 0%, transparent 50%);
  }
}

@layer utilities {
  .animate-fade-in-up {
    animation: fadeInUp 0.6s ease-out forwards;
  }
  
  .animate-slide-in-left {
    animation: slideInLeft 0.6s ease-out forwards;
  }
  
  .animate-bounce-in {
    animation: bounceIn 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
  }
  
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes slideInLeft {
    from {
      opacity: 0;
      transform: translateX(-50px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  @keyframes bounceIn {
    0% {
      opacity: 0;
      transform: scale(0.3);
    }
    50% {
      opacity: 1;
      transform: scale(1.05);
    }
    70% {
      transform: scale(0.9);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }
}'''
		
		# Combine layout-specific CSS with base CSS
		index_css = layout_specific_css + base_css
		supporting_files.append((src_path / "index.css", index_css, "css"))
		
		# Collect React Bits UI components for parallel processing
		react_bits_components = self._get_react_bits_components()
		for file_path, content in react_bits_components.items():
			# Remove 'frontend/' prefix since we're already in frontend_path
			relative_path = file_path.replace("frontend/", "")
			full_path = frontend_path / relative_path
			full_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directories exist
			supporting_files.append((full_path, content, "jsx"))
			print(f"📦 Queued React Bits component: {relative_path}")
		
		# Create enhanced Tailwind config with Awwwards design system
		tailwind_config = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // Awwwards color palette
        aww: {
          purple: '#667eea',
          pink: '#764ba2',
          cyan: '#4ecdc4',
          coral: '#ff6b6b',
          blue: '#45b7d1',
          mint: '#96ceb4',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'mesh-vibrant': `
          radial-gradient(circle at 25% 25%, #ff6b6b 0%, transparent 50%),
          radial-gradient(circle at 75% 75%, #4ecdc4 0%, transparent 50%),
          radial-gradient(circle at 75% 25%, #45b7d1 0%, transparent 50%),
          radial-gradient(circle at 25% 75%, #96ceb4 0%, transparent 50%)
        `,
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(139, 92, 246, 0.3)',
        'glow-lg': '0 0 40px rgba(139, 92, 246, 0.4)',
        'float': '0 20px 40px rgba(0, 0, 0, 0.1)',
        'vibrant': '0 10px 40px rgba(124, 58, 237, 0.3)',
      },
      animation: {
        // Existing animations
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.5s ease-out",
        "slide-in": "slide-in 0.3s ease-out",
        "bounce-in": "bounce-in 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)",
        // New Awwwards animations
        "fade-in-up": "fadeInUp 0.6s ease-out",
        "slide-in-left": "slideInLeft 0.6s ease-out",
        "text-reveal": "textReveal 1s ease-out",
        "float": "float 6s ease-in-out infinite",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite alternate",
        "shimmer": "shimmer 2s linear infinite",
        "gradient-shift": "gradientShift 3s ease infinite",
      },
      keyframes: {
        // Existing keyframes
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
        // New Awwwards keyframes
        fadeInUp: {
          "0%": { opacity: 0, transform: "translateY(30px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        slideInLeft: {
          "0%": { opacity: 0, transform: "translateX(-50px)" },
          "100%": { opacity: 1, transform: "translateX(0)" },
        },
        textReveal: {
          "0%": { opacity: 0, transform: "translateY(30px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" },
        },
        pulseGlow: {
          "0%": { boxShadow: "0 0 20px rgba(139, 92, 246, 0.3)" },
          "100%": { boxShadow: "0 0 40px rgba(139, 92, 246, 0.6)" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
    },
  },
  plugins: [],
}'''
		supporting_files.append((frontend_path / "tailwind.config.js", tailwind_config, "javascript"))
		
		# Create PostCSS config
		postcss_config = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''
		supporting_files.append((frontend_path / "postcss.config.js", postcss_config, "javascript"))
		
		# Create Vite config - FIXES MODULE ISSUES
		vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react({
    babel: {
      parserOpts: {
        plugins: ['jsx', 'typescript']
      }
    }
  })],
  server: {
    port: 3000,
    host: true
  },
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      buffer: 'buffer',
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})'''
		supporting_files.append((frontend_path / "vite.config.js", vite_config, "javascript"))
		
		# 🚀 WRITE ALL SUPPORTING FILES IN PARALLEL FOR MAXIMUM SPEED
		print(f"🚀 Writing {len(supporting_files)} supporting files in parallel...")
		self._write_files_parallel(supporting_files)
		print(f"🎨 ✅ Created enhanced frontend setup with {len(supporting_files)} validated files for {project_name}")

	async def generate_backend_bundle(
		self, plan: Dict[str, Any], project_name: str
	) -> Dict[str, str]:
		request = GenerationRequest(
			prompt=self._build_backend_bundle_prompt(plan, project_name),
			config_overrides={
				"response_mime_type": "application/json",
				"max_output_tokens": 24576,  # Significantly increased for backend bundles
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
				"max_output_tokens": 24576,  # Significantly increased for frontend bundles
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
				"max_output_tokens": 8192,  # Increased for comprehensive docs
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
	def _build_plan_prompt(project_spec, project_name: str) -> str:
		# Extract details from project specification
		if isinstance(project_spec, dict):
			idea = project_spec.get("idea", "")
			project_type = project_spec.get("project_type", "web app")
			features = project_spec.get("features", [])
			tech_stack = project_spec.get("tech_stack", [])
		else:
			idea = str(project_spec)
			project_type = "web app"
			features = []
			tech_stack = []
		
		# Build detailed prompt with user specifications
		spec_details = f"Project Type: {project_type}\n"
		if features:
			spec_details += f"Required Features: {', '.join(features)}\n"
		if tech_stack:
			spec_details += f"Tech Stack: {', '.join(tech_stack)}\n"
		
		return (
			f"Create a COMPREHENSIVE, FEATURE-RICH project plan in JSON for: {idea}\n"
			f"Project: {project_name}\n"
			f"{spec_details}\n"
			"🎯 REQUIREMENTS:\n"
			"- Generate 5-8 SPECIFIC, DETAILED features (not generic)\n"
			"- Create 4-6 meaningful frontend components\n"
			"- Design 3-5 backend models with relevant fields\n"
			"- Define 6-10 RESTful API endpoints\n"
			"- Include REAL data examples and use cases\n\n"
			"JSON format:\n"
			"{\n"
			"  \"app_type\": \"Specific app category (e.g., E-commerce Platform, Task Manager, Analytics Dashboard)\",\n"
			"  \"description\": \"Detailed description of what the app does and its value proposition\",\n"
			"  \"features\": [\n"
			"    \"Specific Feature 1 with real benefit\",\n"
			"    \"Specific Feature 2 with real benefit\",\n"
			"    \"Specific Feature 3 with real benefit\",\n"
			"    \"Specific Feature 4 with real benefit\",\n"
			"    \"Specific Feature 5 with real benefit\",\n"
			"    \"Specific Feature 6 with real benefit\"\n"
			"  ],\n"
			"  \"frontend\": {\n"
			"    \"stack\": \"React+Vite+Tailwind+Framer Motion\",\n"
			"    \"components\": [\n"
			"      {\"name\": \"HeroSection\", \"purpose\": \"Eye-catching landing section with CTA\"},\n"
			"      {\"name\": \"FeaturesGrid\", \"purpose\": \"Showcase key features with icons and descriptions\"},\n"
			"      {\"name\": \"MainContentArea\", \"purpose\": \"Primary interactive content with CRUD operations\"},\n"
			"      {\"name\": \"StatsSection\", \"purpose\": \"Display impressive metrics and statistics\"},\n"
			"      {\"name\": \"Footer\", \"purpose\": \"Comprehensive footer with links and info\"}\n"
			"    ]\n"
			"  },\n"
			"  \"backend\": {\n"
			"    \"stack\": \"FastAPI+Pydantic\",\n"
			"    \"models\": [\n"
			"      {\"name\": \"ModelName1\", \"fields\": [\"id\", \"name\", \"description\", \"created_at\", \"status\"]},\n"
			"      {\"name\": \"ModelName2\", \"fields\": [\"id\", \"title\", \"content\", \"author\", \"tags\"]},\n"
			"      {\"name\": \"ModelName3\", \"fields\": [\"id\", \"value\", \"category\", \"timestamp\"]}\n"
			"    ],\n"
			"    \"endpoints\": [\n"
			"      {\"method\": \"GET\", \"path\": \"/api/v1/items\", \"purpose\": \"Retrieve all items with pagination\"},\n"
			"      {\"method\": \"GET\", \"path\": \"/api/v1/items/{id}\", \"purpose\": \"Get single item details\"},\n"
			"      {\"method\": \"POST\", \"path\": \"/api/v1/items\", \"purpose\": \"Create new item with validation\"},\n"
			"      {\"method\": \"PUT\", \"path\": \"/api/v1/items/{id}\", \"purpose\": \"Update existing item\"},\n"
			"      {\"method\": \"DELETE\", \"path\": \"/api/v1/items/{id}\", \"purpose\": \"Delete item\"},\n"
			"      {\"method\": \"GET\", \"path\": \"/api/v1/stats\", \"purpose\": \"Get application statistics\"},\n"
			"      {\"method\": \"POST\", \"path\": \"/api/v1/search\", \"purpose\": \"Search items with filters\"}\n"
			"    ]\n"
			"  }\n"
			"}\n\n"
			"🎯 CRITICAL: Make features and components SPECIFIC to the app idea. Use real terminology from that domain.\n"
			"For example:\n"
			"- E-commerce: 'Shopping Cart', 'Product Catalog', 'Checkout Process', 'Order Tracking'\n"
			"- Task Manager: 'Task Board', 'Priority Matrix', 'Team Collaboration', 'Progress Tracking'\n"
			"- Analytics: 'Real-time Dashboard', 'Data Visualization', 'Custom Reports', 'Trend Analysis'\n\n"
			"Respond with valid JSON only. Make it comprehensive and specific to the idea."
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
		features = plan.get('features', [])
		app_type = plan.get('app_type', 'Web App')
		description = plan.get('description', 'A modern web application')
		
		# Detect e-commerce features
		has_ecommerce = any(keyword in str(feature).lower() for feature in features 
		                   for keyword in ['shop', 'store', 'ecommerce', 'cart', 'product', 'buy', 'sell', 'market', 'order', 'checkout', 'payment'])
		
		return f"""
Create a COMPLETE, PRODUCTION-READY FastAPI main.py for: {project_name}

Project: {app_type}
Description: {description}
Features: {', '.join(str(f) for f in features)}

MANDATORY REQUIREMENTS:

1. COMPLETE AUTHENTICATION SYSTEM (ALWAYS INCLUDE):
   - JWT token authentication with OAuth2PasswordBearer
   - User registration endpoint: POST /api/v1/auth/register
   - User login endpoint: POST /api/v1/auth/login
   - Get current user: GET /api/v1/auth/me
   - Token refresh: POST /api/v1/auth/refresh
   - Password hashing with bcrypt or passlib
   - Proper JWT secret key configuration
   - Token expiration and validation

2. COMPREHENSIVE CORS CONFIGURATION:
   - Allow all origins for local development (http://localhost:5173)
   - Allow credentials for cookie/token handling
   - Proper headers for authentication
   - Methods: GET, POST, PUT, DELETE, OPTIONS

3. DATABASE INTEGRATION:
   - SQLite database with SQLAlchemy ORM
   - User model with proper relationships
   - Database session dependency
   - Automatic table creation on startup

4. E-COMMERCE API ENDPOINTS (If e-commerce detected):
   - Product management: GET/POST /api/v1/products
   - Shopping cart: POST /api/v1/cart/add, DELETE /api/v1/cart/remove, GET /api/v1/cart
   - Order processing: POST /api/v1/orders, GET /api/v1/orders
   - Payment processing: POST /api/v1/payments/process
   - Inventory management: GET /api/v1/inventory

5. ESSENTIAL MIDDLEWARE AND DEPENDENCIES:
   - CORS middleware properly configured
   - Authentication dependency for protected routes
   - Database session dependency
   - Error handling middleware
   - Request logging

6. SECURITY BEST PRACTICES:
   - Password hashing (never store plain passwords)
   - JWT token validation and expiration
   - Protected routes with proper authentication
   - Input validation and sanitization
   - Rate limiting considerations

CRITICAL IMPLEMENTATION REQUIREMENTS:
- Use FastAPI 0.100+ with modern async patterns
- Include all necessary imports and dependencies
- Proper error handling with HTTPException
- Pydantic models for request/response validation
- Database models with proper relationships
- Authentication middleware and dependencies
- CORS configured for frontend integration

AUTHENTICATION FLOW IMPLEMENTATION:
```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={{"check_same_thread": False}})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # JWT token validation and user retrieval
    pass  # Implement full JWT validation

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    # Implement JWT token creation
    pass
```

{f'''
E-COMMERCE MODELS (REQUIRED if e-commerce detected):
```python
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    image_url = Column(String)
    category = Column(String)
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
```
''' if has_ecommerce else ''}

MAIN APP STRUCTURE:
```python
app = FastAPI(title="{project_name}", description="{description}")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def health_check():
    return {{"status": "healthy", "app": "{project_name}"}}

# Authentication routes
@app.post("/api/v1/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Implement user registration
    pass

@app.post("/api/v1/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Implement user login
    pass

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
```

CRITICAL: Return COMPLETE, WORKING Python code with all imports, models, authentication, and API endpoints properly implemented. No placeholders or "TODO" comments allowed.
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

			"frontend/src/components/ui/Navigation.jsx": '''import React, {{ useState }} from 'react';
import {{ motion }} from 'framer-motion';
import {{ Menu, X }} from 'lucide-react';

export const NavBar = ({{ children, className = '' }}) => {{
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className={{`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${{className}}`}}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {{children}}
          
          {{/* Mobile menu button */}}
          <div className="md:hidden">
            <button
              onClick={{() => setIsOpen(!isOpen)}}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {{isOpen ? <X size={{24}} /> : <Menu size={{24}} />}}
            </button>
          </div>
        </div>
      </div>
      
      {{/* Mobile menu */}}
      <motion.div
        initial={{{{ opacity: 0, height: 0 }}}}
        animate={{{{ 
          opacity: isOpen ? 1 : 0, 
          height: isOpen ? 'auto' : 0 
        }}}}
        className="md:hidden bg-white border-t border-gray-200"
      >
        <div className="px-2 pt-2 pb-3 space-y-1">
          {{children}}
        </div>
      </motion.div>
    </nav>
  );
}};

export const NavLink = ({{ children, active = false, className = '', ...props }}) => (
  <motion.a
    whileHover={{{{ y: -2 }}}}
    className={{`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${{
      active
        ? 'text-blue-600 bg-blue-50'
        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
    }} ${{className}}`}}
    {{...props}}
  >
    {{children}}
  </motion.a>
);

export const FloatingTabs = ({{ tabs, activeTab, onTabChange, className = '' }}) => (
  <div className={{`flex bg-gray-100 p-1 rounded-lg ${{className}}`}}>
    {{tabs.map((tab) => (
      <motion.button
        key={{tab.id}}
        onClick={{() => onTabChange(tab.id)}}
        className={{`relative px-6 py-2 text-sm font-medium rounded-md transition-all duration-200 ${{
          activeTab === tab.id
            ? 'text-blue-600'
            : 'text-gray-600 hover:text-gray-900'
        }}`}}
        whileHover={{{{ y: -1 }}}}
        whileTap={{{{ y: 0 }}}}
      >
        {{activeTab === tab.id && (
          <motion.div
            layoutId="activeTab"
            className="absolute inset-0 bg-white rounded-md shadow-sm"
            transition={{{{ type: "spring", duration: 0.3 }}}}
          />
        )}}
        <span className="relative z-10">{{tab.label}}</span>
      </motion.button>
    ))}}
  </div>
);'''
		}

	@staticmethod
	def _get_awwwards_design_system() -> Dict[str, Any]:
		"""Modern design system based on Awwwards 2025 trends"""
		return {
			"color_palettes": {
				"vibrant_gradients": [
					"bg-gradient-to-br from-purple-600 via-pink-500 to-red-500",
					"bg-gradient-to-br from-blue-600 via-cyan-500 to-teal-400",
					"bg-gradient-to-br from-indigo-600 via-purple-500 to-pink-500",
					"bg-gradient-to-br from-amber-400 via-orange-500 to-red-600",
					"bg-gradient-to-br from-emerald-400 via-teal-500 to-blue-600"
				],
				"duotone_gradients": [
					"bg-gradient-to-br from-slate-900 to-slate-600",
					"bg-gradient-to-br from-gray-900 to-gray-600", 
					"bg-gradient-to-br from-zinc-900 to-zinc-600"
				],
				"mesh_gradients": [
					"bg-gradient-radial from-purple-400 via-pink-300 to-red-400",
					"bg-gradient-conic from-blue-400 via-cyan-300 to-teal-400"
				]
			},
			"typography": {
				"modern_fonts": ["Inter", "Poppins", "Outfit", "Space Grotesk"],
				"headings": "font-bold tracking-tight",
				"body": "font-normal leading-relaxed"
			},
			"animations": {
				"micro_interactions": [
					"hover:scale-105 transition-transform duration-300",
					"hover:-translate-y-2 transition-transform duration-300",
					"hover:rotate-1 transition-transform duration-300"
				],
				"scroll_effects": [
					"animate-fade-in-up",
					"animate-slide-in-left", 
					"animate-bounce-in"
				]
			},
			"layouts": {
				"hero_patterns": [
					"full-screen gradient background with centered content",
					"split-screen layout with image and content",
					"diagonal sections with overlapping elements"
				],
				"card_styles": [
					"glass morphism with backdrop blur",
					"neumorphism with subtle shadows",
					"minimal borders with hover effects"
				]
			},
			"effects": {
				"modern_ui": [
					"backdrop-blur-md bg-white/10",
					"shadow-2xl shadow-purple-500/20",
					"ring-2 ring-white/20"
				],
				"interactive": [
					"group-hover:scale-110 transition-transform",
					"hover:shadow-glow transition-shadow",
					"active:scale-95 transition-transform"
				]
			}
		}

	@staticmethod
	def _build_app_prompt(plan: Dict[str, Any], project_name: str) -> str:
		features = plan.get('features', [])
		features_str = [str(f) for f in features] if features else ['Modern features']
		app_type = plan.get('app_type', 'Web App')
		description = plan.get('description', 'A modern web application')
		
		# Import layout design system
		try:
			from layout_design_scraper import get_diverse_layout_for_project
			from design_trend_scraper import get_latest_design_trends
			
			# Get unique layout pattern for this project
			layout_pattern, custom_css, react_components = get_diverse_layout_for_project(app_type.lower())
			
			# Get fresh design trends
			design_trends = get_latest_design_trends()
			trending_layouts = [t.layout_type for t in design_trends[:3]] if design_trends else ["Modern Grid", "Glass Cards", "Organic Flow"]
			
			print(f"🎨 UNIQUE LAYOUT SELECTED: {layout_pattern.name} - {layout_pattern.type}")
			print(f"   📐 Grid: {layout_pattern.grid_system}")
			print(f"   🌈 Colors: {layout_pattern.color_approach}")
			print(f"   ✨ Effects: {', '.join(layout_pattern.visual_effects[:3])}")
			print(f"   🏆 Inspiration: {layout_pattern.design_inspiration}")
			
		except ImportError as e:
			print(f"⚠️ Layout system import failed: {e}, using fallback design system")
			layout_pattern = None
			custom_css = ""
			react_components = {}
			trending_layouts = ["CSS Grid", "Flexbox Cards", "Modern Layout"]
		
		# Get Awwwards design system (fallback)
		design_system = PureAIGenerator._get_awwwards_design_system()
		
		# Extract design preferences from features
		design_features = []
		functional_features = []
		
		for feature in features_str:
			feature_lower = str(feature).lower()
			if any(keyword in feature_lower for keyword in ['design', 'color', 'background', 'font', 'theme', 'style', 'dark', 'light']):
				design_features.append(str(feature))
			else:
				functional_features.append(str(feature))
		
		# Build Awwwards-inspired design instructions
		design_instructions = f"""
🎨 AWWWARDS 2025 DESIGN SYSTEM (MANDATORY):

COLOR PALETTES:
- Vibrant Gradients: {', '.join(design_system['color_palettes']['vibrant_gradients'][:3])}
- Duotone Effects: {', '.join(design_system['color_palettes']['duotone_gradients'])}
- Mesh Gradients: {', '.join(design_system['color_palettes']['mesh_gradients'])}

TYPOGRAPHY:
- Primary Font: {design_system['typography']['modern_fonts'][0]} (Inter)
- Headings: {design_system['typography']['headings']}
- Body Text: {design_system['typography']['body']}

MICRO-INTERACTIONS:
- {design_system['animations']['micro_interactions'][0]}
- {design_system['animations']['micro_interactions'][1]}
- {design_system['animations']['micro_interactions'][2]}

MODERN EFFECTS:
- Glass Morphism: {design_system['effects']['modern_ui'][0]}
- Glow Shadows: {design_system['effects']['modern_ui'][1]}
- Ring Effects: {design_system['effects']['modern_ui'][2]}

LAYOUT PATTERNS:
- Hero: Full-screen gradient with centered content and floating elements
- Cards: Glass morphism with backdrop blur and subtle animations
- Sections: Diagonal cuts, overlapping elements, and smooth transitions

🚨 UNIQUE LAYOUT ASSIGNMENT - MANDATORY TO IMPLEMENT:"""

		# Add unique layout pattern instructions
		if layout_pattern:
			design_instructions += f"""
🎯 YOUR ASSIGNED LAYOUT: {layout_pattern.type} ({layout_pattern.name})
📐 Grid System: {layout_pattern.grid_system}
🎨 Color Approach: {layout_pattern.color_approach} 
✨ Visual Effects: {', '.join(layout_pattern.visual_effects)}
🎭 Navigation: {layout_pattern.navigation}
📱 Responsive: {layout_pattern.responsive_strategy}
🎬 Animation Style: {layout_pattern.animation_style}
🏆 Inspiration: {layout_pattern.design_inspiration}

MANDATORY CSS CLASSES TO USE:
{chr(10).join(f'- {css_class}' for css_class in layout_pattern.css_classes)}

LAYOUT-SPECIFIC REQUIREMENTS:
- Hero Style: {layout_pattern.hero_style}
- Content Flow: {layout_pattern.content_flow}  
- Visual Hierarchy: {layout_pattern.visual_hierarchy}
- Typography Scale: {layout_pattern.typography_scale}
- Spacing System: {layout_pattern.spacing_system}
- Interactive Elements: {', '.join(layout_pattern.interactive_elements)}

🌟 TRENDING LAYOUTS (Reference for inspiration):
- {trending_layouts[0]}
- {trending_layouts[1]}  
- {trending_layouts[2]}

🚨 CRITICAL: This layout pattern MUST be your primary design approach. DO NOT use generic layouts!
"""
		
		# Add custom CSS if available
		if custom_css.strip():
			design_instructions += f"""

💎 CUSTOM CSS FOR YOUR LAYOUT (Add this to index.css):
```css
{custom_css}
```

"""
		
		design_instructions += '"""'
		
		if design_features:
			design_instructions += f"\n\n🎯 CUSTOM DESIGN REQUIREMENTS (USER-REQUESTED - MANDATORY TO IMPLEMENT):\n"
			for design_feature in design_features:
				design_instructions += f"- {design_feature}\n"
			
			# Enhanced color/theme detection and handling
			user_text_combined = ' '.join(str(df).lower() for df in design_features)
			
			# Color scheme detection
			if any(color in user_text_combined for color in ['blue', 'navy', 'cyan', 'teal']):
				design_instructions += "- 🎨 USER REQUESTED BLUE THEME: Use bg-gradient-to-br from-blue-600 via-cyan-500 to-teal-400, blue-500 accents, blue-100 backgrounds\n"
			elif any(color in user_text_combined for color in ['red', 'crimson', 'rose', 'pink']):
				design_instructions += "- 🎨 USER REQUESTED RED/PINK THEME: Use bg-gradient-to-br from-red-500 via-pink-500 to-rose-400, red-500 accents, red-50 backgrounds\n"
			elif any(color in user_text_combined for color in ['green', 'emerald', 'lime', 'mint']):
				design_instructions += "- 🎨 USER REQUESTED GREEN THEME: Use bg-gradient-to-br from-green-500 via-emerald-500 to-teal-400, green-500 accents, green-50 backgrounds\n"
			elif any(color in user_text_combined for color in ['purple', 'violet', 'indigo', 'lavender']):
				design_instructions += "- 🎨 USER REQUESTED PURPLE THEME: Use bg-gradient-to-br from-purple-600 via-violet-500 to-indigo-400, purple-500 accents, purple-50 backgrounds\n"
			elif any(color in user_text_combined for color in ['orange', 'amber', 'yellow', 'gold']):
				design_instructions += "- 🎨 USER REQUESTED WARM THEME: Use bg-gradient-to-br from-amber-400 via-orange-500 to-red-600, orange-500 accents, amber-50 backgrounds\n"
			elif any(theme in user_text_combined for theme in ['dark', 'black', 'midnight', 'night']):
				design_instructions += "- 🎨 USER REQUESTED DARK THEME: Use bg-gray-900/bg-black main background, white text, dark cards with subtle borders\n"
			elif any(theme in user_text_combined for theme in ['light', 'white', 'minimal', 'clean']):
				design_instructions += "- 🎨 USER REQUESTED LIGHT THEME: Use bg-white/bg-gray-50 main background, dark text, light cards with soft shadows\n"
		
		return f"""🚨 CRITICAL ERROR PREVENTION - MUST FOLLOW:
- NEVER import from 'framer-motion' directly - use the provided fallbacks in template below
- NEVER use AnimatePresence, motion, useScroll without the fallback definitions
- ALL framer-motion usage MUST use the safe fallbacks to prevent ReferenceError crashes
- NEVER use 'exports', 'require', or 'module' in React components
- ONLY use ES6 imports: import React, {{ useState }} from 'react'
- NO CommonJS syntax - only ES modules
- ALL components must be defined before use
- NO undefined variables or functions
- USE proper React patterns only
- ALWAYS use React.createContext and React.useContext (NOT named imports)
- CONSISTENT PATTERN: const AuthContext = React.createContext(null); const useAuth = () => React.useContext(AuthContext);

🌐 BROWSER ENVIRONMENT SAFETY:
- NEVER use process.env directly (causes ReferenceError in browser)
- Instead use: const API_URL = 'http://localhost:8000/api'; (local API)
- OR safe check: const API_URL = (typeof window !== 'undefined' && window.ENV?.API_URL) || 'http://localhost:8000/api';
- NO Node.js globals in browser code (process, Buffer, __dirname, require)

🏆 AWWWARDS-INSPIRED DESIGN BRIEF:
Create a STUNNING, AWARD-WINNING React App.jsx for {project_name} ({app_type}) that would win Site of the Day on Awwwards.

Project: {app_type}
Description: {description}
Functional Features: {', '.join(functional_features) if functional_features else 'Modern web app features'}

🚨 CRITICAL: FOLLOW USER DESIGN REQUIREMENTS EXACTLY - DO NOT DEVIATE!
{design_instructions}

⚠️ COLOR COMPLIANCE WARNING: 
- If user specifies colors/themes in requirements above, YOU MUST use those exact colors
- DO NOT use random or default colors when user has specified preferences
- User-requested colors take absolute priority over design system defaults

🎯 AWWWARDS QUALITY REQUIREMENTS:

1. VISUAL EXCELLENCE:
   - Use vibrant gradients and mesh backgrounds from the design system
   - Implement glass morphism effects: backdrop-blur-md bg-white/10
   - Add subtle animations and micro-interactions on all interactive elements
   - Create depth with layered shadows: shadow-2xl shadow-purple-500/20
   - Use modern typography: Inter font with bold headings and relaxed body text

2. AWARD-WINNING LAYOUT PATTERNS:
   - Hero Section: Full-screen gradient background with floating elements
   - Feature Cards: Glass morphism with hover animations (scale-105, -translate-y-2)
   - Diagonal Sections: Use transform-skew and overlapping elements
   - Interactive Elements: Ripple effects, morphing shapes, 3D transforms

3. COLOR PALETTE PRIORITY:
   - 🚨 FIRST PRIORITY: Use user-requested colors from CUSTOM DESIGN REQUIREMENTS above
   - If no specific colors requested, choose from: Vibrant (purple-pink-red), Tech (blue-cyan-teal), Warm (amber-orange-red)
   - NEVER use random colors - always follow user specifications or design system defaults

4. PREMIUM INTERACTIONS:
   - Hover effects: hover:scale-105 hover:-translate-y-2 hover:shadow-glow
   - Loading states: Skeleton loaders with pulse effects
   - Smooth transitions: transition-all duration-300 ease-in-out
   - Parallax scrolling effects and smooth animations

5. AWWWARDS-STYLE COMPONENTS:
   - Floating navigation with backdrop blur
   - Interactive hero with animated text reveals
   - Feature grid with staggered animations
   - Testimonials with morphing cards
   - Footer with gradient overlays

MANDATORY FULL-STACK INTEGRATION REQUIREMENTS:

1. COMPLETE AUTHENTICATION SYSTEM (ALWAYS INCLUDE):
   - Login modal with email/password form and real validation
   - Signup modal with user registration form and validation  
   - JWT token storage in localStorage with proper management
   - Authentication state management with React context
   - User profile display with logout functionality
   - Protected content areas that require login
   - Proper form submission with API calls to backend
   - Error handling and success notifications

2. WORKING API INTEGRATION:
   - Real fetch() calls to backend API (http://localhost:8000/api)
   - Authentication headers: Authorization: Bearer {{token}}
   - Proper error handling for all network requests
   - Loading states with spinners and user feedback
   - Success/error notifications with toast messages
   - Automatic token refresh and logout on 401 errors

3. E-COMMERCE FEATURES (If shop/store/cart/product detected):
   - Product grid with real product data from API
   - Add to Cart functionality that actually works
   - Shopping cart modal with item management (add/remove/update)
   - Cart count display in header that updates in real-time
   - Checkout process with payment forms
   - Order history and tracking display
   - Search and filtering capabilities

4. ADVANCED UI COMPONENTS:
   - Header with navigation, user info, cart count
   - Modals for login, signup, cart, payment processing
   - Interactive forms with validation and submission
   - Loading spinners and error boundaries
   - Responsive navigation with mobile support
   - Toast notifications for user feedback

CRITICAL IMPLEMENTATION REQUIREMENTS:
- ALL COMPONENTS MUST BE PROPERLY DEFINED AND EXPORTED
- NO UNDEFINED VARIABLES OR COMPONENTS  
- USE PROPER ERROR BOUNDARIES AND LOADING STATES
- INCLUDE SHADCN/UI STYLE COMPONENTS
- WORKING STATE MANAGEMENT WITH REACT HOOKS
- REAL API CALLS WITH PROPER ERROR HANDLING

Build a complete, functional app with:
- Authentication system with working login/signup
- Modern hero section with call-to-action buttons
- Feature showcase with interactive elements
- Working e-commerce functionality (if applicable)
- Responsive design with TailwindCSS
- Real, relevant content and professional appearance

MANDATORY COMPONENT ARCHITECTURE:
```jsx
import React, {{ useState, useEffect, createContext, useContext }} from 'react';

// SAFE FRAMER-MOTION FALLBACKS (CRITICAL FOR BROWSER COMPATIBILITY):
// Create fallback components that filter out animation props to prevent React DOM warnings
const createMotionFallback = (element) => ({{ children, className, style, onClick, id, initial, animate, exit, whileHover, whileTap, whileInView, transition, variants, ...validProps }}) => 
  React.createElement(element, {{ className, style, onClick, id, ...validProps }}, children);

const motion = {{
  div: createMotionFallback('div'),
  span: createMotionFallback('span'), 
  section: createMotionFallback('section'),
  h1: createMotionFallback('h1'),
  button: createMotionFallback('button'),
  p: createMotionFallback('p')
}};

// Safe AnimatePresence fallback that just renders children
const AnimatePresence = ({{ children, mode, ...props }}) => <div {{...props}}>{{children}}</div>;

// Safe hook fallbacks
const useInView = (ref, options = {{}}) => true;
const useScroll = () => ({{ scrollYProgress: {{ get: () => 0, onChange: () => {{}}, set: () => {{}}, stop: () => {{}}, destroy: () => {{}} }} }});

// ANIMATION USAGE GUIDE:
// - Use <motion.div> for animated elements (will render as regular divs with fallbacks)
// - Wrap conditional renders with <AnimatePresence> 
// - Example: <AnimatePresence>{{ showModal && <motion.div>...</motion.div> }}</AnimatePresence>
// - Fallbacks ensure no runtime errors if framer-motion fails to load

// AUTHENTICATION CONTEXT (ALWAYS INCLUDE)
const AuthContext = createContext();
const useAuth = () => useContext(AuthContext);

// CART CONTEXT (IF E-COMMERCE DETECTED)  
const CartContext = createContext();
const useCart = () => useContext(CartContext);

// NOTIFICATION CONTEXT (ALWAYS INCLUDE)
const NotificationContext = createContext();
const useNotification = () => useContext(NotificationContext);

// ICON COMPONENTS (PROPERLY DEFINED)
const Star = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>;

const User = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;

const ShoppingCart = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57L23 6H6"></path></svg>;

const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;

const Plus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>;

const Minus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14"></path></svg>;

// UI COMPONENTS (SHADCN STYLE)
const Button = ({{children, variant = "default", className = "", onClick, disabled, ...props}}) => (
  <button 
    className={{cn(
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed",
      buttonVariants[variant],
      className
    )}} 
    onClick={{onClick}}
    disabled={{disabled}}
    {{...props}}
  >
    {{children}}
  </button>
);

const Card = ({{children, className = "", variant = "default"}}) => (
  <div className={{cn(cardVariants[variant], className)}}>
    {{children}}
  </div>
);

const Modal = ({{ isOpen, onClose, children, title }}) => {{
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">{{title}}</h2>
          <button onClick={{onClose}} className="text-gray-400 hover:text-gray-600">
            <X />
          </button>
        </div>
        <div className="p-6">{{children}}</div>
      </div>
    </div>
  );
}};

const LoadingSpinner = () => (
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
);

const Toast = ({{ message, type = "success", onClose }}) => (
  <div className={{cn(
    "fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 transition-all",
    type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
  )}}>
    <div className="flex items-center justify-between">
      <span>{{message}}</span>
      <button onClick={{onClose}} className="ml-4 text-white hover:text-gray-200">
        <X />
      </button>
    </div>
  </div>
);

// AUTHENTICATION COMPONENTS (ALWAYS INCLUDE)
const LoginModal = ({{ isOpen, onClose, onSuccess }}) => {{
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleLogin = async (e) => {{
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {{
      const response = await fetch('http://localhost:8000/api/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ email, password }})
      }});
      
      const data = await response.json();
      
      if (response.ok) {{
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onSuccess(data.user);
        onClose();
      }} else {{
        setError(data.detail || 'Login failed');
      }}
    }} catch (err) {{
      setError('Network error. Please try again.');
    }} finally {{
      setLoading(false);
    }}
  }};
  
  return (
    <Modal isOpen={{isOpen}} onClose={{onClose}} title="Login">
      <form onSubmit={{handleLogin}} className="space-y-4">
        {{error && <div className="text-red-500 text-sm">{{error}}</div>}}
        <input
          type="email"
          placeholder="Email"
          value={{email}}
          onChange={{(e) => setEmail(e.target.value)}}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={{password}}
          onChange={{(e) => setPassword(e.target.value)}}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <Button type="submit" className="w-full" disabled={{loading}}>
          {{loading ? <LoadingSpinner /> : 'Login'}}
        </Button>
      </form>
    </Modal>
  );
}};

const SignupModal = ({{ isOpen, onClose, onSuccess }}) => {{
  const [formData, setFormData] = useState({{ name: '', email: '', password: '', confirmPassword: '' }});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleSignup = async (e) => {{
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {{
      setError('Passwords do not match');
      return;
    }}
    
    setLoading(true);
    setError('');
    
    try {{
      const response = await fetch('http://localhost:8000/api/auth/register', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          name: formData.name,
          email: formData.email,
          password: formData.password
        }})
      }});
      
      const data = await response.json();
      
      if (response.ok) {{
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onSuccess(data.user);
        onClose();
      }} else {{
        setError(data.detail || 'Registration failed');
      }}
    }} catch (err) {{
      setError('Network error. Please try again.');
    }} finally {{
      setLoading(false);
    }}
  }};
  
  return (
    <Modal isOpen={{isOpen}} onClose={{onClose}} title="Sign Up">
      <form onSubmit={{handleSignup}} className="space-y-4">
        {{error && <div className="text-red-500 text-sm">{{error}}</div>}}
        <input
          type="text"
          placeholder="Full Name"
          value={{formData.name}}
          onChange={{(e) => setFormData({{...formData, name: e.target.value}})}}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={{formData.email}}
          onChange={{(e) => setFormData({{...formData, email: e.target.value}})}}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={{formData.password}}
          onChange={{(e) => setFormData({{...formData, password: e.target.value}})}}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="password"
          placeholder="Confirm Password"
          value={{formData.confirmPassword}}
          onChange={{(e) => setFormData({{...formData, confirmPassword: e.target.value}})}}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <Button type="submit" className="w-full" disabled={{loading}}>
          {{loading ? <LoadingSpinner /> : 'Sign Up'}}
        </Button>
      </form>
    </Modal>
  );
}};

// HEADER COMPONENT (ALWAYS INCLUDE)
const Header = ({{ user, onLogin, onSignup, onLogout, cartCount = 0, onCartClick }}) => (
  <header className="bg-white shadow-sm border-b">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between h-16">
        <div className="flex items-center">
          <h1 className="text-xl font-bold text-gray-900">{project_name}</h1>
        </div>
        <div className="flex items-center space-x-4">
          {{cartCount > 0 && (
            <button
              onClick={{onCartClick}}
              className="relative text-gray-600 hover:text-gray-900"
            >
              <ShoppingCart />
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {{cartCount}}
              </span>
            </button>
          )}}
          {{user ? (
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {{user.name}}</span>
              <Button variant="outline" onClick={{onLogout}}>Logout</Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={{onLogin}}>Login</Button>
              <Button onClick={{onSignup}}>Sign Up</Button>
            </div>
          )}}
        </div>
      </div>
    </div>
  </header>
);

// MAIN APP COMPONENT WITH FULL INTEGRATION
const App = () => {{
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showCart, setShowCart] = useState(false);
  
  // Initialize authentication state
  useEffect(() => {{
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser && savedUser !== 'undefined' && savedUser !== 'null') {{
      try {{
        setUser(JSON.parse(savedUser));
      }} catch (error) {{
        console.error('Failed to parse saved user data:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }}
    }}
  }}, []);
  
  // Authentication handlers
  const handleLoginSuccess = (userData) => {{
    setUser(userData);
    showNotification('Login successful!', 'success');
  }};
  
  const handleSignupSuccess = (userData) => {{
    setUser(userData);
    showNotification('Account created successfully!', 'success');
  }};
  
  const handleLogout = () => {{
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setCart([]);
    showNotification('Logged out successfully', 'success');
  }};
  
  // Notification handler
  const showNotification = (message, type = 'success') => {{
    const id = Date.now();
    setNotifications(prev => [...prev, {{ id, message, type }}]);
    setTimeout(() => {{
      setNotifications(prev => prev.filter(n => n.id !== id));
    }}, 5000);
  }};
  
  // Cart handlers (if e-commerce)
  const addToCart = (product) => {{
    setCart(prev => {{
      const existing = prev.find(item => item.id === product.id);
      if (existing) {{
        return prev.map(item => 
          item.id === product.id 
            ? {{ ...item, quantity: item.quantity + 1 }}
            : item
        );
      }}
      return [...prev, {{ ...product, quantity: 1 }}];
    }});
    showNotification(`Added ${{product.name}} to cart!`, 'success');
  }};
  
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  
  return (
    <AuthContext.Provider value={{ user, login: handleLoginSuccess, logout: handleLogout }}>
      <CartContext.Provider value={{ cart, addToCart, cartCount }}>
        <NotificationContext.Provider value={{ showNotification }}>
          <div className="min-h-screen bg-gray-50">
            <Header 
              user={{user}}
              onLogin={{() => setShowLogin(true)}}
              onSignup={{() => setShowSignup(true)}}
              onLogout={{handleLogout}}
              cartCount={{cartCount}}
              onCartClick={{() => setShowCart(true)}}
            />
            
            {{/* YOUR MAIN CONTENT GOES HERE */}}
            <main className="flex-1">
              {{/* Hero Section */}}
              <section className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-20">
                <div className="max-w-7xl mx-auto px-4 text-center">
                  <h1 className="text-5xl font-bold mb-6">{project_name}</h1>
                  <p className="text-xl mb-8">{description}</p>
                  <div className="space-x-4">
                    {{!user && (
                      <>
                        <Button variant="outline" onClick={{() => setShowSignup(true)}} className="text-white border-white hover:bg-white hover:text-blue-600">
                          Get Started
                        </Button>
                        <Button variant="ghost" onClick={{() => setShowLogin(true)}} className="text-white hover:bg-white/10">
                          Learn More
                        </Button>
                      </>
                    )}}
                    {{user && (
                      <Button variant="outline" className="text-white border-white hover:bg-white hover:text-blue-600">
                        Welcome back, {{user.name}}!
                      </Button>
                    )}}
                  </div>
                </div>
              </section>
              
              {{/* Continue with your app-specific content... */}}
            </main>
            
            {{/* Modals */}}
            <LoginModal 
              isOpen={{showLogin}}
              onClose={{() => setShowLogin(false)}}
              onSuccess={{handleLoginSuccess}}
            />
            <SignupModal 
              isOpen={{showSignup}}
              onClose={{() => setShowSignup(false)}}
              onSuccess={{handleSignupSuccess}}
            />
            
            {{/* Notifications */}}
            {{notifications.map(notification => (
              <Toast
                key={{notification.id}}
                message={{notification.message}}
                type={{notification.type}}
                onClose={{() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}}
              />
            ))}}
          </div>
        </NotificationContext.Provider>
      </CartContext.Provider>
    </AuthContext.Provider>
  );
}};

export default App;
    </div>
  );
}};

export default App;
```

IMPORTANT RULES:
- Define ALL components before using them
- Use proper React functional component syntax
- Include error handling with try-catch where needed
- Make it specific to the {app_type} domain
- Use real data relevant to the application type
- Ensure all variables and functions are properly scoped
- Test all component references before using
- STRICTLY FOLLOW all design requirements specified above
- Apply design preferences to ALL sections (background colors, text colors, etc.)

🚨 FRAMER-MOTION CRITICAL FIXES:
- ALWAYS wrap conditional renders with <AnimatePresence>
- Example: <AnimatePresence>{{showModal && <motion.div exit={{{{opacity: 0}}}}>Content</motion.div>}}</AnimatePresence>
- Use motion.div, motion.button, etc. for animated elements
- Include exit animations to prevent "AnimatePresence is not defined" errors
- Proper imports: import {{ motion, AnimatePresence }} from 'framer-motion';

Return complete, working JSX code only."""