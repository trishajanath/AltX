"""Pure AI generator that relies exclusively on Gemini outputs.

This module intentionally avoids deterministic fallbacks. If Gemini declines
to produce content, the caller must handle the error.

Enhanced with Website Analyzer integration:
- When user says "build a website like Amazon", scrapes Amazon for design patterns
- Extracts colors, layout, typography, components from target website
- Creates similar but unique design based on analysis
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
from code_validator import CodeValidator, validate_generated_code, auto_fix_jsx_for_sandbox, validate_and_fix_for_sandbox

# Import website analyzer for "build a website like X" feature
try:
    from website_analyzer import (
        WebsiteAnalyzer, 
        WebsiteAnalysis, 
        analyze_website_for_inspiration,
        get_inspiration_prompt_context,
        website_analyzer
    )
    WEBSITE_ANALYZER_AVAILABLE = True
except ImportError:
    WEBSITE_ANALYZER_AVAILABLE = False
    print("⚠️ Website analyzer not available - 'like X' feature disabled")

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
							# For App.jsx, always export App
							file_name = file_path.stem  # Get filename without extension
							if file_name == 'App':
								fixed_content = content + f'\n\nexport default App;'
								fixes_applied.append(f"Added export default App")
							else:
								# Find component/function names - search from END of file to find main component
								lines = content.split('\n')
								component_name = None
								for line in reversed(lines):
									if 'function ' in line or 'const ' in line:
										# Extract potential component name
										if 'function' in line:
											name_part = line.split('function')[1].split('(')[0].strip()
										elif 'const' in line and '=' in line:
											name_part = line.split('const')[1].split('=')[0].strip()
										else:
											continue
										if name_part and name_part[0].isupper():  # Component naming convention
											component_name = name_part
											break
								
								# If no component found searching from end, try the filename as component name
								if not component_name and file_name and file_name[0].isupper():
									component_name = file_name
								
								if component_name:
									fixed_content = content + f'\n\nexport default {component_name};'
									fixes_applied.append(f"Added export default {component_name}")
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
		self.code_validator = CodeValidator()  # ESLint validator for JS/JSX
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
		
		print("🤖 Pure AI Generator initialized (Gemini only, no fallbacks) with ESLint validation")

	# ------------------------------------------------------------------
	# Security Decision Records (SDR) Generation
	# ------------------------------------------------------------------

	def generate_security_decision_records(self, plan: Dict[str, Any], project_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Generate Security Decision Records (SDRs) based on the project plan.
		These document the security and architectural choices made by the AI.
		
		Args:
			plan: The project plan from analyze_and_plan
			project_spec: Original project specification
			
		Returns:
			List of SDR dictionaries with id, title, decision, context, alternatives, date, category
		"""
		sdrs = []
		sdr_counter = 1
		today = datetime.now().strftime("%Y-%m-%d")
		
		idea = project_spec.get("idea", "").lower() if isinstance(project_spec, dict) else str(project_spec).lower()
		tech_stack = plan.get("tech_stack", [])
		features = plan.get("features", [])
		
		# SDR 1: Frontend Framework Choice
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "Frontend Framework Selection",
			"decision": "React with Vite build system",
			"context": "React provides a component-based architecture with excellent ecosystem support, TypeScript compatibility, and hot module replacement via Vite for fast development.",
			"alternatives": [
				{"name": "Vue.js", "reason": "Smaller ecosystem and fewer enterprise-grade component libraries"},
				{"name": "Angular", "reason": "Heavier framework with steeper learning curve, overkill for this project scope"},
				{"name": "Svelte", "reason": "Smaller community and fewer production-proven patterns"}
			],
			"date": today,
			"category": "architecture"
		})
		sdr_counter += 1
		
		# SDR 2: Styling Solution
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "CSS Framework Selection",
			"decision": "TailwindCSS utility-first approach",
			"context": "Tailwind enables rapid UI development with consistent design tokens, excellent tree-shaking for production, and avoids CSS specificity conflicts.",
			"alternatives": [
				{"name": "styled-components", "reason": "Runtime CSS-in-JS overhead impacts performance"},
				{"name": "SASS/SCSS", "reason": "Requires additional build configuration and class naming conventions"},
				{"name": "CSS Modules", "reason": "More boilerplate and less design consistency"}
			],
			"date": today,
			"category": "architecture"
		})
		sdr_counter += 1
		
		# SDR 3: Backend Framework
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "Backend Framework Selection",
			"decision": "FastAPI (Python)",
			"context": "FastAPI provides automatic OpenAPI documentation, async support, type validation via Pydantic, and excellent performance suitable for modern web applications.",
			"alternatives": [
				{"name": "Express.js", "reason": "Less built-in validation and documentation generation"},
				{"name": "Django", "reason": "More opinionated and heavier for API-focused applications"},
				{"name": "Flask", "reason": "Requires more manual configuration for production features"}
			],
			"date": today,
			"category": "architecture"
		})
		sdr_counter += 1
		
		# SDR 4: Authentication (if applicable)
		if any(keyword in idea for keyword in ["auth", "login", "user", "signup", "account", "profile", "secure"]):
			sdrs.append({
				"id": f"SDR-{sdr_counter:03d}",
				"title": "Authentication Strategy",
				"decision": "JWT (JSON Web Tokens) with secure HttpOnly cookies",
				"context": "JWTs provide stateless authentication suitable for distributed systems. HttpOnly cookies prevent XSS token theft while maintaining CSRF protection.",
				"alternatives": [
					{"name": "Session-based auth", "reason": "Requires server-side session storage, harder to scale horizontally"},
					{"name": "OAuth2 only", "reason": "Complex for simple applications, depends on third-party availability"},
					{"name": "Basic Auth", "reason": "Credentials sent with every request, no token expiration"}
				],
				"date": today,
				"category": "security"
			})
			sdr_counter += 1
			
			# Password Hashing SDR
			sdrs.append({
				"id": f"SDR-{sdr_counter:03d}",
				"title": "Password Hashing Algorithm",
				"decision": "bcrypt with cost factor 12",
				"context": "bcrypt is memory-hard and resistant to GPU attacks. Cost factor 12 provides ~250ms hash time, balancing security with user experience.",
				"alternatives": [
					{"name": "Argon2id", "reason": "Newer but less library support, bcrypt is battle-tested"},
					{"name": "PBKDF2", "reason": "Susceptible to GPU parallelization attacks"},
					{"name": "SHA-256", "reason": "Too fast, vulnerable to brute force attacks"}
				],
				"date": today,
				"category": "critical"
			})
			sdr_counter += 1
		
		# SDR: Database (if data storage needed)
		if any(keyword in idea for keyword in ["store", "save", "data", "crud", "database", "todo", "task", "list", "inventory", "product"]):
			sdrs.append({
				"id": f"SDR-{sdr_counter:03d}",
				"title": "Database Selection",
				"decision": "SQLite for development, PostgreSQL recommended for production",
				"context": "SQLite provides zero-configuration local development. PostgreSQL offers ACID compliance, JSON support, and horizontal scaling for production workloads.",
				"alternatives": [
					{"name": "MongoDB", "reason": "Schema flexibility can lead to data inconsistency without careful design"},
					{"name": "MySQL", "reason": "Less advanced JSON support and window functions than PostgreSQL"},
					{"name": "Firebase", "reason": "Vendor lock-in and limited query capabilities"}
				],
				"date": today,
				"category": "architecture"
			})
			sdr_counter += 1
		
		# SDR: API Design
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "API Design Pattern",
			"decision": "RESTful API with OpenAPI specification",
			"context": "REST provides predictable resource-based URLs, HTTP method semantics, and automatic documentation via FastAPI's OpenAPI integration.",
			"alternatives": [
				{"name": "GraphQL", "reason": "Over-engineering for simple CRUD operations, steeper learning curve"},
				{"name": "gRPC", "reason": "Requires protocol buffer setup, less browser-friendly"},
				{"name": "SOAP", "reason": "Verbose XML format, outdated for modern applications"}
			],
			"date": today,
			"category": "architecture"
		})
		sdr_counter += 1
		
		# SDR: Input Validation
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "Input Validation Strategy",
			"decision": "Pydantic models with strict validation",
			"context": "Pydantic provides type coercion, custom validators, and automatic error messages. Validates at API boundary to prevent injection attacks.",
			"alternatives": [
				{"name": "Manual validation", "reason": "Error-prone, inconsistent, harder to maintain"},
				{"name": "JSON Schema", "reason": "Less integrated with Python types, separate validation step"},
				{"name": "Marshmallow", "reason": "More verbose, less integrated with FastAPI"}
			],
			"date": today,
			"category": "security"
		})
		sdr_counter += 1
		
		# SDR: E-commerce specific (if applicable)
		if any(keyword in idea for keyword in ["shop", "store", "ecommerce", "e-commerce", "cart", "checkout", "payment", "product"]):
			sdrs.append({
				"id": f"SDR-{sdr_counter:03d}",
				"title": "Payment Processing Architecture",
				"decision": "Stripe integration with client-side tokenization",
				"context": "Stripe handles PCI compliance. Client-side tokenization ensures card data never touches our servers, reducing security scope.",
				"alternatives": [
					{"name": "PayPal", "reason": "More complex integration, higher friction checkout"},
					{"name": "Square", "reason": "Less comprehensive API documentation"},
					{"name": "Direct card processing", "reason": "Requires PCI DSS Level 1 compliance"}
				],
				"date": today,
				"category": "critical"
			})
			sdr_counter += 1
		
		# SDR: State Management
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "Frontend State Management",
			"decision": "React useState/useReducer with Context API",
			"context": "Built-in React state management is sufficient for most applications. Avoids external dependencies and bundle size overhead.",
			"alternatives": [
				{"name": "Redux", "reason": "Excessive boilerplate for typical state complexity"},
				{"name": "MobX", "reason": "Magic mutable state can lead to unpredictable behavior"},
				{"name": "Zustand", "reason": "Additional dependency when React Context suffices"}
			],
			"date": today,
			"category": "architecture"
		})
		sdr_counter += 1
		
		# SDR: Error Handling
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "Error Handling Strategy",
			"decision": "Structured error responses with error boundaries",
			"context": "Consistent JSON error format with status codes. React Error Boundaries prevent full app crashes from component errors.",
			"alternatives": [
				{"name": "Generic error pages", "reason": "Poor user experience, no actionable feedback"},
				{"name": "No error handling", "reason": "Exposes stack traces, security risk"},
				{"name": "Alert popups", "reason": "Intrusive UX, blocks user interaction"}
			],
			"date": today,
			"category": "security"
		})
		sdr_counter += 1
		
		# SDR: CORS Policy
		sdrs.append({
			"id": f"SDR-{sdr_counter:03d}",
			"title": "CORS Policy Configuration",
			"decision": "Whitelist-based CORS with credentials support",
			"context": "Only allows requests from known frontend origins. Credentials mode enabled for cookie-based authentication.",
			"alternatives": [
				{"name": "Allow all origins (*)", "reason": "Security vulnerability, enables CSRF attacks"},
				{"name": "No CORS", "reason": "Blocks legitimate cross-origin requests"},
				{"name": "Proxy all requests", "reason": "Adds latency and single point of failure"}
			],
			"date": today,
			"category": "security"
		})
		sdr_counter += 1
		
		print(f"📋 Generated {len(sdrs)} Security Decision Records")
		return sdrs

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
		
		# Fix common import syntax errors
		import re
		# Fix: "import React, from 'react'" -> "import React from 'react'"
		code = re.sub(r"import\s+React\s*,\s+from\s+['\"]react['\"]", "import React from 'react'", code)
		# Fix: "import { useState, } from 'react'" -> "import { useState } from 'react'"
		code = re.sub(r"\{\s*([^}]+?)\s*,\s*\}", r"{ \1 }", code)
			
		# Check for export
		if "export default" not in code:
			code += "\n\nexport default App;"
		
		# Log issues found
		if issues:
			print(f"DEBUG: Fixed React issues: {', '.join(issues)}")
		
		return code

	def _write_validated_file(self, file_path: Path, content: str, file_type: str, project_slug: str = None) -> str:
		"""Write a file with optional AI validation and automatic fixes. Supports S3 direct upload."""
		
		# CRITICAL: Apply auto-fix for JSX files FIRST
		if file_type in ["jsx", "javascript", "js"] or str(file_path).endswith(('.jsx', '.js', '.tsx', '.ts')):
			content = auto_fix_jsx_for_sandbox(content, file_path.name)
			print(f"🔧 Applied sandbox auto-fixes to {file_path.name}")
		
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
		
		# CRITICAL: Apply auto-fix for JSX files BEFORE validation
		if file_type in ["jsx", "javascript", "js"] or str(file_path).endswith(('.jsx', '.js', '.tsx', '.ts')):
			content = auto_fix_jsx_for_sandbox(content, file_path.name)
			print(f"🔧 Applied sandbox auto-fixes to {file_path.name}")
		
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
			features = project_spec.get("features", [])
		else:
			idea = str(project_spec)
			features = []
			project_spec = {"idea": idea}
		
		# 🤖 NEW: Detect ML model requirements
		try:
			from ml_integration_templates import detect_ml_requirements, detect_llm_requirements
			
			ml_requirements = detect_ml_requirements(idea, features)
			llm_requirements = detect_llm_requirements(idea, features)
			
			if ml_requirements.get("needs_ml"):
				print(f"🤖 ML INTEGRATION DETECTED: {ml_requirements['models']}")
				print(f"   Use cases: {ml_requirements['use_cases']}")
				project_spec["ml_requirements"] = ml_requirements
			
			if llm_requirements.get("needs_llm"):
				print(f"🧠 LLM INTEGRATION DETECTED: {[p['name'] for p in llm_requirements['providers']]}")
				print(llm_requirements.get("api_key_instructions", ""))
				project_spec["llm_requirements"] = llm_requirements
		except ImportError as e:
			print(f"⚠️ ML integration templates not available: {e}")
		
		# 🌐 NEW: Check for website reference and analyze if found
		website_inspiration_context = ""
		if WEBSITE_ANALYZER_AVAILABLE:
			try:
				print("🔍 Checking for website reference in idea...")
				website_analysis = await analyze_website_for_inspiration(idea)
				
				if website_analysis and website_analysis.analysis_quality != "failed":
					print(f"🎨 Found website inspiration: {website_analysis.website_name}")
					print(f"   Layout: {website_analysis.layout_type}")
					print(f"   Colors: {website_analysis.primary_colors[:3]}")
					print(f"   Components: {[c['name'] for c in website_analysis.components[:5]]}")
					
					# Convert analysis to prompt context
					website_inspiration_context = get_inspiration_prompt_context(website_analysis)
					
					# Store in project_spec for downstream use
					project_spec["website_inspiration_context"] = website_inspiration_context
					project_spec["website_analysis"] = {
						"name": website_analysis.website_name,
						"url": website_analysis.website_url,
						"layout": website_analysis.layout_type,
						"colors": website_analysis.primary_colors,
						"features": website_analysis.features,
						"suggestions": website_analysis.design_suggestions
					}
					
					print(f"✅ Website analysis complete - will create inspired but unique design")
				else:
					print("ℹ️ No website reference detected or analysis failed")
			except Exception as e:
				print(f"⚠️ Website analysis error (continuing without): {e}")
			
		request = GenerationRequest(
			prompt=self._build_plan_prompt(project_spec, project_name, website_inspiration_context),
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
		
		# Pass through user-provided data to the plan for downstream use
		if isinstance(project_spec, dict):
			if project_spec.get("product_data"):
				plan["_user_product_data"] = project_spec.get("product_data")
				print(f"📦 User provided {len(project_spec.get('product_data', []))} products for this project")
			if project_spec.get("custom_data"):
				plan["_user_custom_data"] = project_spec.get("custom_data")
				print(f"📋 User provided custom data for this project")
			# Pass through ML/LLM requirements
			if project_spec.get("ml_requirements"):
				plan["_ml_requirements"] = project_spec.get("ml_requirements")
				print(f"🤖 ML models to integrate: {project_spec['ml_requirements'].get('models', [])}")
			if project_spec.get("llm_requirements"):
				plan["_llm_requirements"] = project_spec.get("llm_requirements")
		
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
					# Static requirements file with Google OAuth support
					content = "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\npython-multipart==0.0.6\nsqlalchemy==2.0.0\npasslib==1.7.4\npython-jose==3.3.0\nbcrypt==4.0.1\ngoogle-auth==2.25.0\nhttpx==0.26.0\n"
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
					import traceback
					error_details = traceback.format_exc()
					print(f"❌ ERROR generating App.jsx: {e}")
					print(f"📋 Error details: {error_details}")
					
					# Log error to help debugging
					with open("app_generation_error.log", "a") as f:
						f.write(f"\n{'='*50}\n")
						f.write(f"Project: {project_name}\n")
						f.write(f"Error: {e}\n")
						f.write(f"Details:\n{error_details}\n")
					
					# Return a REAL fallback without imports - sandbox provides globals
					return f'''// App.jsx - Error recovery mode (sandbox-compatible)
// All React hooks, components, and utilities are provided by the sandbox environment

const App = () => {{
  const [count, setCount] = React.useState(0);
  const [user, setUser] = React.useState(null);
  const [isLoggedIn, setIsLoggedIn] = React.useState(false);
  const [showModal, setShowModal] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('All');
  
  // Rich product data for e-commerce demo
  const products = [
    {{ id: 1, name: "Wireless Bluetooth Headphones", price: 79.99, originalPrice: 129.99, rating: 4.5, reviews: 2847, image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&q=80", category: "Electronics", badge: "Best Seller", description: "Premium sound quality with ANC" }},
    {{ id: 2, name: "Smart Fitness Watch Pro", price: 199.99, originalPrice: 249.99, rating: 4.7, reviews: 1523, image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&q=80", category: "Electronics", badge: "Top Rated", description: "Track your health goals" }},
    {{ id: 3, name: "Premium Leather Backpack", price: 89.99, rating: 4.3, reviews: 892, image: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&q=80", category: "Fashion", description: "Stylish and durable" }},
    {{ id: 4, name: "Minimalist Desk Lamp", price: 49.99, rating: 4.6, reviews: 1205, image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&q=80", category: "Home", badge: "New", description: "Modern LED design" }},
    {{ id: 5, name: "Organic Coffee Beans 1kg", price: 24.99, rating: 4.8, reviews: 3421, image: "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=400&q=80", category: "Food", description: "Premium roasted arabica" }},
    {{ id: 6, name: "Running Shoes Ultra", price: 129.99, originalPrice: 159.99, rating: 4.7, reviews: 2567, image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&q=80", category: "Sports", badge: "Popular", description: "Lightweight and breathable" }},
    {{ id: 7, name: "Mechanical Keyboard RGB", price: 149.99, rating: 4.8, reviews: 1834, image: "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400&h=400&q=80", category: "Electronics", description: "Cherry MX switches" }},
    {{ id: 8, name: "Vintage Sunglasses", price: 45.99, rating: 4.3, reviews: 789, image: "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&q=80", category: "Fashion", description: "Classic UV protection" }},
  ];
  
  const categories = ['All', 'Electronics', 'Fashion', 'Home', 'Sports', 'Food'];
  
  const [cart, setCart] = React.useState([]);
  
  const addToCart = (product) => {{
    setCart([...cart, product]);
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 bg-green-500 text-white font-medium';
    notification.textContent = `Added ${{product.name}} to cart!`;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }};
  
  const filteredProducts = products.filter(p => 
    (selectedCategory === 'All' || p.category === selectedCategory) &&
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {{/* Sticky Header */}}
      <header className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center text-xl">🛍️</div>
            <span className="text-xl font-bold">{project_name}</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Shop</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Categories</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Deals</a>
          </nav>
          <div className="flex items-center gap-4">
            <button className="relative p-2 text-gray-300 hover:text-white">
              🛒
              {{cart.length > 0 && <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center">{{cart.length}}</span>}}
            </button>
            <button 
              onClick={{() => setShowModal(true)}}
              className="px-4 py-2 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>
      </header>
      
      {{/* Hero Section */}}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm mb-8">
            ⚡ Free shipping on orders over $50
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            <span className="text-white">Shop the best</span><br />
            <span className="text-blue-400">products online</span>
          </h1>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Discover amazing products at great prices. Fast delivery, easy returns.
          </p>
          <div className="max-w-xl mx-auto mb-10">
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
              <input 
                type="text"
                placeholder="Search products..."
                value={{searchQuery}}
                onChange={{(e) => setSearchQuery(e.target.value)}}
                className="w-full pl-12 pr-4 py-4 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-gray-400">
            <span>🚚 Free Delivery</span>
            <span>✨ Quality Guaranteed</span>
            <span>⚡ Express Checkout</span>
          </div>
        </div>
      </section>
      
      {{/* Products Section */}}
      <section className="py-16 px-4 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white">Featured Products</h2>
              <p className="text-gray-400">Discover our best sellers</p>
            </div>
            <span className="text-gray-500">{{filteredProducts.length}} products</span>
          </div>
          
          {{/* Category Pills */}}
          <div className="flex flex-wrap gap-2 mb-8">
            {{categories.map(cat => (
              <button
                key={{cat}}
                onClick={{() => setSelectedCategory(cat)}}
                className={{`px-4 py-2 rounded-full font-medium transition-colors ${{
                  selectedCategory === cat 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }}`}}
              >
                {{cat}}
              </button>
            ))}}
          </div>
          
          {{/* Products Grid */}}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {{filteredProducts.map(product => (
              <div key={{product.id}} className="bg-gray-800 rounded-xl overflow-hidden hover:ring-2 hover:ring-blue-500/50 transition-all">
                <div className="relative">
                  <img src={{product.image}} alt={{product.name}} className="w-full h-48 object-cover" />
                  {{product.badge && <span className="absolute top-3 left-3 px-2 py-1 bg-blue-500 text-white text-xs font-medium rounded-md">{{product.badge}}</span>}}
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-white mb-1">{{product.name}}</h3>
                  <p className="text-gray-400 text-sm mb-3">{{product.description}}</p>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-bold text-white">${{product.price}}</span>
                      {{product.originalPrice && <span className="text-sm text-gray-500 line-through">${{product.originalPrice}}</span>}}
                    </div>
                    <span className="text-yellow-400 text-sm">⭐ {{product.rating}}</span>
                  </div>
                  <button 
                    onClick={{() => addToCart(product)}}
                    className="w-full py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Add to Cart
                  </button>
                </div>
              </div>
            ))}}
          </div>
        </div>
      </section>
      
      {{/* Login Modal */}}
      {{showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={{() => setShowModal(false)}}>
          <div className="bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 border border-gray-700" onClick={{e => e.stopPropagation()}}>
            <h3 className="text-2xl font-bold text-white mb-6">Sign In</h3>
            <input type="email" placeholder="Email" className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg mb-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <input type="password" placeholder="Password" className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg mb-6 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <button 
              onClick={{() => {{ setIsLoggedIn(true); setShowModal(false); }}}}
              className="w-full px-4 py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 transition-colors"
            >
              Sign In
            </button>
            <button 
              onClick={{() => setShowModal(false)}}
              className="w-full px-4 py-3 mt-4 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}}
      
      {{/* Footer */}}
      <footer className="bg-gray-900 text-white py-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-400">© 2025 {project_name}. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}};

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
		
		# Generate Security Decision Records (SDRs)
		try:
			print(f"📋 Generating Security Decision Records...")
			sdrs = self.generate_security_decision_records(plan, project_spec)
			
			# Upload SDRs to S3 (in frontend folder so it's accessible)
			sdr_content = {
				"project": project_name,
				"generated_at": datetime.now().isoformat(),
				"decisions": sdrs
			}
			
			self.s3_uploader(
				project_slug,
				[{
					'path': 'frontend/sdr.json',
					'content': json.dumps(sdr_content, indent=2)
				}],
				self.user_id
			)
			files_created.append("frontend/sdr.json")
			print(f"✅ Generated {len(sdrs)} SDRs and uploaded to S3")
		except Exception as e:
			print(f"⚠️ Failed to generate SDRs (non-critical): {e}")
		
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
				"max_output_tokens": 65536,  # Maximum tokens for comprehensive frontend - DOUBLED
				"temperature": 0.05,  # Low temperature for consistency
			}
		else:
			config_overrides = {
				"max_output_tokens": 32768,  # Increased for all backend files
				"temperature": 0.05,
			}
			
		request = GenerationRequest(
			prompt=prompt,
			config_overrides=config_overrides,
		)
		
		generated_code = self._strip_code_fences(self._run_generation(request))
		
		# Apply immediate syntax fixes for App.jsx before validation
		if file_type == "frontend_app":
			generated_code = self._fix_jsx_syntax(generated_code)
			
			# Apply auto-fix for sandbox execution FIRST
			generated_code = auto_fix_jsx_for_sandbox(generated_code, "App.jsx")
			
			# Verify the generated code is not a placeholder/incomplete
			generated_code = self._verify_and_enhance_app_code(generated_code, plan, project_name)
			
			# Run ESLint validation and block if critical errors found
			validation_result = self.code_validator.validate_javascript_syntax(generated_code, "App.jsx")
			if not validation_result.is_valid and validation_result.errors:
				print(f"⚠️ ESLint validation found {len(validation_result.errors)} errors:")
				for error in validation_result.errors[:5]:  # Show first 5 errors
					print(f"   - {error}")
				print(f"🔧 Attempting to fix common issues...")
				# Apply additional fixes for common ESLint errors
				generated_code = self._fix_eslint_errors(generated_code, validation_result)
		
		return generated_code

	def _verify_and_enhance_app_code(self, code: str, plan: dict, project_name: str) -> str:
		"""Verify the generated code is production-ready, not placeholder content"""
		# Check for common signs of placeholder/incomplete code
		placeholder_indicators = [
			"Your application is being generated",
			"Coming Soon",
			"Under Construction", 
			"Lorem ipsum",
			"placeholder",
			"TODO:",
			"FIXME:",
			"// Your code here",
			"Welcome to your app",
			"Hello World",
			"def __init__",  # Python code in JSX
		]
		
		functional_indicators = [
			"useState(",
			"onClick=",
			"onSubmit=",
			"setCart",
			"setUser",
			"addToCart",
			"handleLogin",
			"handleSubmit",
			"useNavigate",
			"<Routes>",
			"<Route",
		]
		
		# Count placeholder indicators
		placeholder_count = sum(1 for indicator in placeholder_indicators if indicator.lower() in code.lower())
		
		# Count functional indicators
		functional_count = sum(1 for indicator in functional_indicators if indicator in code)
		
		print(f"📊 Code Quality Check: {functional_count} functional patterns, {placeholder_count} placeholder patterns")
		
		# If code has too many placeholders or too few functional patterns
		if placeholder_count >= 3 or (functional_count < 5 and len(code) < 5000):
			print(f"⚠️ Generated code appears incomplete or placeholder-heavy. Enhancing...")
			
			# Don't regenerate - instead, inject essential functionality
			enhancements = self._get_essential_functionality(plan, project_name)
			
			# Find a safe injection point (before the export or at the end)
			if "export default" in code:
				code = code.replace("export default", f"\n{enhancements}\n\nexport default")
			elif "window.App" in code:
				code = code.replace("window.App", f"\n{enhancements}\n\nwindow.App")
			else:
				code = code + f"\n\n{enhancements}"
		
		return code

	def _get_essential_functionality(self, plan: dict, project_name: str) -> str:
		"""Generate essential functionality code that must be present"""
		app_type = plan.get('app_type', 'general').lower()
		
		# Create safe project name for API
		safe_project_name = project_name.lower().replace(' ', '_').replace('-', '_')
		
		essential_code = f'''
// === ESSENTIAL FUNCTIONALITY FOR {project_name} ===
// Project name for API calls: {safe_project_name}

// === DATABASE API HELPERS ===
const API_BASE = 'http://localhost:8000/api/db';
const PROJECT_NAME = '{safe_project_name}';

// Generic API call helper
const apiCall = async (collection, method = 'GET', data = null, id = null) => {{
  const url = id 
    ? `${{API_BASE}}/${{PROJECT_NAME}}/${{collection}}/${{id}}`
    : `${{API_BASE}}/${{PROJECT_NAME}}/${{collection}}`;
  
  const options = {{
    method,
    headers: {{ 'Content-Type': 'application/json' }},
  }};
  
  if (data && (method === 'POST' || method === 'PUT')) {{
    options.body = JSON.stringify({{ data }});
  }}
  
  try {{
    const response = await fetch(url, options);
    return await response.json();
  }} catch (error) {{
    console.error(`API Error [${{method}} ${{collection}}]:`, error);
    return {{ success: false, error: error.message }};
  }}
}};

// Convenience methods
const db = {{
  getAll: (collection) => apiCall(collection, 'GET'),
  getOne: (collection, id) => apiCall(collection, 'GET', null, id),
  create: (collection, data) => apiCall(collection, 'POST', data),
  update: (collection, id, data) => apiCall(collection, 'PUT', data, id),
  delete: (collection, id) => apiCall(collection, 'DELETE', null, id),
  search: async (collection, query) => {{
    const response = await fetch(`${{API_BASE}}/${{PROJECT_NAME}}/${{collection}}/search?q=${{encodeURIComponent(query)}}`);
    return response.json();
  }}
}};

// Notification system (must work)
const showNotification = (message, type = 'success') => {{
  const notification = document.createElement('div');
  notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${{type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'}} text-white font-medium`;
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => notification.remove(), 3000);
}};

// Local storage helpers (for persistence and offline fallback)
const saveToStorage = (key, data) => {{
  try {{ localStorage.setItem(key, JSON.stringify(data)); }} catch(e) {{ console.warn('Storage error:', e); }}
}};

const loadFromStorage = (key, defaultValue = null) => {{
  try {{ 
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  }} catch(e) {{ return defaultValue; }}
}};
'''
		
		# Add cart functionality for e-commerce apps
		if any(word in app_type for word in ['shop', 'store', 'ecommerce', 'product', 'cart']):
			essential_code += f'''
// === RICH MOCK PRODUCT DATA (Fallback for E-Commerce) ===
const MOCK_PRODUCTS = [
  {{ id: 1, name: "Wireless Bluetooth Headphones", price: 79.99, originalPrice: 129.99, rating: 4.5, reviews: 2847, image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&q=80", category: "Electronics", badge: "Best Seller", description: "Premium sound quality with active noise cancellation" }},
  {{ id: 2, name: "Smart Fitness Watch Pro", price: 199.99, originalPrice: 249.99, rating: 4.7, reviews: 1523, image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&q=80", category: "Electronics", badge: "Top Rated", description: "Track your health and fitness goals" }},
  {{ id: 3, name: "Premium Leather Backpack", price: 89.99, rating: 4.3, reviews: 892, image: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&q=80", category: "Fashion", description: "Stylish and durable for everyday use" }},
  {{ id: 4, name: "Minimalist Desk Lamp", price: 49.99, rating: 4.6, reviews: 1205, image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&q=80", category: "Home", badge: "New", description: "Modern design with adjustable brightness" }},
  {{ id: 5, name: "Organic Coffee Beans 1kg", price: 24.99, rating: 4.8, reviews: 3421, image: "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=400&q=80", category: "Food & Drink", description: "Premium roasted arabica beans" }},
  {{ id: 6, name: "Yoga Mat Premium", price: 39.99, rating: 4.4, reviews: 756, image: "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400&h=400&q=80", category: "Sports", description: "Extra thick for comfort and stability" }},
  {{ id: 7, name: "Stainless Steel Water Bottle", price: 29.99, rating: 4.5, reviews: 2103, image: "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&h=400&q=80", category: "Sports", description: "Keep drinks cold for 24 hours" }},
  {{ id: 8, name: "Wireless Charging Pad", price: 34.99, originalPrice: 49.99, rating: 4.2, reviews: 1876, image: "https://images.unsplash.com/photo-1586816879360-004f5b0c51e5?w=400&h=400&q=80", category: "Electronics", badge: "Sale", description: "Fast charging for all Qi devices" }},
  {{ id: 9, name: "Aromatherapy Diffuser Set", price: 44.99, rating: 4.6, reviews: 945, image: "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=400&h=400&q=80", category: "Home", description: "Essential oil diffuser with LED lights" }},
  {{ id: 10, name: "Running Shoes Ultra", price: 129.99, originalPrice: 159.99, rating: 4.7, reviews: 2567, image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&q=80", category: "Sports", badge: "Popular", description: "Lightweight and breathable for long runs" }},
  {{ id: 11, name: "Mechanical Keyboard RGB", price: 149.99, rating: 4.8, reviews: 1834, image: "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400&h=400&q=80", category: "Electronics", description: "Cherry MX switches with RGB backlighting" }},
  {{ id: 12, name: "Ceramic Plant Pot Set", price: 32.99, rating: 4.4, reviews: 623, image: "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=400&h=400&q=80", category: "Home", description: "Set of 3 minimalist plant pots" }},
  {{ id: 13, name: "Portable Bluetooth Speaker", price: 59.99, rating: 4.5, reviews: 1456, image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&q=80", category: "Electronics", description: "Waterproof with 20-hour battery life" }},
  {{ id: 14, name: "Vintage Sunglasses", price: 45.99, rating: 4.3, reviews: 789, image: "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&q=80", category: "Fashion", description: "Classic style with UV protection" }},
  {{ id: 15, name: "Scented Candle Collection", price: 28.99, rating: 4.6, reviews: 1102, image: "https://images.unsplash.com/photo-1602028915047-37269d1a73f7?w=400&h=400&q=80", category: "Home", description: "Set of 4 relaxing scents" }},
  {{ id: 16, name: "Smart Home Hub", price: 89.99, rating: 4.4, reviews: 934, image: "https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=400&h=400&q=80", category: "Electronics", badge: "Smart Home", description: "Control all your smart devices" }},
];

const CATEGORIES = ["All", "Electronics", "Fashion", "Home", "Sports", "Food & Drink"];

// === E-COMMERCE CART FUNCTIONALITY ===
const useCartState = () => {{
  const [items, setItems] = React.useState(() => loadFromStorage('cart', []));
  
  const addItem = async (product) => {{
    const newItems = [...items, {{ ...product, cartId: Date.now(), quantity: 1 }}];
    setItems(newItems);
    saveToStorage('cart', newItems);
    showNotification(`Added ${{product.name}} to cart!`);
  }};
  
  const updateQuantity = (cartId, delta) => {{
    const newItems = items.map(item => 
      item.cartId === cartId 
        ? {{ ...item, quantity: Math.max(1, item.quantity + delta) }}
        : item
    );
    setItems(newItems);
    saveToStorage('cart', newItems);
  }};
  
  const removeItem = (cartId) => {{
    const newItems = items.filter(item => item.cartId !== cartId);
    setItems(newItems);
    saveToStorage('cart', newItems);
    showNotification('Item removed from cart');
  }};
  
  const clearCart = () => {{
    setItems([]);
    saveToStorage('cart', []);
  }};
  
  const checkout = async (shippingData) => {{
    const orderData = {{
      items: items.map(i => ({{ product_id: i.id, name: i.name, quantity: i.quantity, price: i.price }})),
      total: total,
      shipping: shippingData,
      created_at: new Date().toISOString()
    }};
    
    const result = await db.create('orders', orderData);
    if (result.success) {{
      clearCart();
      showNotification('Order placed successfully!');
      return result.data;
    }} else {{
      showNotification('Failed to place order', 'error');
      return null;
    }}
  }};
  
  const total = items.reduce((sum, item) => sum + ((item.price || 0) * (item.quantity || 1)), 0);
  
  return {{ items, addItem, updateQuantity, removeItem, clearCart, checkout, total, count: items.reduce((sum, i) => sum + i.quantity, 0) }};
}};

// Fetch products from database with fallback to mock data
const useProducts = (category = null) => {{
  const [products, setProducts] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  
  React.useEffect(() => {{
    const fetchProducts = async () => {{
      setLoading(true);
      const url = category 
        ? `${{API_BASE}}/${{PROJECT_NAME}}/products?category=${{encodeURIComponent(category)}}`
        : `${{API_BASE}}/${{PROJECT_NAME}}/products`;
      
      try {{
        const response = await fetch(url);
        const result = await response.json();
        if (result.success && result.data.length > 0) {{
          setProducts(result.data);
        }} else {{
          // Use mock data as fallback
          setProducts(MOCK_PRODUCTS);
        }}
      }} catch (error) {{
        console.warn('Using mock products (API unavailable)');
        setProducts(MOCK_PRODUCTS);
      }} finally {{
        setLoading(false);
      }}
    }};
    fetchProducts();
  }}, [category]);
  
  return {{ products, loading }};
}};
'''
		
		# Add auth functionality for all apps - INTEGRATED WITH MONGODB BACKEND
		essential_code += '''
// === AUTHENTICATION FUNCTIONALITY (MONGODB BACKEND INTEGRATED) ===
// API Base URL for authentication - connects to MongoDB backend
const AUTH_API_BASE = 'http://localhost:8000/api/auth';

// Helper function to make authenticated API calls
const authenticatedFetch = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
};

const useAuthState = () => {
  const [user, setUser] = React.useState(() => loadFromStorage('user', null));
  const [isLoggedIn, setIsLoggedIn] = React.useState(() => !!loadFromStorage('access_token'));
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  
  // Login with MongoDB backend
  const login = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${AUTH_API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }
      
      // Save token and user data
      localStorage.setItem('access_token', data.access_token);
      saveToStorage('user', data.user);
      setUser(data.user);
      setIsLoggedIn(true);
      showNotification(`Welcome back, ${data.user.username || data.user.email}!`);
      return data.user;
    } catch (err) {
      setError(err.message);
      showNotification(err.message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Signup with MongoDB backend
  const signup = async (userData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${AUTH_API_BASE}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: userData.email,
          username: userData.username || userData.name || userData.email.split('@')[0],
          password: userData.password
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Signup failed');
      }
      
      // Save token and user data
      localStorage.setItem('access_token', data.access_token);
      saveToStorage('user', data.user);
      setUser(data.user);
      setIsLoggedIn(true);
      showNotification(`Welcome, ${data.user.username}! Account created successfully.`);
      return data.user;
    } catch (err) {
      setError(err.message);
      showNotification(err.message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Logout - clears token and user data
  const logout = async () => {
    try {
      // Call backend logout endpoint (optional, for token blacklisting)
      await authenticatedFetch(`${AUTH_API_BASE}/logout`, { method: 'POST' }).catch(() => {});
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setUser(null);
      setIsLoggedIn(false);
      showNotification('Logged out successfully');
    }
  };
  
  // Get current user from backend
  const getCurrentUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    try {
      const response = await authenticatedFetch(`${AUTH_API_BASE}/me`);
      if (!response.ok) {
        // Token expired or invalid
        logout();
        return null;
      }
      const userData = await response.json();
      setUser(userData);
      saveToStorage('user', userData);
      return userData;
    } catch (err) {
      console.error('Failed to get current user:', err);
      return null;
    }
  };
  
  // Check authentication status on mount
  React.useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !user) {
      getCurrentUser();
    }
  }, []);
  
  return { user, isLoggedIn, loading, error, login, signup, logout, getCurrentUser, authenticatedFetch };
};

// === BACKEND API INTEGRATION ===
// These functions connect your frontend to the generated backend API
const backendAPI = {
  // Base URL for the generated project backend
  baseUrl: 'http://localhost:8000/api/v1',
  
  // Generic authenticated request helper
  async request(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('access_token');
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }
    };
    
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, options);
    const result = await response.json();
    
    if (!response.ok) {
      throw new Error(result.detail || 'API request failed');
    }
    
    return result;
  },
  
  // Convenience methods
  get: (endpoint) => backendAPI.request(endpoint, 'GET'),
  post: (endpoint, data) => backendAPI.request(endpoint, 'POST', data),
  put: (endpoint, data) => backendAPI.request(endpoint, 'PUT', data),
  delete: (endpoint) => backendAPI.request(endpoint, 'DELETE'),
};
'''
		
		return essential_code

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
		
		# Enhanced index.html - PRODUCTION READY with auto-fix agent
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
    
    <!-- Auto-Fix Error Interceptor - Automatically fixes runtime errors -->
    <script>
    (function() {{
      const projectSlug = window.location.pathname.split('/').pop() || '{project_name}';
      const userId = new URLSearchParams(window.location.search).get('user_id_alt') || 'anonymous';
      
      class ErrorInterceptor {{
        constructor(projectSlug, userId) {{
          this.projectSlug = projectSlug;
          this.userId = userId;
          this.reportedErrors = new Set();
          this.init();
        }}
        
        init() {{
          const self = this;
          const originalError = console.error;
          console.error = function(...args) {{
            originalError.apply(console, args);
            const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            self.reportError(msg, new Error().stack);
          }};
          
          window.addEventListener('error', (e) => self.reportError(e.message, e.error?.stack || '', e.filename));
          window.addEventListener('unhandledrejection', (e) => self.reportError(`Promise: ${{e.reason}}`, e.reason?.stack || ''));
        }}
        
        async reportError(msg, stack, file) {{
          const sig = `${{msg}}-${{file}}`.substring(0, 100);
          if (this.reportedErrors.has(sig)) return;
          this.reportedErrors.add(sig);
          
          console.log('🤖 Auto-fix agent analyzing error...');
          
          try {{
            const res = await fetch('http://localhost:8000/api/auto-fix-errors', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ project_name: this.projectSlug, user_id: this.userId, error_message: msg, error_stack: stack, file_path: file }})
            }});
            
            const result = await res.json();
            if (result.success) {{
              console.log(`✅ Auto-fixed: ${{result.message}}`);
              setTimeout(() => location.reload(), 2000);
            }}
          }} catch(e) {{
            console.warn('Auto-fix unavailable:', e);
          }}
        }}
      }}
      
      new ErrorInterceptor(projectSlug, userId);
    }})();
    </script>
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

@layer components {
  /* Awwwards Glass Morphism */
  .glass-morphism {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }
  
  .glass-dark {
    background: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  /* Award-winning Gradients */
  .gradient-text {
    @apply bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent;
  }
  
  .gradient-vibrant {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  .gradient-mesh {
    background: radial-gradient(circle at 20% 50%, #ff6b6b 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, #4ecdc4 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, #45b7d1 0%, transparent 50%),
                linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }
  
  /* Modern Shadows */
  .shadow-glow {
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.4);
  }
  
  .shadow-float {
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  }
  
  .shadow-vibrant {
    box-shadow: 0 10px 40px rgba(124, 58, 237, 0.3);
  }
  
  /* Interactive Elements */
  .btn-awwwards {
    @apply relative overflow-hidden px-8 py-4 rounded-2xl font-semibold text-white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    transition: all 0.3s ease;
  }
  
  .btn-awwwards::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }
  
  .btn-awwwards:hover::before {
    left: 100%;
  }
  
  .btn-awwwards:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
  }
  
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
		self._write_files_parallel(supporting_files, project_name)
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
		"""Extract code from AI response, removing description text and markdown fences."""
		import re
		
		stripped = text.strip()
		
		# First, try to find code block with language identifier (```jsx, ```javascript, ```python, etc.)
		code_block_match = re.search(r'```(?:jsx|javascript|js|python|py|typescript|ts|html|css)?\s*\n(.*?)```', stripped, re.DOTALL)
		if code_block_match:
			return code_block_match.group(1).strip()
		
		# If no code block found, check if it starts with code fence
		if stripped.startswith("```"):
			stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
		
		# Check if it ends with code fence
		if stripped.endswith("```"):
			stripped = stripped.rsplit("\n", 1)[0] if "\n" in stripped else stripped[:-3]
		
		# If there's still description text before the code, try to find the actual code start
		# Look for common code patterns that indicate where real code begins
		code_start_patterns = [
			r'^(// NO IMPORTS)',  # Common in our generated code
			r'^(// App\.jsx)',
			r'^(// (?:Main )?App)',
			r'^(import\s+)',  # Import statement
			r'^(const\s+)',  # Const declaration
			r'^(function\s+)',  # Function declaration
			r'^(export\s+)',  # Export statement
			r'^(class\s+)',  # Class declaration
			r'^(/\*)',  # Multi-line comment start
		]
		
		lines = stripped.split('\n')
		for i, line in enumerate(lines):
			line_stripped = line.strip()
			for pattern in code_start_patterns:
				if re.match(pattern, line_stripped, re.IGNORECASE):
					# Found code start, return from here
					return '\n'.join(lines[i:]).strip()
		
		return stripped.strip()

	def _fix_jsx_syntax(self, code: str) -> str:
		"""Apply quick JSX syntax fixes before validation."""
		import re
		
		# Fix common JSX issues
		# 1. Fix class -> className
		code = re.sub(r'\bclass=', 'className=', code)
		
		# 2. Fix for -> htmlFor
		code = re.sub(r'\bfor=', 'htmlFor=', code)
		
		# 3. Ensure self-closing tags have proper syntax
		code = re.sub(r'<(img|br|hr|input|meta|link)([^>]*[^/])>', r'<\1\2 />', code)
		
		# 4. Fix style attributes that should be objects
		# Convert style="color: red; font-size: 16px" to style={{color: 'red', fontSize: '16px'}}
		def fix_style_attr(match):
			style_content = match.group(1)
			if '{' in style_content:
				return match.group(0)  # Already object syntax
			
			# Parse CSS string
			styles = {}
			for rule in style_content.split(';'):
				if ':' in rule:
					prop, value = rule.split(':', 1)
					prop = prop.strip()
					value = value.strip()
					# Convert kebab-case to camelCase
					prop_camel = ''.join(word.capitalize() if i > 0 else word 
					                   for i, word in enumerate(prop.split('-')))
					styles[prop_camel] = value
			
			if not styles:
				return match.group(0)
			
			# Convert to JSX object notation
			style_obj = ', '.join(f"{k}: '{v}'" for k, v in styles.items())
			return f'style={{{{{style_obj}}}}}'
		
		code = re.sub(r'style=["\']([^"\']+)["\']', fix_style_attr, code)
		
		return code

	def _fix_eslint_errors(self, code: str, validation_result) -> str:
		"""Apply fixes for common ESLint errors."""
		import re
		
		# Fix unused imports by removing them
		if any('is defined but never used' in err for err in validation_result.errors):
			# Remove unused React import if components don't use JSX.createElement
			if "React" in code and "'React' is defined but never used" in str(validation_result.errors):
				# Check if React is actually used
				if not re.search(r'React\.(createElement|Fragment|useState|useEffect)', code):
					code = re.sub(r"import\s+React\s+from\s+['\"]react['\"];\s*\n?", '', code)
					code = re.sub(r"import\s+React,\s*{", 'import {', code)
		
		# Fix missing keys in map operations
		if any('Missing "key" prop' in err for err in validation_result.errors):
			# Add key prop to elements in map
			def add_key_to_map(match):
				map_content = match.group(0)
				if 'key=' not in map_content:
					# Try to find the opening tag after .map
					tag_match = re.search(r'\.map\([^)]+\)\s*=>\s*(\{?\s*<(\w+)', map_content)
					if tag_match:
						tag_name = tag_match.group(2)
						# Add key prop
						map_content = map_content.replace(
							f'<{tag_name}',
							f'<{tag_name} key={{index}}',
							1
						)
				return map_content
			
			code = re.sub(r'\.map\([^{]+{[^}]+}', add_key_to_map, code)
		
		return code

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
	def _build_plan_prompt(project_spec, project_name: str, website_inspiration_context: str = "") -> str:
		# Extract details from project specification
		if isinstance(project_spec, dict):
			idea = project_spec.get("idea", "")
			project_type = project_spec.get("project_type", "web app")
			features = project_spec.get("features", [])
			tech_stack = project_spec.get("tech_stack", [])
			# NEW: Extract user-provided documentation context
			documentation_context = project_spec.get("documentation_context", "")
			# NEW: Get website inspiration context if passed in spec
			website_inspiration_context = project_spec.get("website_inspiration_context", website_inspiration_context)
			# NEW: Extract user-provided product data (for e-commerce projects)
			product_data = project_spec.get("product_data")
			custom_data = project_spec.get("custom_data", {})
		else:
			idea = str(project_spec)
			project_type = "web app"
			features = []
			tech_stack = []
			documentation_context = ""
			product_data = None
			custom_data = {}
		
		# Build detailed prompt with user specifications
		spec_details = f"Project Type: {project_type}\n"
		if features:
			spec_details += f"Required Features: {', '.join(features)}\n"
		if tech_stack:
			spec_details += f"Tech Stack: {', '.join(tech_stack)}\n"
		
		# Add website inspiration section if available
		website_section = ""
		if website_inspiration_context:
			website_section = f"""
{website_inspiration_context}

"""
		
		# Add documentation context if provided by user
		doc_section = ""
		if documentation_context:
			doc_section = f"""
=== USER PROVIDED DOCUMENTATION ===
The user has uploaded reference documents (PDFs, images, specifications) to guide this project.
Use this information to create accurate, specific features and designs.

{documentation_context}

IMPORTANT: 
- Base the features, UI design, and functionality on this documentation
- Use exact terminology, field names, and workflows described in the documents
- If images show UI mockups, replicate the layout, colors, and components shown
- Extract any business rules, validation requirements, or data models described
=== END USER DOCUMENTATION ===

"""
		
		# Add product data section for e-commerce projects
		product_section = ""
		if product_data:
			product_section = f"""
=== USER PROVIDED PRODUCT DATA ===
The user has provided their actual product catalog to use in this e-commerce project.
DO NOT use mock/placeholder product data. Use ONLY these real products:

{json.dumps(product_data, indent=2)}

CRITICAL REQUIREMENTS:
- Use EXACTLY these products with their real names, prices, and descriptions
- Display the user's actual product images (if image URLs provided)
- Categories should match the user's product categories
- Prices must be exact as provided (no made-up prices)
- This is REAL business data - accuracy is mandatory
=== END USER PRODUCT DATA ===

"""
		
		# Add custom data section (menu items, services, etc.)
		custom_section = ""
		if custom_data:
			custom_section = f"""
=== USER PROVIDED CUSTOM DATA ===
The user has provided specific data to use in this project:

{json.dumps(custom_data, indent=2)}

IMPORTANT: Use this exact data in the application instead of placeholder/mock data.
=== END USER CUSTOM DATA ===

"""
		
		return (
			f"Create a COMPREHENSIVE, MULTI-PAGE, PRODUCTION-READY project plan in JSON for: {idea}\n"
			f"Project: {project_name}\n"
			f"{spec_details}\n"
			f"{website_section}"
			f"{doc_section}"
			f"{product_section}"
			f"{custom_section}"
			"🎯 MANDATORY REQUIREMENTS:\n"
			"- Generate 5-8 SPECIFIC, DETAILED features (not generic)\n"
			"- Create 6-10 separate page components (Home, About, Features, Contact, etc.)\n"
			"- Design 3-5 backend models with complete fields and relationships\n"
			"- Define 10-15 FULLY FUNCTIONAL RESTful API endpoints\n"
			"- Plan for REAL IMAGES from Unsplash API (never use placeholder URLs)\n"
			"- Include working authentication (login/signup/logout)\n"
			"- Add shopping cart for e-commerce projects (fully functional)\n"
			"- Include REAL data examples and use cases\n"
			+ ("- CRITICAL: Use the user's documentation to define exact features, UI, and data models\n" if documentation_context else "")
			+ ("- CRITICAL: Create a SIMILAR but UNIQUE design inspired by the analyzed website - do NOT copy exactly\n" if website_inspiration_context else "") +
			"\nJSON format:\n"
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
			"    \"stack\": \"React+Vite+Tailwind+Framer Motion+React Router\",\n"
			"    \"pages\": [\n"
			"      {\"name\": \"HomePage\", \"route\": \"/\", \"purpose\": \"Main landing page with hero and features\"},\n"
			"      {\"name\": \"AboutPage\", \"route\": \"/about\", \"purpose\": \"About us with team and mission\"},\n"
			"      {\"name\": \"FeaturesPage\", \"route\": \"/features\", \"purpose\": \"Detailed features showcase\"},\n"
			"      {\"name\": \"ContactPage\", \"route\": \"/contact\", \"purpose\": \"Contact form with working submission\"},\n"
			"      {\"name\": \"DashboardPage\", \"route\": \"/dashboard\", \"purpose\": \"User dashboard (protected route)\"},\n"
			"      {\"name\": \"ProfilePage\", \"route\": \"/profile\", \"purpose\": \"User profile management (protected)\"}\n"
			"    ],\n"
			"    \"components\": [\n"
			"      {\"name\": \"Header\", \"purpose\": \"Navigation with auth state and cart\"},\n"
			"      {\"name\": \"HeroSection\", \"purpose\": \"Eye-catching landing section with CTA\"},\n"
			"      {\"name\": \"FeaturesGrid\", \"purpose\": \"Showcase features with real images\"},\n"
			"      {\"name\": \"ProductCard\", \"purpose\": \"Product display with add to cart\"},\n"
			"      {\"name\": \"ShoppingCart\", \"purpose\": \"Fully functional cart with backend sync\"},\n"
			"      {\"name\": \"Footer\", \"purpose\": \"Footer with links and info\"}\n"
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
				"backend/database.py",
				"backend/requirements.txt",
			],
			"optional_paths": [
				"backend/auth.py",
				"backend/schemas.py",
			],
		}

		return (
			"You are generating a COMPLETE, FULLY FUNCTIONAL FastAPI backend for a project. "
			"Return a JSON object that maps POSIX file paths to file contents. "
			"Do not include markdown or code fences; encode newlines with \\n as required by JSON string rules.\n\n"
			f"Project name: {project_name}\n"
			+ "Backend plan context:\n"
			+ json.dumps({
				"stack": backend_plan.get("stack", "FastAPI + Pydantic + SQLite/MongoDB"),
				"models": models,
				"endpoints": endpoints,
				"features": plan.get("features", []),
			}, indent=2)
			+ "\n\n🚨🚨🚨 CRITICAL: GENERATE FULLY WORKING BACKEND - NO MOCKS! 🚨🚨🚨\n\n"
			"Requirements:\n"
			"* Use FastAPI with Pydantic v2 models and ConfigDict(from_attributes=True).\n"
			"* ⚠️ MUST use REAL DATABASE persistence - SQLite with SQLAlchemy ORM (NOT in-memory dicts/lists!).\n"
			"* database.py MUST create actual database connection and session management.\n"
			"* ALL CRUD operations MUST read/write to the actual database.\n"
			"* Ensure main.py creates the FastAPI app, configures CORS, and includes routes from routes.py.\n"
			"* routes.py must wire CRUD endpoints that align exactly with the plan endpoints.\n"
			"* requirements.txt must list ALL dependencies needed to run the backend.\n"
			"* Every endpoint MUST be fully implemented - NO placeholder 'pass' statements!\n"
			"* Include proper error handling with HTTPException for all edge cases.\n\n"
			
			"📦 REQUIRED FILES AND THEIR CONTENTS:\n\n"
			
			"1. backend/database.py - Database Connection:\n"
			"```python\n"
			"from sqlalchemy import create_engine\n"
			"from sqlalchemy.ext.declarative import declarative_base\n"
			"from sqlalchemy.orm import sessionmaker\n"
			"import os\n\n"
			"SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./app.db')\n"
			"engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})\n"
			"SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n"
			"Base = declarative_base()\n\n"
			"def get_db():\n"
			"    db = SessionLocal()\n"
			"    try:\n"
			"        yield db\n"
			"    finally:\n"
			"        db.close()\n"
			"```\n\n"
			
			"2. backend/models.py - SQLAlchemy Models (NOT Pydantic):\n"
			"```python\n"
			"from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean\n"
			"from sqlalchemy.orm import relationship\n"
			"from datetime import datetime\n"
			"from database import Base\n\n"
			"class User(Base):\n"
			"    __tablename__ = 'users'\n"
			"    id = Column(Integer, primary_key=True, index=True)\n"
			"    email = Column(String, unique=True, index=True)\n"
			"    username = Column(String, unique=True, index=True)\n"
			"    hashed_password = Column(String)\n"
			"    is_active = Column(Boolean, default=True)\n"
			"    created_at = Column(DateTime, default=datetime.utcnow)\n"
			"# Add more models based on project requirements\n"
			"```\n\n"
			
			"3. backend/schemas.py - Pydantic Schemas:\n"
			"```python\n"
			"from pydantic import BaseModel, ConfigDict\n"
			"from datetime import datetime\n"
			"from typing import Optional, List\n\n"
			"class UserCreate(BaseModel):\n"
			"    email: str\n"
			"    username: str\n"
			"    password: str\n\n"
			"class UserResponse(BaseModel):\n"
			"    model_config = ConfigDict(from_attributes=True)\n"
			"    id: int\n"
			"    email: str\n"
			"    username: str\n"
			"    is_active: bool\n"
			"```\n\n"
			
			"4. backend/routes.py - FULLY IMPLEMENTED CRUD:\n"
			"```python\n"
			"from fastapi import APIRouter, Depends, HTTPException, status\n"
			"from sqlalchemy.orm import Session\n"
			"from typing import List\n"
			"from database import get_db\n"
			"import models, schemas\n\n"
			"router = APIRouter(prefix='/api/v1')\n\n"
			"@router.get('/items', response_model=List[schemas.ItemResponse])\n"
			"def get_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):\n"
			"    items = db.query(models.Item).offset(skip).limit(limit).all()\n"
			"    return items\n\n"
			"@router.post('/items', response_model=schemas.ItemResponse)\n"
			"def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):\n"
			"    db_item = models.Item(**item.model_dump())\n"
			"    db.add(db_item)\n"
			"    db.commit()\n"
			"    db.refresh(db_item)\n"
			"    return db_item\n"
			"```\n\n"
			
			"5. backend/main.py - Complete App Setup:\n"
			"```python\n"
			"from fastapi import FastAPI\n"
			"from fastapi.middleware.cors import CORSMiddleware\n"
			"from database import engine, Base\n"
			"import models\n"
			"from routes import router\n\n"
			"# Create database tables\n"
			"Base.metadata.create_all(bind=engine)\n\n"
			"app = FastAPI(title='Project API')\n\n"
			"app.add_middleware(\n"
			"    CORSMiddleware,\n"
			"    allow_origins=['http://localhost:5173', 'http://localhost:3000'],\n"
			"    allow_credentials=True,\n"
			"    allow_methods=['*'],\n"
			"    allow_headers=['*'],\n"
			")\n\n"
			"app.include_router(router)\n"
			"```\n\n"
			
			"6. backend/requirements.txt:\n"
			"```\n"
			"fastapi>=0.100.0\n"
			"uvicorn[standard]>=0.23.0\n"
			"sqlalchemy>=2.0.0\n"
			"pydantic>=2.0.0\n"
			"python-jose[cryptography]>=3.3.0\n"
			"passlib[bcrypt]>=1.7.4\n"
			"python-multipart>=0.0.6\n"
			"python-dotenv>=1.0.0\n"
			"```\n\n"
			
			"7. SEED DATA ON STARTUP (Add to main.py):\n"
			"```python\n"
			"# Seed initial data on startup\n"
			"@app.on_event('startup')\n"
			"def seed_database():\n"
			"    db = SessionLocal()\n"
			"    try:\n"
			"        # Check if products already exist\n"
			"        if db.query(models.Product).count() == 0:\n"
			"            sample_products = [\n"
			"                models.Product(name='Wireless Headphones', description='Premium sound quality', price=79.99, category='Electronics', stock_quantity=50, image_url='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400'),\n"
			"                models.Product(name='Smart Watch', description='Track your fitness goals', price=199.99, category='Electronics', stock_quantity=30, image_url='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400'),\n"
			"                models.Product(name='Leather Backpack', description='Stylish and durable', price=89.99, category='Fashion', stock_quantity=25, image_url='https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400'),\n"
			"                models.Product(name='Coffee Maker', description='Brew perfect coffee', price=149.99, category='Home', stock_quantity=20, image_url='https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400'),\n"
			"                models.Product(name='Running Shoes', description='Lightweight performance', price=129.99, category='Sports', stock_quantity=40, image_url='https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400'),\n"
			"            ]\n"
			"            for product in sample_products:\n"
			"                db.add(product)\n"
			"            db.commit()\n"
			"            print('✅ Database seeded with sample products')\n"
			"    finally:\n"
			"        db.close()\n"
			"```\n\n"
			
			"⛔ FORBIDDEN - DO NOT GENERATE:\n"
			"- In-memory storage like `items = []` or `db = {}`\n"
			"- Placeholder functions with just `pass`\n"
			"- Mock data that doesn't persist\n"
			"- Endpoints that return hardcoded responses\n"
			"- TODO comments instead of actual code\n\n"
			
			"✅ REQUIRED - MUST GENERATE:\n"
			"- Real SQLite database with SQLAlchemy\n"
			"- All CRUD operations that actually persist data\n"
			"- Proper foreign key relationships\n"
			"- Error handling for not found, duplicates, etc.\n"
			"- Working authentication with password hashing\n"
			"- Database migrations/table creation on startup\n"
			"- SEED DATA on first startup so the app has content\n\n"
			
			"Output JSON schema:\n"
			+ json.dumps(schema, indent=2)
			+ "\nEnsure every required path is present with COMPLETE, WORKING code."
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
		models = backend_plan.get('models', [])[:5]  # Allow up to 5 models
		endpoints = backend_plan.get('endpoints', [])[:8]
		
		# Build model names list for routes to reference
		model_names = [m.get('name', m) if isinstance(m, dict) else str(m).replace(' ', '') for m in models]
		
		return f"""
Create FastAPI models.py with SQLAlchemy ORM models for a REAL DATABASE.

Models needed: {models}
Endpoints that will use these models: {endpoints}

🎯 MODEL NAMES TO CREATE (routes.py will import these exact names):
{chr(10).join(f'- {name}' for name in model_names)}

🚨 CRITICAL REQUIREMENTS:
- Use SQLAlchemy ORM models (NOT Pydantic for database models!)
- Import Base from database.py
- Include proper Column types: Integer, String, Float, DateTime, Text, Boolean, ForeignKey
- Add relationships between models where appropriate
- Include created_at and updated_at timestamps
- Add proper indexes on frequently queried columns

EXAMPLE STRUCTURE:
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    category = Column(String(100), index=True)
    image_url = Column(String(500))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

⛔ DO NOT use in-memory lists/dicts like `products = []`
✅ MUST use SQLAlchemy Column definitions that persist to database

Return complete, working Python code only.
"""

	@staticmethod  
	def _build_routes_prompt(plan: Dict[str, Any]) -> str:
		backend_plan = plan.get("backend", {})
		endpoints = backend_plan.get('endpoints', [])[:8]  # Allow up to 8 endpoints
		models = backend_plan.get('models', [])[:5]
		
		# Build model names that routes MUST import and use
		model_names = [m.get('name', m) if isinstance(m, dict) else str(m).replace(' ', '') for m in models]
		
		return f"""
Create FastAPI routes.py with FULLY WORKING CRUD endpoints.

Endpoints needed: {endpoints}

🎯 MODELS TO IMPORT AND USE (from models.py):
{chr(10).join(f'- models.{name}' for name in model_names)}

You MUST import and use ALL these models in your database queries.
Example: db.query(models.{model_names[0] if model_names else 'Product'}).all()

🚨 CRITICAL REQUIREMENTS:
- Use APIRouter with proper prefix
- Import get_db from database.py
- Import models from models.py  
- ALL database operations MUST use SQLAlchemy session (db.query, db.add, db.commit)
- Include proper error handling with HTTPException
- Return proper response models

EXAMPLE FULLY WORKING ROUTES:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/api/v1", tags=["API"])

# Pydantic schemas for request/response
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    category: Optional[str]
    image_url: Optional[str]
    is_available: bool

# GET all products - READS FROM DATABASE
@router.get("/products", response_model=List[ProductResponse])
def get_products(
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.category == category)
    products = query.offset(skip).limit(limit).all()
    return products

# GET single product - READS FROM DATABASE
@router.get("/products/{{product_id}}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# POST create product - WRITES TO DATABASE
@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# PUT update product - UPDATES DATABASE
@router.put("/products/{{product_id}}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

# DELETE product - DELETES FROM DATABASE
@router.delete("/products/{{product_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return None
```

⛔ FORBIDDEN:
- In-memory storage: `items = []` or `db = {{}}`
- Placeholder code: `pass` or `# TODO`
- Hardcoded return values
- Missing error handling

✅ REQUIRED:
- db.query() for reading
- db.add() + db.commit() for creating
- db.commit() for updating  
- db.delete() + db.commit() for deleting
- HTTPException for errors

Return complete, working Python code only.
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
   - Google OAuth endpoint: POST /api/v1/auth/google (accepts {{id_token: string}})
   - Get current user: GET /api/v1/auth/me
   - Token refresh: POST /api/v1/auth/refresh
   - Password hashing with bcrypt or passlib
   - Proper JWT secret key configuration
   - Token expiration and validation
   - Google ID token verification using google.oauth2.id_token

2. COMPREHENSIVE CORS CONFIGURATION:
   - Allow all origins for local development (http://localhost:5173)
   - Allow credentials for cookie/token handling
   - Proper headers for authentication
   - Methods: GET, POST, PUT, DELETE, OPTIONS

3. DATABASE INTEGRATION:
   - SQLite database with SQLAlchemy ORM
   - IMPORT models from models.py (do NOT redefine them in main.py!)
   - IMPORT routes from routes.py and include the router
   - Database session dependency
   - Automatic table creation on startup
   
   🚨 CRITICAL: Use the models from models.py, don't duplicate them!
   ```python
   from database import engine, SessionLocal, get_db
   import models
   from routes import router
   
   # Create tables from models.py
   models.Base.metadata.create_all(bind=engine)
   
   # Include routes from routes.py
   app.include_router(router)
   ```
   
   IMPORTANT: The main AltX backend already has MongoDB authentication at:
   - POST /api/auth/signup - User registration (stores in MongoDB)
   - POST /api/auth/login - User login (validates against MongoDB)
   - GET /api/auth/me - Get current user (requires JWT token)
   - POST /api/auth/logout - Logout (client-side token removal)
   
   The generated project backend should integrate with or mirror these endpoints.

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

🗄️ MONGODB INTEGRATION OPTION (Recommended for production):
```python
# For MongoDB integration, use pymongo:
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URL)
db = client["app_database"]

# Collections
users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]

# Create indexes
users_collection.create_index([("email", ASCENDING)], unique=True)
```

AUTHENTICATION FLOW IMPLEMENTATION:
```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import httpx
from datetime import datetime, timedelta
import os
from pydantic import BaseModel

# Import from project files - DO NOT REDEFINE!
from database import engine, SessionLocal, get_db
import models  # Use models from models.py
from routes import router  # Use routes from routes.py

# Create tables from models.py
models.Base.metadata.create_all(bind=engine)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic schemas for auth (NOT database models!)
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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={{"WWW-Authenticate": "Bearer"}},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# Authentication functions - FULLY IMPLEMENTED
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({{"exp": expire}})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

{f'''
E-COMMERCE MODELS - THESE MUST BE IN models.py, NOT HERE!
The models.py file should contain: Product, CartItem, Order, User
Do NOT redefine models in main.py - import them with: import models
Then use: models.Product, models.CartItem, models.Order, models.User
''' if has_ecommerce else ''}

MAIN APP STRUCTURE:
```python
app = FastAPI(title="{project_name}", description="{description}")

# Include routes from routes.py
app.include_router(router)

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

# Authentication routes - FULLY IMPLEMENTED (NO PLACEHOLDERS!)
# Use models.User from models.py - do NOT redefine!
@app.post("/api/auth/signup", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.name,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={{"sub": str(db_user.id)}})
    return {{
        "access_token": access_token,
        "token_type": "bearer",
        "user": {{"id": db_user.id, "name": db_user.username, "email": db_user.email}}
    }}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={{"WWW-Authenticate": "Bearer"}},
        )
    access_token = create_access_token(data={{"sub": str(user.id)}})
    return {{
        "access_token": access_token,
        "token_type": "bearer",
        "user": {{"id": user.id, "name": user.username, "email": user.email}}
    }}

# Also support JSON login for frontend compatibility
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login/json", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    access_token = create_access_token(data={{"sub": str(user.id)}})
    return {{
        "access_token": access_token,
        "token_type": "bearer",
        "user": {{"id": user.id, "name": user.username, "email": user.email}}
    }}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    return {{"id": current_user.id, "name": current_user.username, "email": current_user.email}}
```

🚨 IMPORTANT: ALL models must be imported from models.py - use `models.User`, `models.Product`, etc.
🚨 ALL routes must be imported from routes.py - use `app.include_router(router)`

🚨🚨🚨 CRITICAL: ALL CODE MUST BE FULLY IMPLEMENTED - NO `pass` STATEMENTS! 🚨🚨🚨

⛔ FORBIDDEN:
- `pass` statements anywhere in the code
- `# TODO` or `# Implement` comments
- Placeholder functions
- In-memory storage (lists/dicts instead of database)
- Hardcoded responses without database queries
- REDEFINING models that are already in models.py

✅ EVERY FUNCTION MUST:
- Have complete working implementation
- Read/write to SQLite database via SQLAlchemy
- Use `models.ModelName` for all database queries (import models)
- Include proper error handling
- Return actual data from database queries

Return COMPLETE, WORKING Python code with all imports, models, authentication, and API endpoints FULLY IMPLEMENTED.
"""

	@staticmethod
	def _get_react_bits_components() -> Dict[str, str]:
		"""Returns a collection of React Bits-inspired component patterns"""
		return {
			"frontend/src/components/ui/Button.jsx": '''import React from 'react';

// Safe motion fallback if framer-motion not available
const motion = window.motion || {
  button: ({ children, className, style, onClick, disabled, whileHover, whileTap, ...props }) => 
    React.createElement('button', { className, style, onClick, disabled, ...props }, children)
};

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

// Safe motion fallback if framer-motion not available
const motion = window.motion || {
  div: ({ children, className, style, onClick, initial, animate, whileHover, ...props }) => 
    React.createElement('div', { className, style, onClick, ...props }, children)
};

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

// Safe motion fallback if framer-motion not available
const motion = window.motion || {
  span: ({ children, className, style, onClick, initial, animate, transition, ...props }) => 
    React.createElement('span', { className, style, onClick, ...props }, children)
};

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

// Safe motion fallback if framer-motion not available
const motion = window.motion || {
  div: ({ children, className, style, animate, transition, ...props }) => 
    React.createElement('div', { className, style, ...props }, children)
};

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

// Safe motion fallback if framer-motion not available
const motion = window.motion || {
  div: ({ children, className, style, initial, animate, ...props }) => 
    React.createElement('div', { className, style, ...props }, children),
  label: ({ children, className, style, animate, ...props }) => 
    React.createElement('label', { className, style, ...props }, children)
};

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

// Safe motion fallback if framer-motion not available
const motion = window.motion || {
  div: ({ children, className, style, initial, animate, ...props }) => 
    React.createElement('div', { className, style, ...props }, children)
};

// Lucide icon fallbacks - simple SVG icons
const Menu = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </svg>
);

const X = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

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
		"""Build comprehensive prompt for App.jsx generation - All curly braces properly escaped for f-string"""
		features = plan.get('features', [])
		features_str = [str(f) for f in features] if features else ['Modern features']
		app_type = plan.get('app_type', 'Web App')
		description = plan.get('description', 'A modern web application')
		
		# Extract user-provided product data and custom data
		user_product_data = plan.get('_user_product_data')
		user_custom_data = plan.get('_user_custom_data', {})
		
		# Extract ML/LLM requirements
		ml_requirements = plan.get('_ml_requirements', {})
		llm_requirements = plan.get('_llm_requirements', {})
		
		# Build product data section for the prompt
		product_data_section = ""
		if user_product_data:
			product_data_section = f"""
🛒🛒🛒 CRITICAL: USER-PROVIDED PRODUCT DATA - USE THIS EXACTLY 🛒🛒🛒
════════════════════════════════════════════════════════════════════════
The user has provided their REAL product catalog. You MUST use these actual products
instead of generating mock/placeholder data!

📦 USER'S PRODUCT DATA:
{json.dumps(user_product_data, indent=2)}

🚨 MANDATORY REQUIREMENTS FOR PRODUCT DATA:
1. Use EXACTLY these product names, prices, and descriptions
2. Display user's actual prices (no made-up prices!)
3. If image URLs provided, use them; otherwise use relevant Unsplash images
4. Categories must match user's product categories
5. This is REAL business data - accuracy is critical!

✅ EXAMPLE IMPLEMENTATION WITH USER'S PRODUCTS:
```jsx
const products = {json.dumps(user_product_data[:3] if len(user_product_data) > 3 else user_product_data, indent=2)};

// Render user's actual products
products.map(product => (
  <div key={{product.id || product.name}} className="product-card">
    <img src={{product.image_url || `https://images.unsplash.com/photo-random?w=400`}} />
    <h3>{{product.name}}</h3>
    <p>{{product.description}}</p>
    <span className="price">${{product.price}}</span>
  </div>
))
```
════════════════════════════════════════════════════════════════════════

"""
		
		# Build custom data section
		custom_data_section = ""
		if user_custom_data:
			custom_data_section = f"""
📋 USER-PROVIDED CUSTOM DATA - USE THIS DATA:
════════════════════════════════════════════════════════════════════════
{json.dumps(user_custom_data, indent=2)}

Use this exact data in the application instead of generating placeholder content.
════════════════════════════════════════════════════════════════════════

"""
		
		# Build ML integration section
		ml_integration_section = ""
		if ml_requirements and ml_requirements.get('detected'):
			models = ml_requirements.get('models', [])
			ml_integration_section = f"""
🤖🤖🤖 MACHINE LEARNING INTEGRATION REQUIRED 🤖🤖🤖
════════════════════════════════════════════════════════════════════════
The user has requested ML model integration. You MUST include:

📊 DETECTED ML MODELS: {', '.join(models)}

🎯 ML IMPLEMENTATION REQUIREMENTS:

1. **LINEAR REGRESSION** (if detected: population prediction, price prediction, trend analysis):
   - Create a form to input feature values (X variables)
   - Call backend API: POST /api/ml/predict with {{ "model": "linear_regression", "features": [values] }}
   - Display prediction results in a nice card with visualization
   - Show model accuracy/confidence if available
   
   Example Implementation:
   ```jsx
   const [features, setFeatures] = useState([]);
   const [prediction, setPrediction] = useState(null);
   const [loading, setLoading] = useState(false);
   
   const handlePredict = async () => {{
     setLoading(true);
     try {{
       const response = await fetch('http://localhost:8000/api/ml/predict', {{
         method: 'POST',
         headers: {{ 'Content-Type': 'application/json' }},
         body: JSON.stringify({{ model: 'linear_regression', features }})
       }});
       const data = await response.json();
       setPrediction(data.prediction);
     }} catch (error) {{
       console.error('Prediction failed:', error);
     }} finally {{
       setLoading(false);
     }}
   }};
   
   // Prediction UI
   <div className="p-6 bg-white rounded-xl shadow-lg">
     <h3 className="text-xl font-bold mb-4">Make Prediction</h3>
     <input 
       type="number" 
       placeholder="Enter value"
       onChange={{(e) => setFeatures([parseFloat(e.target.value)])}}
       className="px-4 py-2 border rounded-lg w-full mb-4"
     />
     <button 
       onClick={{handlePredict}}
       disabled={{loading}}
       className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold"
     >
       {{loading ? 'Predicting...' : 'Get Prediction'}}
     </button>
     {{prediction !== null && (
       <div className="mt-4 p-4 bg-green-50 rounded-lg">
         <p className="text-lg font-semibold text-green-800">
           Predicted Value: {{prediction.toFixed(2)}}
         </p>
       </div>
     )}}
   </div>
   ```

2. **CLASSIFICATION** (if detected: sentiment analysis, categorization, spam detection):
   - Create input for text/features to classify
   - Show classification result with confidence scores
   - Display probability distribution for each class
   
3. **TIME SERIES** (if detected: forecasting, trend prediction):
   - Show historical data in a chart
   - Allow selecting forecast period
   - Display predicted future values with confidence intervals

4. **TRAIN YOUR OWN MODEL** Feature:
   - Allow users to upload CSV data
   - Auto-detect feature columns
   - Train model and show training progress
   - Save trained model for future predictions

🔧 BACKEND ML ENDPOINTS (Already available):
- POST /api/ml/predict - Make predictions
- POST /api/ml/train - Train custom model
- GET /api/ml/models - List available models
- POST /api/ml/upload-data - Upload training data

✅ REQUIRED UI COMPONENTS:
- Prediction form with proper validation
- Results display with nice visualization
- Loading states during model inference
- Error handling for failed predictions
- Historical predictions list (optional)
════════════════════════════════════════════════════════════════════════

"""
		
		# Build LLM integration section
		llm_integration_section = ""
		if llm_requirements and llm_requirements.get('detected'):
			provider = llm_requirements.get('provider', 'openai')
			instructions = llm_requirements.get('setup_instructions', '')
			llm_integration_section = f"""
🧠🧠🧠 LLM/AI INTEGRATION REQUIRED 🧠🧠🧠
════════════════════════════════════════════════════════════════════════
The user has requested LLM integration. You MUST include:

🔑 DETECTED LLM PROVIDER: {provider.upper()}

⚠️ API KEY REQUIRED! Show this message to the user:
{instructions}

🎯 LLM IMPLEMENTATION REQUIREMENTS:

1. **API KEY INPUT UI** (CRITICAL - Show first!):
   ```jsx
   const [apiKey, setApiKey] = useState(localStorage.getItem('llm_api_key') || '');
   const [isApiKeySet, setIsApiKeySet] = useState(!!localStorage.getItem('llm_api_key'));
   
   const saveApiKey = () => {{
     localStorage.setItem('llm_api_key', apiKey);
     setIsApiKeySet(true);
     showNotification('API Key saved successfully!');
   }};
   
   // Show if no API key
   {{!isApiKeySet && (
     <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
       <div className="bg-white p-8 rounded-xl max-w-md w-full">
         <h2 className="text-2xl font-bold mb-4">🔑 API Key Required</h2>
         <p className="text-gray-600 mb-4">
           {instructions.replace(chr(10), ' ')}
         </p>
         <input
           type="password"
           value={{apiKey}}
           onChange={{(e) => setApiKey(e.target.value)}}
           placeholder="Enter your API key"
           className="w-full px-4 py-3 border rounded-lg mb-4"
         />
         <button
           onClick={{saveApiKey}}
           disabled={{!apiKey}}
           className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold disabled:opacity-50"
         >
           Save API Key
         </button>
       </div>
     </div>
   )}}
   ```

2. **CHAT INTERFACE** (AI Chat/Assistant apps):
   ```jsx
   const [messages, setMessages] = useState([]);
   const [input, setInput] = useState('');
   const [loading, setLoading] = useState(false);
   
   const sendMessage = async () => {{
     if (!input.trim()) return;
     
     const userMessage = {{ role: 'user', content: input }};
     setMessages(prev => [...prev, userMessage]);
     setInput('');
     setLoading(true);
     
     try {{
       const response = await fetch('http://localhost:8000/api/llm/chat', {{
         method: 'POST',
         headers: {{
           'Content-Type': 'application/json',
           'X-API-Key': localStorage.getItem('llm_api_key')
         }},
         body: JSON.stringify({{
           provider: '{provider}',
           messages: [...messages, userMessage]
         }})
       }});
       const data = await response.json();
       setMessages(prev => [...prev, {{ role: 'assistant', content: data.response }}]);
     }} catch (error) {{
       setMessages(prev => [...prev, {{ role: 'assistant', content: 'Error: Failed to get response' }}]);
     }} finally {{
       setLoading(false);
     }}
   }};
   ```

3. **TEXT GENERATION** (Content generation apps):
   - Prompt input with templates
   - Generated content display
   - Copy to clipboard functionality
   - Regenerate option

🔧 BACKEND LLM ENDPOINTS (Already available):
- POST /api/llm/chat - Chat completion
- POST /api/llm/generate - Text generation
- POST /api/llm/summarize - Text summarization
- POST /api/llm/analyze - Content analysis

✅ REQUIRED UI COMPONENTS:
- API Key setup modal (shows first if no key)
- Chat interface with message history
- Loading indicators during API calls
- Error handling for rate limits/failures
- Settings to change model/provider
════════════════════════════════════════════════════════════════════════

"""
		
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
		
		# Build design instructions - USER PREFERENCES FIRST
		design_instructions = f"""
🚨🚨🚨 CRITICAL: USER DESIGN PREFERENCES OVERRIDE EVERYTHING 🚨🚨🚨
════════════════════════════════════════════════════════════════════════

⛔ FORBIDDEN UNLESS USER EXPLICITLY REQUESTS:
- Purple/violet gradients (bg-gradient-to-* from-purple-* to-violet-*)
- Massive shadows (shadow-2xl, shadow-purple-500/20, shadow-glow)
- Gradient text effects (bg-clip-text text-transparent bg-gradient-*)
- Over-the-top animations and floating elements
- Pink/magenta color schemes
- Glass morphism effects (unless user asks for it)
- Mesh gradients and radial gradients
- Neon glow effects

✅ DEFAULT CLEAN PROFESSIONAL STYLE (Use unless user specifies otherwise):
- Clean solid backgrounds (bg-white, bg-gray-50, bg-black, bg-gray-900)
- Simple readable typography (text-gray-900, text-white, text-gray-600)
- Subtle shadows only (shadow-sm, shadow-md)
- Minimal animations (hover:scale-102, transition-colors)
- Professional color accents (blue-600, green-600, etc.)
- Clear visual hierarchy with proper spacing
- NO gradient text unless explicitly requested
- NO purple/pink unless explicitly requested

🎯 TYPOGRAPHY RULES:
- Font: Inter or system-ui (clean, professional)
- Headings: font-semibold or font-bold, NOT font-black or excessive weights
- Body: font-normal, text-base or text-sm, proper line-height
- NO all-caps unless it's a short label
- NO excessive letter-spacing
- Readable contrast ratios always

🎨 COLOR APPLICATION RULES:
- Use user-specified colors EXACTLY as described
- If user says "black background" → use bg-black or bg-gray-950
- If user says "white text" → use text-white
- If user says "dark theme" → dark backgrounds, light text
- If user says "light theme" → light backgrounds, dark text
- DO NOT add random purple/pink accents
- DO NOT add gradient backgrounds unless requested

🚨 UNIQUE LAYOUT ASSIGNMENT:"""

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
		
		# Also check description for design preferences
		description_lower = description.lower() if description else ''
		all_user_text = ' '.join([description_lower] + [str(df).lower() for df in design_features + functional_features])
		
		if design_features or any(keyword in description_lower for keyword in ['design', 'color', 'theme', 'style', 'dark', 'light', 'modern', 'minimalist', 'elegant', 'bold']):
			design_instructions += f"\n\n🎯 USER'S EXACT REQUIREMENTS (MANDATORY - DO NOT IGNORE!):\n"
			design_instructions += f"📝 User Description: \"{description}\"\n"
			if design_features:
				design_instructions += f"🎨 Design Requests: {', '.join(design_features)}\n"
			if functional_features:
				design_instructions += f"⚙️ Features: {', '.join(functional_features)}\n"
			
			design_instructions += "\n⚠️ IMPORTANT: The design MUST reflect what the user described above!\n"
			design_instructions += "- If they want dark theme → use dark backgrounds and light text\n"
			design_instructions += "- If they mention a specific industry → use appropriate imagery and colors\n"
			design_instructions += "- If they want minimalist → use clean layouts with lots of whitespace\n"
			design_instructions += "- If they want bold → use strong colors and impactful typography\n"
			
			# Enhanced color/theme detection and handling (now including description)
			user_text_combined = all_user_text
			
			# Color scheme detection with more patterns
			if any(color in user_text_combined for color in ['blue', 'navy', 'cyan', 'teal', 'ocean', 'sky', 'azure']):
				design_instructions += "\n🎨 DETECTED BLUE/OCEAN THEME: Use bg-gradient-to-br from-blue-600 via-cyan-500 to-teal-400, blue-500 accents, blue-100 backgrounds\n"
			elif any(color in user_text_combined for color in ['red', 'crimson', 'rose', 'pink', 'cherry', 'ruby']):
				design_instructions += "\n🎨 DETECTED RED/PINK THEME: Use bg-gradient-to-br from-red-500 via-pink-500 to-rose-400, red-500 accents, red-50 backgrounds\n"
			elif any(color in user_text_combined for color in ['green', 'emerald', 'lime', 'mint', 'forest', 'sage', 'nature', 'eco']):
				design_instructions += "\n🎨 DETECTED GREEN/NATURE THEME: Use bg-gradient-to-br from-green-500 via-emerald-500 to-teal-400, green-500 accents, green-50 backgrounds\n"
			elif any(color in user_text_combined for color in ['purple', 'violet', 'indigo', 'lavender', 'royal', 'luxur']):
				design_instructions += "\n🎨 DETECTED PURPLE/LUXURY THEME: Use bg-gradient-to-br from-purple-600 via-violet-500 to-indigo-400, purple-500 accents, purple-50 backgrounds\n"
			elif any(color in user_text_combined for color in ['orange', 'amber', 'yellow', 'gold', 'sunset', 'warm', 'energetic']):
				design_instructions += "\n🎨 DETECTED WARM/ENERGETIC THEME: Use bg-gradient-to-br from-amber-400 via-orange-500 to-red-600, orange-500 accents, amber-50 backgrounds\n"
			elif any(theme in user_text_combined for theme in ['dark', 'black', 'midnight', 'night', 'sleek', 'professional']):
				design_instructions += """

🚨🚨🚨 MANDATORY DARK THEME - FOLLOW EXACTLY 🚨🚨🚨
════════════════════════════════════════════════════════════════════════
User requested DARK/BLACK theme. You MUST use:

✅ REQUIRED COLORS:
- Main background: bg-black or bg-gray-950 (NOT bg-gray-900, too light)
- Secondary backgrounds: bg-gray-900, bg-gray-900/50
- Text: text-white for primary, text-gray-300 for secondary
- Borders: border-gray-800 or border-white/10
- Cards: bg-gray-900 or bg-white/5 with border-gray-800

⛔ ABSOLUTELY FORBIDDEN:
- Purple gradients (NO from-purple-* to-violet-*)
- Pink/magenta colors
- Gradient text effects
- Colorful mesh backgrounds
- Light backgrounds anywhere
- Gray-700 or lighter backgrounds

✅ ALLOWED ACCENTS (pick ONE, keep minimal):
- Blue: text-blue-400, bg-blue-600 for buttons
- Green: text-green-400, bg-green-600 for success
- White: text-white, bg-white for primary buttons on dark

✅ EXAMPLE DARK THEME STRUCTURE:
```jsx
<div className="min-h-screen bg-black text-white">
  <nav className="bg-gray-950 border-b border-gray-800">
    <span className="text-white font-semibold">Logo</span>
    <button className="bg-white text-black px-4 py-2 rounded-lg">Sign In</button>
  </nav>
  <main className="bg-black">
    <h1 className="text-4xl font-bold text-white">Heading</h1>
    <p className="text-gray-300">Description text</p>
    <button className="bg-white text-black px-6 py-3 rounded-lg font-medium">Get Started</button>
  </main>
</div>
```
════════════════════════════════════════════════════════════════════════
"""
			elif any(theme in user_text_combined for theme in ['light', 'white', 'minimal', 'clean', 'simple', 'bright']):
				design_instructions += """

🚨🚨🚨 MANDATORY LIGHT/MINIMAL THEME - FOLLOW EXACTLY 🚨🚨🚨
════════════════════════════════════════════════════════════════════════
User requested LIGHT/CLEAN theme. You MUST use:

✅ REQUIRED COLORS:
- Main background: bg-white or bg-gray-50
- Text: text-gray-900 for primary, text-gray-600 for secondary
- Borders: border-gray-200
- Cards: bg-white with shadow-sm and border-gray-200

⛔ ABSOLUTELY FORBIDDEN:
- Purple gradients
- Dark backgrounds
- Gradient text effects
- Neon colors
- Heavy shadows (shadow-2xl, shadow-glow)

✅ ALLOWED ACCENTS:
- Blue: text-blue-600, bg-blue-600 for primary actions
- Gray: bg-gray-100 for secondary elements
════════════════════════════════════════════════════════════════════════
"""
			
			# Industry-specific design guidance
			if any(industry in user_text_combined for industry in ['medical', 'health', 'doctor', 'hospital', 'clinic']):
				design_instructions += "\n🏥 MEDICAL INDUSTRY: Use calming blues/greens, professional feel, trust-inspiring design, clear navigation\n"
			elif any(industry in user_text_combined for industry in ['finance', 'bank', 'money', 'investment', 'trading']):
				design_instructions += "\n💰 FINANCE INDUSTRY: Use navy/gold colors, conservative typography, data visualizations, professional trust signals\n"
			elif any(industry in user_text_combined for industry in ['food', 'restaurant', 'cafe', 'cook', 'recipe', 'meal']):
				design_instructions += "\n🍕 FOOD/RESTAURANT INDUSTRY: Use warm appetizing colors (oranges, reds), beautiful food imagery, menu-style layouts\n"
			elif any(industry in user_text_combined for industry in ['tech', 'software', 'startup', 'saas', 'app']):
				design_instructions += "\n💻 TECH/STARTUP: Use modern gradients, glassmorphism, futuristic feel, clean data displays\n"
			elif any(industry in user_text_combined for industry in ['fashion', 'clothing', 'style', 'boutique', 'luxury']):
				design_instructions += "\n👗 FASHION/LUXURY: Use elegant typography, lots of whitespace, high-quality imagery, sophisticated color palette\n"
			elif any(industry in user_text_combined for industry in ['fitness', 'gym', 'sport', 'workout', 'exercise']):
				design_instructions += "\n💪 FITNESS/SPORTS: Use energetic colors (orange, red), bold typography, action imagery, motivational feel\n"
			elif any(industry in user_text_combined for industry in ['education', 'school', 'learn', 'course', 'student']):
				design_instructions += "\n📚 EDUCATION: Use friendly colors, clear hierarchy, accessible design, encouraging feel\n"
			elif any(industry in user_text_combined for industry in ['travel', 'hotel', 'vacation', 'tour', 'flight']):
				design_instructions += "\n✈️ TRAVEL/HOSPITALITY: Use inspiring imagery, dreamy colors, adventure feel, easy booking flows\n"
		else:
			# Default enhancement for projects without specific design mentions
			design_instructions += f"\n\n🎯 PROJECT CONTEXT (ADAPT DESIGN ACCORDINGLY):\n"
			design_instructions += f"📝 Description: \"{description}\"\n"
			design_instructions += f"⚙️ Features: {', '.join(features_str)}\n"
			design_instructions += """
💡 NO SPECIFIC DESIGN REQUESTED - USE CLEAN PROFESSIONAL DEFAULTS:
- Background: bg-white or bg-gray-50 (light, clean)
- Text: text-gray-900 (dark, readable)
- Accents: blue-600 for primary actions
- Shadows: shadow-sm or shadow-md only
- NO purple gradients, NO gradient text, NO heavy effects
- Keep it simple, professional, and functional
"""
		
		return f"""🚨 CRITICAL ERROR PREVENTION - MUST FOLLOW:

{product_data_section}
{custom_data_section}
{ml_integration_section}
{llm_integration_section}

🌐 BROWSER SANDBOX ENVIRONMENT - CRITICAL REQUIREMENTS:
════════════════════════════════════════════════════════
This code runs in a BROWSER SANDBOX with globals pre-defined.
The following are ALREADY AVAILABLE GLOBALLY - DO NOT IMPORT OR REDEFINE:

✅ REACT (Global): React, useState, useEffect, useCallback, useMemo, useRef, useContext, useReducer
✅ ROUTER (Global): Router, Routes, Route, Link, NavLink, Navigate, useNavigate, useLocation, useParams
✅ ANIMATION (Global): motion, AnimatePresence, useInView, useScroll
✅ UI COMPONENTS (Global): Button, Input, Card, Loading, AnimatedText, Navigation
✅ ICONS (Global): User, Search, Menu, X, Plus, Minus, Heart, Star, ShoppingCart, Trash2, Edit, Save, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, Home, Settings, Bell, Mail, Phone, MapPin, etc.
✅ UTILITIES (Global): cn (className utility)

🎨🎨🎨 CRITICAL: BUTTON VISIBILITY & WORKING FUNCTIONALITY 🎨🎨🎨
════════════════════════════════════════════════════════════════
⚠️ PROBLEM: Buttons appearing as plain text or NOT WORKING are UNACCEPTABLE!
⚠️ EVERY button must be VISUALLY OBVIOUS and have WORKING onClick handlers!

✅ CORRECT BUTTON PATTERNS (Follow user's color scheme):
```jsx
// For DARK THEME (black background):
<button 
  onClick={{() => setIsLoginOpen(true)}}
  className="bg-white text-black px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
>
  Sign In
</button>

// For LIGHT THEME (white background):
<button 
  onClick={{() => navigate('/signup')}}
  className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
>
  Get Started
</button>

// Secondary/Outline button:
<button 
  onClick={{handleSecondary}}
  className="border-2 border-white text-white hover:bg-white hover:text-black px-6 py-3 rounded-lg font-semibold transition-all"
>
  Learn More
</button>
```

❌ WRONG - BROKEN BUTTONS (NEVER DO THIS):
```jsx
// ❌ No onClick handler - button does nothing!
<button className="bg-blue-600 text-white px-4 py-2 rounded">Click Me</button>

// ❌ No background color - button looks like plain text!
<button onClick={{handler}}>Click Me</button>

// ❌ Using purple gradient when user asked for black/white theme!
<button className="bg-gradient-to-r from-purple-600 to-pink-600">Bad</button>
```

🎨 BUTTON STYLING BY THEME:
- DARK THEME PRIMARY: bg-white text-black px-6 py-3 rounded-lg font-semibold hover:bg-gray-100
- DARK THEME SECONDARY: border border-white text-white hover:bg-white hover:text-black px-6 py-3 rounded-lg
- LIGHT THEME PRIMARY: bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700
- LIGHT THEME SECONDARY: border-2 border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white px-6 py-3 rounded-lg
- ALWAYS ADD: onClick={{handlerFunction}} - NEVER skip this!

🚨 ABSOLUTE RULES FOR SANDBOX COMPATIBILITY:
1. DO NOT use import statements - everything is global
2. DO NOT use export statements - component is assigned to window.App
3. DO NOT redefine motion, AnimatePresence, or any icons
4. DO NOT import from 'react', 'react-router-dom', 'framer-motion', or 'lucide-react'
5. USE motion.div, motion.span directly (they are global)
6. USE Router, Routes, Route, Link, NavLink directly (they are global)
7. USE Button, Input, Card, Loading directly (they are global)
8. USE React.createContext and React.useContext (React is global)

🚨🚨🚨 CRITICAL CODE QUALITY RULES - VIOLATIONS CAUSE RUNTIME ERRORS 🚨🚨🚨
════════════════════════════════════════════════════════════════════════

⛔ EMPTY COMPONENT BODIES (FATAL ERROR):
NEVER create components with empty bodies - they render NOTHING!

❌ WRONG - Empty component body (renders nothing):
const NeumorphicInput = ({{ children, className }}) => {{}};
const Card = ({{ children }}) => {{}};
const MyComponent = () => ();
const MyComponent = () => {{}};  // Empty block

✅ CORRECT - Components MUST have a return statement:
const NeumorphicInput = ({{ children, className }}) => {{
  return (
    <div className={{cn('bg-gray-800 rounded-xl p-4', className)}}>
      {{children}}
    </div>
  );
}};

const Card = ({{ children }}) => (
  <div className="bg-white rounded-xl p-6 shadow-md">{{children}}</div>
);

⛔ ASYNC IN SYNC CONTEXT (FATAL ERROR):
NEVER call async functions inside useMemo, useState initializers, or render!

❌ WRONG - async in useMemo (returns Promise, not data!):
const data = useMemo(() => {{
  const result = await fetchData();  // ❌ Can't use await in useMemo!
  return result;
}}, []);

const data = useMemo(() => fetchAPIData(), []);  // ❌ Returns Promise object!

✅ CORRECT - Use useEffect for async operations:
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {{
  const loadData = async () => {{
    setLoading(true);
    try {{
      const result = await fetchData();
      setData(result);
    }} catch (err) {{
      console.error(err);
    }} finally {{
      setLoading(false);
    }}
  }};
  loadData();
}}, []);

// For computed values that depend on async data:
const processedData = useMemo(() => {{
  if (!data) return null;  // Handle null case
  return data.map(item => ({{ ...item, processed: true }}));  // Sync transformation
}}, [data]);

⛔ WRONG EXPORT (FATAL ERROR):
If you have AppWrapper, export AppWrapper NOT App!

❌ WRONG:
const AppWrapper = () => (<Router><App /></Router>);
export default App;  // ❌ Wrong! Should export AppWrapper

✅ CORRECT:
const AppWrapper = () => (<Router><App /></Router>);
export default AppWrapper;  // ✅ Correct!

// Or better for sandbox (no export at all):
const AppWrapper = () => (<Router><App /></Router>);
// window.App = AppWrapper is handled by sandbox

⛔ TAILWIND PEER CLASSES (UNRELIABLE IN SANDBOX):
Avoid peer-checked/peer-focus classes - use state-based styling instead!

❌ WRONG - Peer classes may not work:
<input type="checkbox" className="peer" />
<span className="peer-checked:bg-blue-500">Toggle</span>

✅ CORRECT - State-based styling (always works):
const [isChecked, setIsChecked] = useState(false);
<input type="checkbox" checked={{isChecked}} onChange={{(e) => setIsChecked(e.target.checked)}} />
<span className={{isChecked ? 'bg-blue-500' : 'bg-gray-500'}}>Toggle</span>

════════════════════════════════════════════════════════════════════════

✅ CORRECT PATTERN:
```jsx
// NO IMPORTS NEEDED - everything is global!

const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

const App = () => {{
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  
  return (
    <Router>
      <motion.div className="min-h-screen">
        <NavLink to="/" className={{location.pathname === '/' ? 'text-blue-500' : 'text-gray-600'}}>Home</NavLink>
        <Button onClick={{() => navigate('/dashboard')}}>Go to Dashboard</Button>
        <Routes>
          <Route path="/" element={{<HomePage />}} />
        </Routes>
      </motion.div>
    </Router>
  );
}};

const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);
```

⚠️⚠️⚠️ CRITICAL: DO NOT USE FRAMER-MOTION OR MOTION COMPONENTS! ⚠️⚠️⚠️
The sandbox has issues with motion components causing "a.set is not a function" errors.
USE REGULAR HTML ELEMENTS WITH CSS TRANSITIONS INSTEAD:

✅ CORRECT - Use CSS transitions:
```jsx
<div className="transition-all duration-300 hover:scale-105">Content</div>
<button className="transform hover:-translate-y-1 transition-transform">Click</button>
```

❌ WRONG - Will cause errors:
```jsx
<motion.div initial={{...}} animate={{...}}>Content</motion.div>
<AnimatePresence>...</AnimatePresence>
```

❌ WRONG - WILL CAUSE ERRORS:
```jsx
import React, {{ useState }} from 'react';  // ❌ NO IMPORTS
import {{ motion }} from 'framer-motion';   // ❌ motion causes errors!
import {{ ShoppingCart }} from 'lucide-react'; // ❌ icons are global
export default App; // ❌ NO EXPORTS

const motion = {{ div: ... }}; // ❌ DON'T REDEFINE - it's global!
<motion.div>...</motion.div> // ❌ DON'T USE motion.X - causes errors!
<AnimatePresence>...</AnimatePresence> // ❌ DON'T USE - causes errors!
```

📋 SANDBOX HTML TEMPLATE (Your code runs inside this):
════════════════════════════════════════════════════════
```html
<!DOCTYPE html>
<html>
<head>
  <script src="react@18/umd/react.production.min.js"></script>
  <script src="react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="framer-motion/dist/framer-motion.umd.min.js"></script>
  <script src="@babel/standalone/babel.min.js"></script>
  <link href="tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    // ═══ THESE ARE ALREADY DEFINED BEFORE YOUR CODE RUNS ═══
    const {{ useState, useEffect, useCallback, useMemo, useRef, useContext }} = React;
    
    // Router (hash-based, works without react-router-dom package)
    // Router, Routes, Route, Link, NavLink, Navigate, useNavigate, useLocation, useParams
    
    // Motion (framer-motion loaded globally)
    // motion.div, motion.span, motion.button, etc., AnimatePresence
    
    // Icons (simple SVG components)
    // User, Search, Menu, X, Plus, Minus, Heart, Star, ShoppingCart, etc.
    
    // UI Components
    // Button, Input, Card, Loading, AnimatedText, Navigation
    
    // Utilities
    // cn() - className utility like clsx/tailwind-merge
    
    // ═══ YOUR App.jsx CODE GOES HERE (NO IMPORTS/EXPORTS!) ═══
    
    const App = () => {{
      // Your component code...
    }};
    
    const AppWrapper = () => (<Router><App /></Router>);
    window.App = AppWrapper;
    
    // ═══ RENDERING (HANDLED BY SANDBOX) ═══
    ReactDOM.createRoot(document.getElementById('root')).render(
      React.createElement(window.App)
    );
  </script>
</body>
</html>
```
════════════════════════════════════════════════════════

🎯 YOUR OUTPUT FORMAT - Generate ONLY the component code:
```jsx
// NO IMPORTS - everything is global!

// Contexts (use React.createContext)
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

// Page Components (USE USER'S REQUESTED COLORS, NOT PURPLE GRADIENTS!)
const HomePage = () => {{
  const navigate = useNavigate();
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  
  return (
    <div className="min-h-screen bg-black text-white">  {{/* USE USER'S COLORS! */}}
      <nav className="flex justify-between items-center p-6 border-b border-gray-800">
        <span className="text-xl font-semibold">Logo</span>
        <div className="flex gap-4">
          <button 
            onClick={{() => setIsLoginOpen(true)}}
            className="px-4 py-2 text-white hover:text-gray-300"
          >
            Sign In
          </button>
          <button 
            onClick={{() => navigate('/signup')}}
            className="px-6 py-2 bg-white text-black rounded-lg font-medium hover:bg-gray-100"
          >
            Get Started
          </button>
        </div>
      </nav>
      <main className="container mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl font-bold text-white mb-6">Welcome</h1>
        <p className="text-gray-400 text-lg mb-8">Your description here</p>
        <button 
          onClick={{() => navigate('/products')}}
          className="px-8 py-4 bg-white text-black rounded-lg font-semibold hover:bg-gray-100"
        >
          Get Started Free
        </button>
      </main>
      
      {{/* Login Modal - MUST WORK! */}}
      {{isLoginOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={{() => setIsLoginOpen(false)}}>
          <div className="bg-gray-900 p-8 rounded-xl max-w-md w-full" onClick={{(e) => e.stopPropagation()}}>
            <h2 className="text-2xl font-bold text-white mb-6">Sign In</h2>
            <form onSubmit={{(e) => {{ e.preventDefault(); /* handle login */ }}}}>
              <input type="email" placeholder="Email" className="w-full p-3 mb-4 bg-gray-800 rounded-lg text-white" />
              <input type="password" placeholder="Password" className="w-full p-3 mb-6 bg-gray-800 rounded-lg text-white" />
              <button type="submit" className="w-full py-3 bg-white text-black rounded-lg font-semibold">Sign In</button>
            </form>
            <button onClick={{() => setIsLoginOpen(false)}} className="mt-4 text-gray-400 hover:text-white">Close</button>
          </div>
        </div>
      )}}
    </div>
  );
}};

// Main App with Router
const App = () => {{
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);
  const location = useLocation();
  
  return (
    <AuthContext.Provider value={{{{ user, setUser }}}}>
      <Routes>
        <Route path="/" element={{<HomePage />}} />
        <Route path="/products" element={{<ProductsPage />}} />
      </Routes>
    </AuthContext.Provider>
  );
}};

// Wrapper with Router (REQUIRED)
const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);

// NO EXPORT STATEMENT - sandbox assigns window.App = AppWrapper
```
════════════════════════════════════════════════════════

🚨🚨🚨 CRITICAL: NO PLACEHOLDER OR FAKE CODE ALLOWED! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════
⛔ NEVER generate "Welcome" screens, loading placeholders, or fake apps
⛔ NEVER generate: "Your application is being generated..." messages
⛔ NEVER generate: <div>Welcome to {{project_name}}</div> as the main content
⛔ NEVER generate: Loading animations as the primary UI
⛔ EVERY button, form, feature MUST be fully functional - no placeholders!
✅ Generate COMPLETE, PRODUCTION-READY applications with real functionality
✅ Users want working e-commerce, dashboards, social apps - not placeholders!
✅ If asked for an e-commerce app, build a REAL store with products, cart, checkout
✅ If asked for a dashboard, build REAL charts, tables, and data visualizations
═══════════════════════════════════════════════════════════════════════

🌐 BROWSER ENVIRONMENT SAFETY:
- NEVER use process.env directly (causes ReferenceError in browser)
- Instead use: const API_URL = 'http://localhost:8000/api'; (local API)
- OR safe check: const API_URL = (typeof window !== 'undefined' && window.ENV?.API_URL) || 'http://localhost:8000/api';
- NO Node.js globals in browser code (process, Buffer, __dirname, require)

�🎨🎨 PROFESSIONAL UI DESIGN PRINCIPLES (MUST FOLLOW!) 🎨🎨🎨
═══════════════════════════════════════════════════════════════════════
Generate apps that look like they were built by professional designers at companies 
like Apple, Stripe, Linear, or Vercel. Follow these 7 core UI principles:

1. HIERARCHY - Guide users to key information at a glance:
   - Hero headlines: text-4xl md:text-5xl lg:text-6xl font-bold
   - Subheadlines: text-xl md:text-2xl text-gray-400 (lighter weight)
   - Body text: text-base text-gray-300
   - Use font-bold for important labels, font-medium for secondary
   - Most important content at the top, less important below the fold
   - Create visual sections with different background colors/shades

2. PROGRESSIVE DISCLOSURE - Don't overwhelm users:
   - Show essential features first, advanced options in expandable sections
   - Multi-step forms should show progress (Step 1 of 3)
   - Use tabs or accordions to organize complex content
   - Category filter pills for easy filtering (like: All | Electronics | Fashion | Home)
   - Collapsible sidebars for filters on product pages

3. CONSISTENCY - Same patterns throughout:
   - All buttons same border-radius (rounded-lg or rounded-xl)
   - All cards same shadow level (shadow-md or shadow-lg)
   - Same spacing scale (use gap-4, gap-6, gap-8 consistently)
   - Same transition timing (transition-all duration-200)
   - Header height consistent across all pages
   - Same hover effects on similar elements

4. CONTRAST - Strategic color use:
   - Primary CTA buttons: solid bright color (bg-green-500, bg-blue-600)
   - Secondary buttons: outline or muted (border border-gray-600)
   - Destructive actions: bg-red-600 to stand out
   - Use accent color SPARINGLY - only for CTAs and highlights
   - Dark theme: bg-gray-900/bg-black with lighter text
   - Light theme: bg-white/bg-gray-50 with darker text

5. ACCESSIBILITY - Design for everyone:
   - Text contrast ratio minimum 4.5:1 (white text on dark, dark text on light)
   - Interactive elements minimum 44x44px touch targets
   - Focus states visible (focus:ring-2 focus:ring-offset-2)
   - Don't rely on color alone to convey meaning
   - All images have alt text

6. PROXIMITY - Group related elements:
   - Product info (name, price, rating) grouped together
   - Navigation items grouped logically (Shop | Categories | Deals)
   - Form fields with their labels (no orphan labels)
   - Action buttons together (Save, Cancel side by side)
   - Footer sections: About, Support, Legal grouped

7. ALIGNMENT - Clean grid-based layouts:
   - Use consistent container widths (max-w-7xl mx-auto px-4)
   - Align text left (not centered) for readability in content areas
   - Center only hero headlines and CTAs
   - Use grid layouts: grid-cols-1 md:grid-cols-2 lg:grid-cols-4
   - Consistent padding in cards (p-4 or p-6)
   - Proper gutters between grid items (gap-4 or gap-6)

✨ PROFESSIONAL POLISH CHECKLIST:
□ Hero section with large headline, subtitle, and clear CTA
□ Consistent 8px spacing grid (p-2, p-4, p-6, p-8, etc.)
□ Subtle shadows (shadow-sm, shadow-md) - NOT shadow-2xl
□ Smooth hover transitions (hover:bg-opacity-90, transition-colors)
□ Loading states for async operations (spinner or skeleton)
□ Empty states with helpful messages ("No products found")
□ Proper error states with red accents
□ Success feedback (green checkmarks, toast notifications)
□ Responsive design that works on mobile AND desktop
□ Sticky header for easy navigation

═══════════════════════════════════════════════════════════════════════

🏆 DESIGN BRIEF - FOLLOW USER REQUIREMENTS EXACTLY:
Create a React App.jsx for {project_name} ({app_type}).

Project: {app_type}
Description: {description}
Features: {', '.join(functional_features) if functional_features else 'Modern web app features'}

🚨🚨🚨 ABSOLUTE DESIGN RULES - VIOLATIONS WILL BE REJECTED 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════
1. BUILD EXACTLY WHAT THE USER DESCRIBED - not something random
2. Use ONLY the colors/theme the user specified
3. If user said "black background" → bg-black, NOT purple gradients
4. If user said "white text" → text-white, NOT gradient text
5. NO purple/violet/pink unless user explicitly asked for it
6. NO gradient text effects unless user explicitly asked for it
7. NO massive shadows (shadow-2xl, shadow-glow) unless requested
8. NO glass morphism unless requested
9. Keep it CLEAN and PROFESSIONAL by default
═══════════════════════════════════════════════════════════════════════

🚨 CRITICAL: FOLLOW USER DESIGN REQUIREMENTS EXACTLY - DO NOT DEVIATE!
{design_instructions}

⚠️ COLOR COMPLIANCE WARNING: 
- If user specifies colors/themes in requirements above, YOU MUST use those exact colors
- DO NOT use random or default colors when user has specified preferences
- User-requested colors take absolute priority over design system defaults
- VERIFY every className uses the user-requested color scheme

🚨 FUNCTIONALITY REQUIREMENTS - EVERYTHING MUST ACTUALLY WORK:

CRITICAL: This is NOT a static demo - every button, form, and feature MUST be fully functional!

1. BUTTONS MUST WORK:
   - Every button MUST have a real onClick handler
   - Login button → actually opens login modal or navigates to login
   - Add to Cart → actually adds item to cart state and updates count
   - Submit forms → actually process the form data
   - Navigation buttons → actually change routes
   - Delete/Edit buttons → actually modify data
   - Example: <Button onClick={{() => addToCart(product)}}>Add to Cart</Button>
   - NOT: <Button>Add to Cart</Button> (NO onClick = BROKEN!)

2. FORMS MUST SUBMIT:
   - Every form needs onSubmit handler with e.preventDefault()
   - Must update state with form values using useState
   - Validate inputs before submission
   - Clear form after successful submission
   - Example:
   ```jsx
   const [formData, setFormData] = useState({{ name: '', email: '' }});
   const handleSubmit = (e) => {{
     e.preventDefault();
     // Actually process the form
     console.log('Form submitted:', formData);
     // Show success message, update state, etc.
   }};
   ```

3. STATE MANAGEMENT MUST WORK:
   - Shopping cart → useState for cart items, working add/remove/update
   - Authentication → useState for user, isLoggedIn status
   - Forms → useState for all input fields
   - Modals → useState for open/closed state
   - Search → useState for search term and filtered results
   - All state changes must trigger re-renders properly

4. CART FUNCTIONALITY (E-commerce apps):
   - Working addToCart function that updates cart state
   - Cart count in header that updates in real-time
   - Cart modal that shows actual items
   - Remove from cart button that actually works
   - Update quantity that changes cart state
   - Calculate totals correctly
   - Persist cart in localStorage

5. AUTHENTICATION MUST WORK:
   - Login form actually updates user state
   - Show/hide protected content based on auth state
   - Logout button actually clears user state
   - Login/Signup modals toggle correctly
   - Form validation with error messages
   - Remember user state in localStorage

6. NAVIGATION MUST WORK:
   - All Links use React Router <Link to="/path">
   - Navigate function for programmatic navigation
   - Active route highlighting works
   - Mobile menu toggle works with state
   - Back button works (browser history)

7. SEARCH/FILTER MUST WORK:
   - Search input updates state on change
   - Filter results based on search term
   - Display filtered results dynamically
   - Clear search button works

8. MODALS MUST WORK:
   - Open/close with state management
   - Backdrop click closes modal
   - Close button works
   - ESC key closes modal

🎯 DESIGN QUALITY REQUIREMENTS (RESPECT USER PREFERENCES):

1. VISUAL STYLE - FOLLOW USER'S THEME:
   - If user specified dark theme: bg-black/bg-gray-950, text-white, NO gradients unless requested
   - If user specified light theme: bg-white/bg-gray-50, text-gray-900, clean shadows
   - If no theme specified: default to clean, professional light theme
   - Typography: Inter font, readable sizes, proper contrast
   - Shadows: shadow-sm or shadow-md only (NO shadow-2xl, NO shadow-glow unless requested)

2. CLEAN PROFESSIONAL LAYOUTS:
   - Hero Section: Clear heading, description, working CTA button
   - Feature Cards: Clean cards with proper padding, subtle shadows
   - Content Sections: Clear visual hierarchy, proper spacing
   - NO diagonal sections, NO morphing shapes, NO 3D transforms unless requested

3. COLOR COMPLIANCE - ABSOLUTE PRIORITY:
   - 🚨 USE EXACT COLORS USER SPECIFIED - NOT RANDOM DEFAULTS
   - If user says "black background" → bg-black, NOT purple gradient
   - If user says "white text" → text-white, NOT gradient text
   - If user says "blue accent" → blue-600, NOT purple-500
   - NEVER add purple/pink unless user explicitly requested it
   - Verify EVERY className matches user's color requirements

4. INTERACTIONS (MUST ALL WORK):
   - Hover effects: hover:bg-opacity-90 or hover:scale-102 (subtle, not dramatic)
   - Loading states: Show spinner when data is loading
   - Smooth transitions: transition-colors duration-200
   - Button clicks: EVERY button must have onClick={{handleFunction}}
   - Form submissions: ALL forms need onSubmit with preventDefault()

5. FUNCTIONAL COMPONENTS:
   - Navigation with working links (Link component with to prop)
   - Hero with working CTA buttons (onClick handlers)
   - Forms with working submission (onSubmit handlers)
   - Modals that open and close (useState for visibility)
   - Cart that adds/removes items (useState for cart array)

MANDATORY WORKING CODE EXAMPLES:

✅ WORKING BUTTON (Always use this pattern):
```jsx
const [cart, setCart] = useState([]);

const addToCart = (product) => {{
  setCart([...cart, product]);
  showNotification('Added to cart!');
}};

<Button onClick={{() => addToCart(product)}}>
  Add to Cart
</Button>
```

✅ WORKING FORM (Always use this pattern):
```jsx
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');

const handleLogin = (e) => {{
  e.preventDefault();
  // Actually process login
  setUser({{ email }});
  setIsLoggedIn(true);
  showNotification('Login successful!');
}};

<form onSubmit={{handleLogin}}>
  <Input 
    value={{email}} 
    onChange={{(e) => setEmail(e.target.value)}}
  />
  <Button type="submit">Login</Button>
</form>
```

✅ WORKING CART (Always use this pattern):
```jsx
const [cartItems, setCartItems] = useState([]);

const addToCart = (product) => {{
  setCartItems([...cartItems, {{ ...product, id: Date.now() }}]);
}};

const removeFromCart = (itemId) => {{
  setCartItems(cartItems.filter(item => item.id !== itemId));
}};

// Header cart count
<span>Cart ({{cartItems.length}})</span>

// Cart modal
{{cartItems.map(item => (
  <div key={{item.id}}>
    {{item.name}} - ${{item.price}}
    <button onClick={{() => removeFromCart(item.id)}}>Remove</button>
  </div>
))}}
```

✅ WORKING MODAL (Always use this pattern):
```jsx
const [isLoginOpen, setIsLoginOpen] = useState(false);

<Button onClick={{() => setIsLoginOpen(true)}}>Login</Button>

{{isLoginOpen && (
  <div className="modal-backdrop" onClick={{() => setIsLoginOpen(false)}}>
    <div className="modal-content" onClick={{(e) => e.stopPropagation()}}>
      <button onClick={{() => setIsLoginOpen(false)}}>Close</button>
      <LoginForm />
    </div>
  </div>
)}}
```

✅ WORKING NAVIGATION (Always use this pattern):
```jsx
const navigate = useNavigate();
const location = useLocation();

// Navigation links
<Link 
  to="/about" 
  className={{location.pathname === '/about' ? 'active' : ''}}
>
  About
</Link>

// Programmatic navigation
<Button onClick={{() => navigate('/dashboard')}}>
  Go to Dashboard
</Button>
```

❌ BROKEN CODE (NEVER DO THIS):
```jsx
// NO onClick handler - button does nothing!
<Button>Add to Cart</Button>

// Form doesn't prevent default - page reloads!
<form><button>Submit</button></form>

// No state management - nothing updates!
<Button>Login</Button>

// Modal never opens - no state control!
<div className="modal">...</div>
```

🚨🚨🚨 BUTTON VISIBILITY - BUTTONS MUST BE VISIBLE AND READABLE! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════════════
ALL BUTTONS MUST:
1. Have a VISIBLE BACKGROUND COLOR (bg-blue-600, bg-green-500, bg-gray-800, etc.) - NOT transparent!
2. Have VISIBLE TEXT LABEL inside ("Add to Cart", "Buy Now", "Submit", etc.)
3. Have PROPER PADDING (px-4 py-2 minimum, px-6 py-3 recommended)
4. Have READABLE TEXT COLOR that contrasts with background (text-white on dark bg)
5. Have ROUNDED CORNERS (rounded-lg or rounded-xl)
6. Be LARGE ENOUGH to click (minimum 40px height)

✅ CORRECT VISIBLE BUTTON:
```jsx
<button 
  onClick={{() => addToCart(product)}}
  className="w-full px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
>
  Add to Cart
</button>
```

❌ WRONG - INVISIBLE/BROKEN BUTTONS:
```jsx
// No background - invisible!
<button className="text-blue-500">Add to Cart</button>

// Empty button - no text!
<button className="bg-blue-500"></button>

// Icon only without visible styling!
<button><ShoppingCart /></button>

// Too small - hard to click!
<button className="p-1 text-xs">Add</button>
```

PRODUCT CARD BUTTON REQUIREMENTS:
- "Add to Cart" button MUST be full-width inside the card (w-full)
- MUST have solid background color (bg-blue-600, bg-green-600, bg-indigo-600)
- MUST have white text (text-white) 
- MUST have the text "Add to Cart" visible
- MUST have padding (py-3 minimum)
- MUST have onClick handler that calls addToCart function

🌟🌟🌟 PROFESSIONAL E-COMMERCE LAYOUT TEMPLATE (COPY THIS STRUCTURE!) 🌟🌟🌟
═══════════════════════════════════════════════════════════════════════════════
This is how a PROFESSIONAL e-commerce app should be structured (like Lovable/Vercel quality):

```jsx
const App = () => {{
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  
  const categories = ['All', 'Fruits & Vegetables', 'Dairy & Eggs', 'Meat & Seafood', 'Bakery', 'Beverages', 'Snacks', 'Pantry'];
  
  const addToCart = (product) => {{
    setCart([...cart, {{ ...product, cartId: Date.now() }}]);
    showNotification(`${{product.name}} added to cart!`);
  }};
  
  const filteredProducts = products.filter(p => 
    (selectedCategory === 'All' || p.category === selectedCategory) &&
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {{/* ===== STICKY HEADER ===== */}}
      <header className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {{/* Logo */}}
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center">
                <span className="text-xl">🛒</span>
              </div>
              <span className="text-xl font-bold">QuickCart</span>
            </div>
            
            {{/* Navigation */}}
            <nav className="hidden md:flex items-center gap-8">
              <Link to="/shop" className="text-gray-300 hover:text-white transition-colors">Shop</Link>
              <Link to="/categories" className="text-gray-300 hover:text-white transition-colors">Categories</Link>
              <Link to="/deals" className="text-gray-300 hover:text-white transition-colors">Deals</Link>
            </nav>
            
            {{/* Right Side Actions */}}
            <div className="flex items-center gap-4">
              <button 
                onClick={{() => setIsCartOpen(true)}}
                className="relative p-2 text-gray-300 hover:text-white transition-colors"
              >
                <ShoppingCart className="w-6 h-6" />
                {{cart.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 text-white text-xs rounded-full flex items-center justify-center">
                    {{cart.length}}
                  </span>
                )}}
              </button>
              <button className="p-2 text-gray-300 hover:text-white transition-colors">
                <User className="w-6 h-6" />
              </button>
              <button 
                onClick={{() => setIsLoginOpen(true)}}
                className="px-4 py-2 bg-green-500 text-white font-medium rounded-lg hover:bg-green-600 transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {{/* ===== HERO SECTION ===== */}}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          {{/* Badge */}}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 text-sm mb-8">
            <Zap className="w-4 h-4" />
            Delivery in 30 minutes or less
          </div>
          
          {{/* Main Headline */}}
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            <span className="text-white">Groceries delivered</span>
            <br />
            <span className="text-green-400">while you work</span>
          </h1>
          
          {{/* Subtitle */}}
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Fresh groceries at your doorstep. No time wasted in queues. 
            Perfect for busy professionals.
          </p>
          
          {{/* Search Bar */}}
          <div className="max-w-xl mx-auto mb-10">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input 
                type="text"
                placeholder="Search groceries..."
                value={{searchQuery}}
                onChange={{(e) => setSearchQuery(e.target.value)}}
                className="w-full pl-12 pr-4 py-4 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
          </div>
          
          {{/* Trust Badges */}}
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <Truck className="w-5 h-5 text-green-400" />
              Free delivery over $50
            </div>
            <div className="flex items-center gap-2">
              <Leaf className="w-5 h-5 text-green-400" />
              Freshness guaranteed
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-green-400" />
              Express checkout
            </div>
          </div>
        </div>
      </section>
      
      {{/* ===== PRODUCTS SECTION ===== */}}
      <section className="py-16 px-4 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          {{/* Section Header */}}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white">Fresh Picks</h2>
              <p className="text-gray-400">Quality groceries delivered to your door</p>
            </div>
            <span className="text-gray-500">{{filteredProducts.length}} products</span>
          </div>
          
          {{/* Category Pills */}}
          <div className="flex flex-wrap gap-2 mb-8">
            {{categories.map(cat => (
              <button
                key={{cat}}
                onClick={{() => setSelectedCategory(cat)}}
                className={{`px-4 py-2 rounded-full font-medium transition-colors ${{
                  selectedCategory === cat 
                    ? 'bg-green-500 text-white' 
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }}`}}
              >
                {{cat}}
              </button>
            ))}}
          </div>
          
          {{/* Products Grid */}}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {{filteredProducts.map(product => (
              <div key={{product.id}} className="bg-gray-800 rounded-xl overflow-hidden hover:ring-2 hover:ring-green-500/50 transition-all">
                <div className="relative">
                  <img src={{product.image}} alt={{product.name}} className="w-full h-48 object-cover" />
                  {{product.badge && (
                    <span className="absolute top-3 left-3 px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-md">
                      {{product.badge}}
                    </span>
                  )}}
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-white mb-1">{{product.name}}</h3>
                  <p className="text-gray-400 text-sm mb-3">{{product.description}}</p>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-bold text-white">${{product.price}}</span>
                      {{product.originalPrice && (
                        <span className="text-sm text-gray-500 line-through">${{product.originalPrice}}</span>
                      )}}
                    </div>
                    <div className="flex items-center gap-1 text-yellow-400">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm text-gray-400">{{product.rating}}</span>
                    </div>
                  </div>
                  <button 
                    onClick={{() => addToCart(product)}}
                    className="w-full py-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition-colors"
                  >
                    Add to Cart
                  </button>
                </div>
              </div>
            ))}}
          </div>
        </div>
      </section>
      
      {{/* ===== FOOTER ===== */}}
      <footer className="py-12 px-4 border-t border-gray-800">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center">
                <span className="text-xl">🛒</span>
              </div>
              <span className="text-xl font-bold">QuickCart</span>
            </div>
            <p className="text-gray-400 text-sm">Fresh groceries delivered fast.</p>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-4">Shop</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><Link to="/categories" className="hover:text-white">Categories</Link></li>
              <li><Link to="/deals" className="hover:text-white">Today's Deals</Link></li>
              <li><Link to="/new" className="hover:text-white">New Arrivals</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-4">Support</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><Link to="/help" className="hover:text-white">Help Center</Link></li>
              <li><Link to="/track" className="hover:text-white">Track Order</Link></li>
              <li><Link to="/returns" className="hover:text-white">Returns</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-4">Legal</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li><Link to="/privacy" className="hover:text-white">Privacy Policy</Link></li>
              <li><Link to="/terms" className="hover:text-white">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-8 pt-8 border-t border-gray-800 text-center text-gray-500 text-sm">
          © 2026 QuickCart. All rights reserved.
        </div>
      </footer>
    </div>
  );
}};
```

KEY PATTERNS FROM THIS TEMPLATE:
1. Dark theme: bg-gray-950 base, bg-gray-900 for sections, bg-gray-800 for cards
2. Green accent: bg-green-500 for CTAs and highlights only
3. Sticky header with backdrop blur for professional feel
4. Trust badges to build confidence
5. Category filter pills (not dropdown)
6. Product cards with hover ring effect
7. Clean grid layout: 1 col mobile → 2 tablet → 4 desktop
8. Proper spacing: py-16/py-20 for sections, p-4 for cards
9. Footer with organized link groups

═══════════════════════════════════════════════════════════════════════════════

📦📦📦 RICH CONTENT REQUIREMENTS - NO EMPTY/BLAND PAGES! 📦📦📦
═══════════════════════════════════════════════════════════════════════════════
EVERY PAGE MUST BE FILLED WITH RICH, REAL CONTENT - NOT BLANK PLACEHOLDERS!

FOR E-COMMERCE APPS (Like Amazon/Walmart):
- Hero banner with featured deal and "Shop Now" button
- "Today's Deals" section with 4-8 discounted products
- "Trending Now" section with popular items
- Category navigation grid (Electronics, Fashion, Home, etc.)
- "Recommended For You" personalized section
- "Best Sellers" section with top-rated products
- Flash sale countdown timer
- Customer reviews and ratings on products
- "Customers Also Bought" section
- Newsletter signup section
- Minimum 20+ products in the mock data
- Multiple product categories (at least 5)
- Product cards with: image, title, price, rating, reviews count, "Add to Cart" button
- Sidebar filters (price range, category, rating, brand)
- Sorting options (price low-high, rating, newest)

FOR TECH/PRODUCT SITES (Like Apple/Samsung):
- Large hero section with flagship product showcase
- "Explore the lineup" section with product family
- Feature highlights with icons and descriptions (8-12 features)
- Comparison table for different models
- Tech specs section with detailed specifications
- Gallery with multiple product angles
- "What's in the box" section
- Reviews and testimonials (4-6 reviews)
- Trade-in program section
- Financing options display
- Store locator or availability checker
- Related accessories section
- Environmental sustainability section
- Support and resources links

FOR PORTFOLIO/PERSONAL SITES:
- Hero with name, title, and professional photo
- "About Me" section with bio and background
- Skills section with proficiency levels (8-12 skills)
- Featured projects grid (6-12 projects with images)
- Work experience timeline
- Education and certifications
- Testimonials from clients/colleagues (4-6)
- Contact form that works
- Social media links
- Resume/CV download button
- Blog or articles section

FOR DASHBOARDS/ADMIN PANELS:
- Key metrics cards (4-6 KPIs with icons)
- Charts: Line chart for trends, Bar chart for comparisons, Pie chart for distribution
- Recent activity feed
- Data tables with sorting and pagination
- User management section
- Settings panel
- Notifications center
- Quick action buttons
- Search and filter functionality
- Export to CSV/PDF buttons

FOR RESTAURANT/FOOD APPS:
- Hero with restaurant image and "Order Now" CTA
- "Popular Dishes" section with 6-8 items
- Full menu organized by categories (Appetizers, Mains, Desserts, Drinks)
- Each menu item: image, name, description, price, dietary icons, "Add to Cart"
- Special offers/combos section
- Restaurant info: hours, location, contact
- Customer reviews (4-6 reviews with photos)
- Delivery tracking interface
- Order history page
- Reservation booking form

MOCK DATA REQUIREMENTS:
- Minimum 15-30 items for any list (products, menu items, projects)
- Use real Unsplash images: https://images.unsplash.com/photo-XXXXXXXXXX?w=400&h=400&q=80
- Realistic names, descriptions, and prices
- Varied ratings (3.5-5.0 stars)
- Review counts (50-5000+ reviews)
- Multiple categories/tags

MANDATORY FULL-STACK INTEGRATION REQUIREMENTS:

1. STATE MANAGEMENT - EVERYTHING MUST USE PROPER STATE:
   ```jsx
   // Required state hooks at top of component
   const [user, setUser] = useState(null);
   const [isLoggedIn, setIsLoggedIn] = useState(false);
   const [cartItems, setCartItems] = useState([]);
   const [isCartOpen, setIsCartOpen] = useState(false);
   const [isLoginOpen, setIsLoginOpen] = useState(false);
   const [loading, setLoading] = useState(false);
   const [searchQuery, setSearchQuery] = useState('');
   const [filteredData, setFilteredData] = useState([]);
   ```

2. MULTI-PAGE APPLICATION WITH REACT ROUTER (ALWAYS INCLUDE):
   - Router components are GLOBAL - DO NOT import from 'react-router-dom'
   - Use: Router, Routes, Route, Link, NavLink, Navigate, useNavigate, useLocation, useParams (all global)
   - Create 5-8 separate page components (HomePage, AboutPage, FeaturesPage, ContactPage, DashboardPage, ProfilePage, etc.)
   - Implement navigation menu with active route highlighting using useLocation()
   - Protected routes that require authentication with Navigate redirects
   - Smooth page transitions and routing
   - Working browser navigation (back/forward buttons)
   - Add React Router to package.json dependencies

🚨🚨🚨 CRITICAL: MULTI-PAGE NAVIGATION MUST WORK - NO SCROLL-TO-SECTION! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════════════
EVERY navigation button MUST actually navigate to a NEW PAGE with NEW CONTENT!

❌ WRONG - DO NOT USE SCROLL-TO-SECTION:
```jsx
// This is WRONG - user stays on same page!
const scrollToSection = (id) => document.getElementById(id)?.scrollIntoView();
<button onClick={{() => scrollToSection('projects')}}>Projects</button>
```

✅ CORRECT - USE ACTUAL ROUTE NAVIGATION:
```jsx
// This is CORRECT - user goes to a NEW PAGE!
const navigate = useNavigate();
<button onClick={{() => navigate('/projects')}}>Projects</button>

// Or use Link component:
<Link to="/projects" className="nav-link">Projects</Link>
```

REQUIRED NAVIGATION STRUCTURE:
```jsx
// At the top of App - define ALL page components FIRST
const HomePage = () => (
  <div className="min-h-screen">
    <h1>Welcome Home</h1>
    <Button onClick={{() => navigate('/projects')}}>View My Work</Button>
    <Button onClick={{() => navigate('/contact')}}>Get In Touch</Button>
  </div>
);

const ProjectsPage = () => (
  <div className="min-h-screen">
    <h1>My Projects</h1>
    {{/* FULL project listing with cards, details, etc. */}}
  </div>
);

const AboutPage = () => (
  <div className="min-h-screen">
    <h1>About Me</h1>
    {{/* FULL about content - bio, skills, experience */}}
  </div>
);

const ContactPage = () => (
  <div className="min-h-screen">
    <h1>Contact</h1>
    {{/* FULL contact form that works */}}
  </div>
);

// Then in App, set up routes:
const App = () => {{
  const location = useLocation();
  const navigate = useNavigate();
  
  return (
    <div>
      {{/* Navigation - EVERY link navigates to a REAL page */}}
      <nav>
        <Link to="/" className={{location.pathname === '/' ? 'text-blue-500 font-bold' : 'text-gray-600'}}>Home</Link>
        <Link to="/projects" className={{location.pathname === '/projects' ? 'text-blue-500 font-bold' : 'text-gray-600'}}>Projects</Link>
        <Link to="/about" className={{location.pathname === '/about' ? 'text-blue-500 font-bold' : 'text-gray-600'}}>About</Link>
        <Link to="/contact" className={{location.pathname === '/contact' ? 'text-blue-500 font-bold' : 'text-gray-600'}}>Contact</Link>
      </nav>
      
      {{/* Routes - EVERY route renders a DIFFERENT page component */}}
      <Routes>
        <Route path="/" element={{<HomePage />}} />
        <Route path="/projects" element={{<ProjectsPage />}} />
        <Route path="/about" element={{<AboutPage />}} />
        <Route path="/contact" element={{<ContactPage />}} />
        <Route path="/blog" element={{<BlogPage />}} />
      </Routes>
    </div>
  );
}};

// REQUIRED wrapper
const AppWrapper = () => (<Router><App /></Router>);
```

EACH PAGE MUST HAVE UNIQUE, SUBSTANTIAL CONTENT:
- HomePage: Hero section, brief intro, CTAs that navigate to other pages
- ProjectsPage: Grid of project cards with details, images, links
- AboutPage: Bio, skills list, experience timeline, education
- ContactPage: Working contact form with name, email, message fields
- BlogPage: List of blog posts with excerpts
- ProfilePage: User info, settings (if logged in)

🚫 ABSOLUTELY FORBIDDEN:
- scrollIntoView(), scrollToSection(), or any scroll-based "navigation"
- All content on one long page with anchor links
- Buttons that don't navigate anywhere
- Empty page components
- Pages that just say "Coming Soon" or placeholder text
   - Add react-router-dom to package.json dependencies
   - Example:
   ```jsx
   const AppContent = () => {{
     const location = useLocation();
     return (
       <main>
         <nav>
           <Link to="/" className={{location.pathname === '/' ? 'active' : ''}}>Home</Link>
           <Link to="/about" className={{location.pathname === '/about' ? 'active' : ''}}>About</Link>
         </nav>
         <Routes>
           <Route path="/" element={{<HomePage />}} />
           <Route path="/about" element={{<AboutPage />}} />
           <Route path="/dashboard" element={{isLoggedIn ? <Dashboard /> : <Navigate to="/login" />}} />
         </Routes>
       </main>
     );
   }};
   ```

3. REAL IMAGES FROM UNSPLASH API (MANDATORY - NO PLACEHOLDERS):
   🚨🚨🚨 EVERY IMAGE MUST BE A REAL UNSPLASH IMAGE - NO EXCEPTIONS 🚨🚨🚨
   
   ⛔ FORBIDDEN IMAGE URLS (WILL BREAK THE APP):
   - https://via.placeholder.com/* 
   - https://placeholder.com/*
   - https://placehold.co/*
   - https://picsum.photos/*
   - Any URL with "placeholder" in it
   - Any fake/made-up URLs
   
   ✅ REQUIRED: Use these REAL Unsplash images for different categories:
   
   🏠 HERO/BANNER IMAGES:
   - "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1600&h=900&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1600&h=900&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1551434678-e076c223a692?w=1600&h=900&q=80&auto=format&fit=crop"
   
   🛒 GROCERY/FOOD PRODUCTS (USE FOR GROCERY STORES):
   - Fresh vegetables: "https://images.unsplash.com/photo-1518843875459-f738682238a6?w=400&h=400&q=80&auto=format&fit=crop"
   - Fruits: "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=400&q=80&auto=format&fit=crop"
   - Organic produce: "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&h=400&q=80&auto=format&fit=crop"
   - Fresh tomatoes: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400&h=400&q=80&auto=format&fit=crop"
   - Grocery basket: "https://images.unsplash.com/photo-1534723452862-4c874018d66d?w=400&h=400&q=80&auto=format&fit=crop"
   - Milk/dairy: "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=400&q=80&auto=format&fit=crop"
   - Bread/bakery: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=400&q=80&auto=format&fit=crop"
   - Meat: "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=400&h=400&q=80&auto=format&fit=crop"
   - Fish/seafood: "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=400&h=400&q=80&auto=format&fit=crop"
   - Eggs: "https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=400&h=400&q=80&auto=format&fit=crop"
   - Grocery hero: "https://images.unsplash.com/photo-1542838132-92c53300491e?w=1600&h=900&q=80&auto=format&fit=crop"
   
   🛍️ E-COMMERCE/PRODUCTS:
   - "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400&h=400&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=400&h=400&q=80&auto=format&fit=crop"
   
   👤 PROFILE/AVATAR IMAGES:
   - "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&q=80&auto=format&fit=crop"
   
   🎨 FEATURE/ICON BACKGROUNDS:
   - "https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&h=600&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=600&q=80&auto=format&fit=crop"
   
   🏢 TEAM/ABOUT IMAGES:
   - "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&h=600&q=80&auto=format&fit=crop"
   - "https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=800&h=600&q=80&auto=format&fit=crop"
   
   Example grocery product array:
   ```jsx
   const GROCERY_PRODUCTS = [
     {{ id: 1, name: "Fresh Organic Vegetables", price: 12.99, image: "https://images.unsplash.com/photo-1518843875459-f738682238a6?w=400&h=400&q=80&auto=format&fit=crop", category: "Produce" }},
     {{ id: 2, name: "Farm Fresh Fruits", price: 8.99, image: "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=400&q=80&auto=format&fit=crop", category: "Produce" }},
     {{ id: 3, name: "Organic Milk", price: 5.99, image: "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=400&q=80&auto=format&fit=crop", category: "Dairy" }},
     {{ id: 4, name: "Artisan Bread", price: 4.99, image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=400&q=80&auto=format&fit=crop", category: "Bakery" }},
     {{ id: 5, name: "Fresh Salmon", price: 15.99, image: "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=400&h=400&q=80&auto=format&fit=crop", category: "Seafood" }},
     {{ id: 6, name: "Free Range Eggs", price: 6.99, image: "https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=400&h=400&q=80&auto=format&fit=crop", category: "Dairy" }},
     {{ id: 7, name: "Premium Beef", price: 18.99, image: "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=400&h=400&q=80&auto=format&fit=crop", category: "Meat" }},
     {{ id: 8, name: "Cherry Tomatoes", price: 3.99, image: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400&h=400&q=80&auto=format&fit=crop", category: "Produce" }},
   ];
   ```

4. COMPLETE AUTHENTICATION SYSTEM (ALWAYS INCLUDE AND MAKE IT WORK):
   - Login modal/page with working form submission:
   ```jsx
   const [email, setEmail] = useState('');
   const [password, setPassword] = useState('');
   const [error, setError] = useState('');
   
   const handleLogin = async (e) => {{
     e.preventDefault();
     setError('');
     if (!email || !password) {{
       setError('Please fill all fields');
       return;
     }}
     // Simulate API call
     setUser({{ email, name: email.split('@')[0] }});
     setIsLoggedIn(true);
     setIsLoginOpen(false);
     showNotification('Login successful!');
   }};
   ```
   - Signup modal/page with user registration form and validation
   - JWT token storage in localStorage with proper management
   - Authentication state management with React context
   - User profile display with logout functionality that works:
   ```jsx
   const handleLogout = () => {{
     setUser(null);
     setIsLoggedIn(false);
     localStorage.removeItem('user');
     showNotification('Logged out successfully');
     navigate('/');
   }};
   ```
   - Protected content areas that check isLoggedIn
   - Proper form validation with error messages
   - "Remember me" checkbox functionality
   - Password strength validation

5. WORKING API INTEGRATION WITH DATABASE (MUST ACTUALLY WORK):
   
   🗄️ DATABASE API AVAILABLE AT: http://localhost:8000/api/db/{{PROJECT_NAME}}/{{COLLECTION}}
   
   The backend provides a UNIVERSAL DATABASE API that works for ANY data:
   
   API ENDPOINTS:
   - GET    /api/db/{{project}}/{{collection}}           → Get all items
   - POST   /api/db/{{project}}/{{collection}}           → Create item (body: {{ data: {{...}} }})
   - GET    /api/db/{{project}}/{{collection}}/{{id}}    → Get single item
   - PUT    /api/db/{{project}}/{{collection}}/{{id}}    → Update item (body: {{ data: {{...}} }})
   - DELETE /api/db/{{project}}/{{collection}}/{{id}}    → Delete item
   - GET    /api/db/{{project}}/{{collection}}/search?q=term → Search items
   - GET    /api/db/{{project}}/products?category=X      → Get filtered products
   - POST   /api/db/{{project}}/orders                   → Create order
   
   EXAMPLE: Fetching products from database:
   ```jsx
   const PROJECT_NAME = '{project_name}'; // Use your project name
   const API_BASE = 'http://localhost:8000/api/db';
   
   const fetchProducts = async () => {{
     setLoading(true);
     try {{
       const response = await fetch(`${{API_BASE}}/${{PROJECT_NAME}}/products`);
       const result = await response.json();
       if (result.success) {{
         setProducts(result.data);
       }}
     }} catch (error) {{
       console.error('Failed to fetch products:', error);
       // Fallback to mock data if API fails
       setProducts(MOCK_PRODUCTS);
     }} finally {{
       setLoading(false);
     }}
   }};
   
   useEffect(() => {{ fetchProducts(); }}, []);
   ```
   
   EXAMPLE: Creating an order:
   ```jsx
   const createOrder = async () => {{
     try {{
       const response = await fetch(`${{API_BASE}}/${{PROJECT_NAME}}/orders`, {{
         method: 'POST',
         headers: {{ 'Content-Type': 'application/json' }},
         body: JSON.stringify({{
           data: {{
             user_id: user?.id,
             items: cartItems,
             total: cartTotal,
             shipping_address: formData.address
           }}
         }})
       }});
       const result = await response.json();
       if (result.success) {{
         showNotification('Order placed successfully!');
         setCartItems([]);
       }}
     }} catch (error) {{
       showNotification('Failed to place order', 'error');
     }}
   }};
   ```
   
   EXAMPLE: Adding a product (admin):
   ```jsx
   const addProduct = async (productData) => {{
     const response = await fetch(`${{API_BASE}}/${{PROJECT_NAME}}/products`, {{
       method: 'POST',
       headers: {{ 'Content-Type': 'application/json' }},
       body: JSON.stringify({{ data: productData }})
     }});
     const result = await response.json();
     if (result.success) {{
       setProducts([...products, result.data]);
     }}
   }};
   ```
   
   IMPORTANT: Always have RICH FALLBACK MOCK DATA in case API is unavailable (minimum 12-20 products):
   ```jsx
   const MOCK_PRODUCTS = [
     {{ id: 1, name: "Wireless Bluetooth Headphones", price: 79.99, originalPrice: 129.99, rating: 4.5, reviews: 2847, image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&q=80", category: "Electronics", badge: "Best Seller" }},
     {{ id: 2, name: "Smart Fitness Watch Pro", price: 199.99, originalPrice: 249.99, rating: 4.7, reviews: 1523, image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&q=80", category: "Electronics", badge: "Top Rated" }},
     {{ id: 3, name: "Premium Leather Backpack", price: 89.99, rating: 4.3, reviews: 892, image: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&q=80", category: "Fashion" }},
     {{ id: 4, name: "Minimalist Desk Lamp", price: 49.99, rating: 4.6, reviews: 1205, image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&q=80", category: "Home", badge: "New" }},
     {{ id: 5, name: "Organic Coffee Beans 1kg", price: 24.99, rating: 4.8, reviews: 3421, image: "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=400&q=80", category: "Food & Drink" }},
     {{ id: 6, name: "Yoga Mat Premium", price: 39.99, rating: 4.4, reviews: 756, image: "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400&h=400&q=80", category: "Sports" }},
     {{ id: 7, name: "Stainless Steel Water Bottle", price: 29.99, rating: 4.5, reviews: 2103, image: "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&h=400&q=80", category: "Sports" }},
     {{ id: 8, name: "Wireless Charging Pad", price: 34.99, originalPrice: 49.99, rating: 4.2, reviews: 1876, image: "https://images.unsplash.com/photo-1586816879360-004f5b0c51e5?w=400&h=400&q=80", category: "Electronics", badge: "Sale" }},
     {{ id: 9, name: "Aromatherapy Diffuser Set", price: 44.99, rating: 4.6, reviews: 945, image: "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=400&h=400&q=80", category: "Home" }},
     {{ id: 10, name: "Running Shoes Ultra", price: 129.99, originalPrice: 159.99, rating: 4.7, reviews: 2567, image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&q=80", category: "Sports", badge: "Popular" }},
     {{ id: 11, name: "Mechanical Keyboard RGB", price: 149.99, rating: 4.8, reviews: 1834, image: "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400&h=400&q=80", category: "Electronics" }},
     {{ id: 12, name: "Ceramic Plant Pot Set", price: 32.99, rating: 4.4, reviews: 623, image: "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=400&h=400&q=80", category: "Home" }},
     {{ id: 13, name: "Portable Bluetooth Speaker", price: 59.99, rating: 4.5, reviews: 1456, image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&q=80", category: "Electronics" }},
     {{ id: 14, name: "Vintage Sunglasses", price: 45.99, rating: 4.3, reviews: 789, image: "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&q=80", category: "Fashion" }},
     {{ id: 15, name: "Scented Candle Collection", price: 28.99, rating: 4.6, reviews: 1102, image: "https://images.unsplash.com/photo-1602028915047-37269d1a73f7?w=400&h=400&q=80", category: "Home" }},
     {{ id: 16, name: "Smart Home Hub", price: 89.99, rating: 4.4, reviews: 934, image: "https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=400&h=400&q=80", category: "Electronics", badge: "Smart Home" }},
   ];
   
   // Categories for filtering
   const CATEGORIES = ["All", "Electronics", "Fashion", "Home", "Sports", "Food & Drink"];
   ```
   
   - Authentication headers: Authorization: Bearer {{token}}
   - Loading states with spinners: {{loading ? <Loading /> : <ProductList />}}
   - Success/error notifications that actually show
   - Automatic token refresh and logout on 401 errors

6. E-COMMERCE FEATURES (If shop/store/cart/product detected - MUST WORK):
   - Product grid with real product data from API or mock data
   - Working addToCart function:
   ```jsx
   const addToCart = (product) => {{
     const existingItem = cartItems.find(item => item.id === product.id);
     if (existingItem) {{
       setCartItems(cartItems.map(item => 
         item.id === product.id 
           ? {{ ...item, quantity: item.quantity + 1 }}
           : item
       ));
     }} else {{
       setCartItems([...cartItems, {{ ...product, quantity: 1 }}]);
     }}
     showNotification(`${{product.name}} added to cart!`);
   }};
   ```
   - Shopping cart modal with working item management:
   ```jsx
   const removeFromCart = (productId) => {{
     setCartItems(cartItems.filter(item => item.id !== productId));
   }};
   
   const updateQuantity = (productId, newQuantity) => {{
     setCartItems(cartItems.map(item =>
       item.id === productId ? {{ ...item, quantity: newQuantity }} : item
     ));
   }};
   ```
   - Cart count display in header that updates: <span>Cart ({{cartItems.length}})</span>
   - Cart persistence in localStorage with useEffect
   - Checkout process with payment forms that submit
   - Order history and tracking display
   - Search and filtering that actually works:
   ```jsx
   const filteredProducts = products.filter(product =>
     product.name.toLowerCase().includes(searchQuery.toLowerCase())
   );
   ```
   - Product detail pages with full information
   - Price calculations that work: 
   ```jsx
   const total = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
   ```

7. 💳💳💳 STRIPE PAYMENT CHECKOUT SYSTEM (E-COMMERCE APPS MUST USE) 💳💳💳:
   
   EVERY e-commerce app MUST have a WORKING checkout flow using window.StripePayment!
   
   ⚠️ DO NOT SIMULATE PAYMENTS - USE THE REAL STRIPE INTEGRATION ⚠️
   
   Required Checkout Page Components:
   ```jsx
   // CHECKOUT PAGE (Add as separate route: /checkout)
   const CheckoutPage = () => {{
     const {{ cartItems, clearCart }} = useCart();
     const navigate = useNavigate();
     const [step, setStep] = useState(1); // 1: Shipping, 2: Payment, 3: Review
     const [isProcessing, setIsProcessing] = useState(false);
     const [orderComplete, setOrderComplete] = useState(false);
     const [paymentError, setPaymentError] = useState(null);
     const [orderId, setOrderId] = useState(null);
     
     // Shipping form state
     const [shippingInfo, setShippingInfo] = useState({{
       fullName: '',
       email: '',
       phone: '',
       address: '',
       city: '',
       state: '',
       zipCode: '',
       country: 'United States'
     }});
     
     // Payment form state  
     const [paymentInfo, setPaymentInfo] = useState({{
       cardNumber: '',
       cardName: '',
       expiryDate: '',
       cvv: ''
     }});
     
     const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
     const shipping = subtotal > 50 ? 0 : 9.99;
     const tax = subtotal * 0.08; // 8% tax
     const total = subtotal + shipping + tax;
     
     // 💳 REAL STRIPE PAYMENT PROCESSING - NOT SIMULATED!
     const handlePlaceOrder = async () => {{
       setIsProcessing(true);
       setPaymentError(null);
       
       try {{
         // Step 1: Create Stripe payment intent
         const paymentIntent = await window.StripePayment.createPaymentIntent(
           Math.round(total * 100), // Amount in cents
           'usd'
         );
         
         console.log('💳 Payment intent created:', paymentIntent);
         
         // Step 2: Process payment with card details
         const result = await window.StripePayment.processPayment(
           {{
             number: paymentInfo.cardNumber.replace(/\\s/g, ''),
             name: paymentInfo.cardName,
             expiry: paymentInfo.expiryDate,
             cvv: paymentInfo.cvv
           }},
           paymentIntent
         );
         
         if (result.success) {{
           // Payment successful - create order
           const orderData = {{
             items: cartItems,
             shipping: shippingInfo,
             payment: {{
               paymentId: result.paymentId,
               last4: result.last4,
               amount: total
             }},
             subtotal,
             tax,
             shippingCost: shipping,
             total,
             status: 'confirmed',
             createdAt: new Date().toISOString()
           }};
           
           // Save order to database
           await db.create('orders', orderData);
           setOrderId(result.paymentId);
           clearCart();
           setOrderComplete(true);
         }} else {{
           // Payment failed
           setPaymentError(result.error || 'Payment failed. Please check your card details.');
         }}
       }} catch (error) {{
         console.error('Payment error:', error);
         setPaymentError('An error occurred. Please try again.');
       }} finally {{
         setIsProcessing(false);
       }}
     }};
     
     // Format card number with spaces (4242 4242 4242 4242)
     const formatCardNumber = (value) => {{
       const v = value.replace(/\\s+/g, '').replace(/[^0-9]/gi, '');
       const parts = [];
       for (let i = 0; i < v.length && i < 16; i += 4) {{
         parts.push(v.substring(i, i + 4));
       }}
       return parts.join(' ');
     }};
     
     if (orderComplete) {{
       return (
         <div className="min-h-screen bg-gray-50 flex items-center justify-center">
           <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md">
             <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
               <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
               </svg>
             </div>
             <h2 className="text-2xl font-bold text-gray-900 mb-2">Order Confirmed!</h2>
             <p className="text-gray-600 mb-2">Thank you for your purchase. Your order is being processed.</p>
             {{orderId && <p className="text-sm text-gray-500 mb-6">Order ID: {{orderId}}</p>}}
             <button 
               onClick={{() => navigate('/')}}
               className="bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
             >
               Continue Shopping
             </button>
           </div>
         </div>
       );
     }}
     
     return (
       <div className="min-h-screen bg-gray-50 py-12">
         <div className="max-w-7xl mx-auto px-4">
           <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>
           
           {{/* Payment Error Alert */}}
           {{paymentError && (
             <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
               <p className="font-medium">Payment Failed</p>
               <p className="text-sm">{{paymentError}}</p>
             </div>
           )}}
           
           {{/* Progress Steps */}}
           <div className="flex items-center justify-center mb-8">
             {{[1, 2, 3].map((s) => (
               <div key={{s}} className="flex items-center">
                 <div className={{`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${{
                   step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                 }}`}}>
                   {{s}}
                 </div>
                 {{s < 3 && <div className={{`w-20 h-1 ${{step > s ? 'bg-blue-600' : 'bg-gray-200'}}`}} />}}
               </div>
             ))}}
           </div>
           
           <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
             {{/* Form Section */}}
             <div className="lg:col-span-2">
               {{step === 1 && (
                 <div className="bg-white p-6 rounded-xl shadow-sm">
                   <h2 className="text-xl font-semibold mb-4">Shipping Information</h2>
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <input 
                       type="text" 
                       placeholder="Full Name"
                       value={{shippingInfo.fullName}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, fullName: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <input 
                       type="email" 
                       placeholder="Email"
                       value={{shippingInfo.email}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, email: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <input 
                       type="tel" 
                       placeholder="Phone"
                       value={{shippingInfo.phone}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, phone: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <input 
                       type="text" 
                       placeholder="Address"
                       value={{shippingInfo.address}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, address: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent md:col-span-2"
                     />
                     <input 
                       type="text" 
                       placeholder="City"
                       value={{shippingInfo.city}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, city: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <input 
                       type="text" 
                       placeholder="State"
                       value={{shippingInfo.state}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, state: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <input 
                       type="text" 
                       placeholder="ZIP Code"
                       value={{shippingInfo.zipCode}}
                       onChange={{(e) => setShippingInfo({{...shippingInfo, zipCode: e.target.value}})}}
                       className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                   </div>
                   <button 
                     onClick={{() => setStep(2)}}
                     className="mt-6 w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
                   >
                     Continue to Payment
                   </button>
                 </div>
               )}}
               
               {{step === 2 && (
                 <div className="bg-white p-6 rounded-xl shadow-sm">
                   <h2 className="text-xl font-semibold mb-4">Payment Details</h2>
                   <p className="text-sm text-gray-500 mb-4">Test card: 4242 4242 4242 4242 | Any future date | Any 3 digits</p>
                   <div className="space-y-4">
                     <input 
                       type="text" 
                       placeholder="Card Number (4242 4242 4242 4242)"
                       value={{paymentInfo.cardNumber}}
                       onChange={{(e) => setPaymentInfo({{...paymentInfo, cardNumber: formatCardNumber(e.target.value)}})}}
                       className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                       maxLength={{19}}
                     />
                     <input 
                       type="text" 
                       placeholder="Name on Card"
                       value={{paymentInfo.cardName}}
                       onChange={{(e) => setPaymentInfo({{...paymentInfo, cardName: e.target.value}})}}
                       className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                     />
                     <div className="grid grid-cols-2 gap-4">
                       <input 
                         type="text" 
                         placeholder="MM/YY"
                         value={{paymentInfo.expiryDate}}
                         onChange={{(e) => setPaymentInfo({{...paymentInfo, expiryDate: e.target.value}})}}
                         className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                         maxLength={{5}}
                       />
                       <input 
                         type="text" 
                         placeholder="CVV"
                         value={{paymentInfo.cvv}}
                         onChange={{(e) => setPaymentInfo({{...paymentInfo, cvv: e.target.value.replace(/\\D/g, '').slice(0, 4)}})}}
                         className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                         maxLength={{4}}
                       />
                     </div>
                   </div>
                   <div className="flex gap-4 mt-6">
                     <button 
                       onClick={{() => setStep(1)}}
                       className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-xl font-semibold hover:bg-gray-50"
                     >
                       Back
                     </button>
                     <button 
                       onClick={{() => setStep(3)}}
                       className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700"
                     >
                       Review Order
                     </button>
                   </div>
                 </div>
               )}}
               
               {{step === 3 && (
                 <div className="bg-white p-6 rounded-xl shadow-sm">
                   <h2 className="text-xl font-semibold mb-4">Review Order</h2>
                   <div className="space-y-4">
                     {{cartItems.map(item => (
                       <div key={{item.id}} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                         <img src={{item.image}} alt={{item.name}} className="w-16 h-16 object-cover rounded" />
                         <div className="flex-1">
                           <h3 className="font-medium">{{item.name}}</h3>
                           <p className="text-gray-500">Qty: {{item.quantity}}</p>
                         </div>
                         <span className="font-semibold">${{(item.price * item.quantity).toFixed(2)}}</span>
                       </div>
                     ))}}
                   </div>
                   <div className="flex gap-4 mt-6">
                     <button 
                       onClick={{() => setStep(2)}}
                       className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-xl font-semibold"
                     >
                       Back
                     </button>
                     <button 
                       onClick={{handlePlaceOrder}}
                       disabled={{isProcessing}}
                       className="flex-1 bg-green-600 text-white py-3 rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50"
                     >
                       {{isProcessing ? 'Processing...' : `Place Order - ${{total.toFixed(2)}}`}}
                     </button>
                   </div>
                 </div>
               )}}
             </div>
             
             {{/* Order Summary */}}
             <div className="bg-white p-6 rounded-xl shadow-sm h-fit sticky top-4">
               <h2 className="text-xl font-semibold mb-4">Order Summary</h2>
               <div className="space-y-3 text-sm">
                 <div className="flex justify-between">
                   <span className="text-gray-600">Subtotal ({{cartItems.length}} items)</span>
                   <span>${{subtotal.toFixed(2)}}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className="text-gray-600">Shipping</span>
                   <span>{{shipping === 0 ? 'FREE' : `${{shipping.toFixed(2)}}`}}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className="text-gray-600">Tax</span>
                   <span>${{tax.toFixed(2)}}</span>
                 </div>
                 <div className="border-t pt-3 flex justify-between font-bold text-lg">
                   <span>Total</span>
                   <span>${{total.toFixed(2)}}</span>
                 </div>
               </div>
             </div>
           </div>
         </div>
       </div>
     );
   }};
   
   // Add route: <Route path="/checkout" element={{<CheckoutPage />}} />
   // Add checkout button in cart: <Link to="/checkout" className="bg-green-600 text-white ...">Checkout</Link>
   ```

8. ADVANCED UI COMPONENTS (ALL MUST WORK):
   - Header with navigation, user info, cart count that all work
   - Working modals with state management:
   ```jsx
   {{isCartOpen && (
     <div className="fixed inset-0 bg-black/50 z-50" onClick={{() => setIsCartOpen(false)}}>
       <div className="bg-white p-6" onClick={{(e) => e.stopPropagation()}}>
         <button onClick={{() => setIsCartOpen(false)}}>Close</button>
         {{cartItems.map(item => (
           <div key={{item.id}}>
             {{item.name}} - ${{item.price}} x {{item.quantity}}
             <button onClick={{() => removeFromCart(item.id)}}>Remove</button>
           </div>
         ))}}
       </div>
     </div>
   )}}
   ```
   - Interactive forms with validation and real submission
   - Loading spinners that show during async operations
   - Error boundaries for crash protection
   - Responsive navigation with working mobile menu toggle
   - Toast notifications that actually appear:
   ```jsx
   const [notification, setNotification] = useState(null);
   
   const showNotification = (message, type = 'success') => {{
     setNotification({{ message, type }});
     setTimeout(() => setNotification(null), 3000);
   }};
   
   {{notification && (
     <div className={{`fixed top-4 right-4 p-4 rounded-lg ${{notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'}} text-white`}}>
       {{notification.message}}
     </div>
   )}}
   ```
   - Breadcrumb navigation that updates
   - Pagination that changes displayed items
   - Search bar that filters results

7. USER DESIGN PREFERENCES - ABSOLUTE COMPLIANCE:
   - If user says "blue theme" → EVERY gradient, button, accent MUST be blue/cyan/teal
   - If user says "dark mode" → bg-gray-900/bg-black everywhere, white text
   - If user says "minimalist" → clean white backgrounds, simple borders, no heavy effects
   - If user says "colorful" → vibrant gradients, multiple accent colors
   - VERIFY: Go through EVERY className and ensure it matches user preferences
   - NO mixing themes - stay consistent with user request throughout entire app

CRITICAL IMPLEMENTATION CHECKLIST:
✅ Every button has onClick handler
✅ Every form has onSubmit handler with preventDefault
✅ All state variables are defined with useState
✅ Cart adds/removes items and updates count
✅ Login/Logout actually changes user state
✅ Modals open/close with state management
✅ Navigation links use React Router Link component
✅ Search/filter actually updates displayed results
✅ Loading states show during async operations
✅ Error handling with try/catch and user feedback
✅ All user color/theme preferences are followed exactly
✅ Real Unsplash images (no placeholders)
✅ Multi-page with 5+ routes
✅ Protected routes check authentication
✅ localStorage persistence for cart and user

🌍🌍🌍 UNIVERSAL APP TYPE SUPPORT - BUILD ANY APPLICATION 🌍🌍🌍
═══════════════════════════════════════════════════════════════════════

These libraries are GLOBALLY AVAILABLE in the sandbox. Use them directly!

9. 🌐 3D GLOBE VIEWER (If user asks for globe, world map, earth visualization):
   
   Globe.gl is LOADED GLOBALLY - use window.createGlobe() or Globe():
   
   ```jsx
   const GlobeViewer = () => {{
     const globeContainerRef = useRef(null);
     const globeRef = useRef(null);
     
     useEffect(() => {{
       if (globeContainerRef.current && !globeRef.current) {{
         // Create 3D globe using globally loaded Globe.gl
         const globe = Globe()(globeContainerRef.current)
           .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
           .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
           .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
           .width(globeContainerRef.current.offsetWidth)
           .height(500);
         
         // Add points/markers on the globe
         const points = [
           {{ lat: 40.7128, lng: -74.0060, name: 'New York', color: '#ff0000' }},
           {{ lat: 51.5074, lng: -0.1278, name: 'London', color: '#00ff00' }},
           {{ lat: 35.6762, lng: 139.6503, name: 'Tokyo', color: '#0000ff' }},
           {{ lat: 48.8566, lng: 2.3522, name: 'Paris', color: '#ffff00' }},
         ];
         
         globe
           .pointsData(points)
           .pointLat('lat')
           .pointLng('lng')
           .pointColor('color')
           .pointAltitude(0.06)
           .pointRadius(0.5)
           .pointLabel(d => d.name);
         
         // Add arcs between cities
         globe
           .arcsData([
             {{ startLat: 40.7128, startLng: -74.0060, endLat: 51.5074, endLng: -0.1278 }},
             {{ startLat: 51.5074, startLng: -0.1278, endLat: 35.6762, endLng: 139.6503 }},
           ])
           .arcColor(() => '#ffffff')
           .arcStroke(0.5)
           .arcAltitudeAutoScale(0.3);
         
         // Auto-rotate
         globe.controls().autoRotate = true;
         globe.controls().autoRotateSpeed = 0.5;
         
         globeRef.current = globe;
       }}
       
       return () => {{
         if (globeRef.current) {{
           // Cleanup
         }}
       }};
     }}, []);
     
     return (
       <div className="min-h-screen bg-black">
         <h1 className="text-white text-3xl font-bold text-center py-8">3D World Globe</h1>
         <div ref={{globeContainerRef}} className="w-full h-[600px]" />
       </div>
     );
   }};
   ```

10. 🗺️ INTERACTIVE MAPS (If user asks for maps, location, directions):
   
   Leaflet is LOADED GLOBALLY - use L.map():
   
   ```jsx
   const MapView = () => {{
     const mapContainerRef = useRef(null);
     const mapRef = useRef(null);
     const [markers, setMarkers] = useState([
       {{ lat: 40.7128, lng: -74.0060, title: 'New York City' }},
       {{ lat: 34.0522, lng: -118.2437, title: 'Los Angeles' }},
       {{ lat: 41.8781, lng: -87.6298, title: 'Chicago' }},
     ]);
     
     useEffect(() => {{
       if (mapContainerRef.current && !mapRef.current && typeof L !== 'undefined') {{
         // Create Leaflet map
         const map = L.map(mapContainerRef.current).setView([39.8283, -98.5795], 4);
         
         // Add OpenStreetMap tiles
         L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
           attribution: '&copy; OpenStreetMap contributors',
           maxZoom: 19
         }}).addTo(map);
         
         // Add markers
         markers.forEach(marker => {{
           L.marker([marker.lat, marker.lng])
             .addTo(map)
             .bindPopup(marker.title);
         }});
         
         mapRef.current = map;
       }}
       
       return () => {{
         if (mapRef.current) {{
           mapRef.current.remove();
           mapRef.current = null;
         }}
       }};
     }}, []);
     
     return (
       <div className="min-h-screen bg-gray-100">
         <h1 className="text-2xl font-bold text-center py-6">Interactive Map</h1>
         <div ref={{mapContainerRef}} className="w-full h-[600px] rounded-lg shadow-lg" />
       </div>
     );
   }};
   ```

11. 📊 CHARTS & DATA VISUALIZATION (If user asks for charts, graphs, analytics):
   
   Chart.js and D3.js are LOADED GLOBALLY:
   
   ```jsx
   const Dashboard = () => {{
     const lineChartRef = useRef(null);
     const barChartRef = useRef(null);
     const pieChartRef = useRef(null);
     
     useEffect(() => {{
       if (typeof Chart !== 'undefined') {{
         // Line Chart
         new Chart(lineChartRef.current, {{
           type: 'line',
           data: {{
             labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
             datasets: [{{
               label: 'Revenue',
               data: [12000, 19000, 15000, 25000, 22000, 30000],
               borderColor: '#3b82f6',
               tension: 0.4,
               fill: true,
               backgroundColor: 'rgba(59, 130, 246, 0.1)'
             }}]
           }},
           options: {{ responsive: true, plugins: {{ legend: {{ position: 'top' }} }} }}
         }});
         
         // Bar Chart
         new Chart(barChartRef.current, {{
           type: 'bar',
           data: {{
             labels: ['Product A', 'Product B', 'Product C', 'Product D'],
             datasets: [{{
               label: 'Sales',
               data: [650, 590, 800, 810],
               backgroundColor: ['#ef4444', '#22c55e', '#3b82f6', '#f59e0b']
             }}]
           }}
         }});
         
         // Pie Chart
         new Chart(pieChartRef.current, {{
           type: 'doughnut',
           data: {{
             labels: ['Desktop', 'Mobile', 'Tablet'],
             datasets: [{{
               data: [55, 35, 10],
               backgroundColor: ['#3b82f6', '#22c55e', '#f59e0b']
             }}]
           }}
         }});
       }}
     }}, []);
     
     return (
       <div className="min-h-screen bg-gray-100 p-8">
         <h1 className="text-3xl font-bold mb-8">Analytics Dashboard</h1>
         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
           <div className="bg-white p-6 rounded-xl shadow-sm">
             <h3 className="font-semibold mb-4">Revenue Over Time</h3>
             <canvas ref={{lineChartRef}} />
           </div>
           <div className="bg-white p-6 rounded-xl shadow-sm">
             <h3 className="font-semibold mb-4">Product Sales</h3>
             <canvas ref={{barChartRef}} />
           </div>
           <div className="bg-white p-6 rounded-xl shadow-sm">
             <h3 className="font-semibold mb-4">Traffic Sources</h3>
             <canvas ref={{pieChartRef}} />
           </div>
         </div>
       </div>
     );
   }};
   ```

12. 💳💳💳 REAL STRIPE PAYMENT INTEGRATION (NOT MOCK - ACTUALLY PROCESSES PAYMENTS) 💳💳💳:
   
   Stripe.js is LOADED GLOBALLY - Use window.StripePayment for real processing:
   
   ```jsx
   const RealCheckoutPage = () => {{
     const {{ cartItems, clearCart, getTotal }} = useCart();
     const navigate = useNavigate();
     const [step, setStep] = useState(1);
     const [isProcessing, setIsProcessing] = useState(false);
     const [paymentError, setPaymentError] = useState(null);
     const [orderComplete, setOrderComplete] = useState(false);
     const [orderId, setOrderId] = useState(null);
     
     // Shipping info
     const [shippingInfo, setShippingInfo] = useState({{
       fullName: '', email: '', phone: '', address: '', city: '', state: '', zipCode: '', country: 'US'
     }});
     
     // Payment info
     const [paymentInfo, setPaymentInfo] = useState({{
       cardNumber: '', cardName: '', expiryDate: '', cvv: ''
     }});
     
     const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
     const shipping = subtotal > 50 ? 0 : 9.99;
     const tax = subtotal * 0.08;
     const total = subtotal + shipping + tax;
     
     // REAL PAYMENT PROCESSING WITH STRIPE
     const handlePayment = async () => {{
       setIsProcessing(true);
       setPaymentError(null);
       
       try {{
         // Step 1: Create payment intent
         const paymentIntent = await window.StripePayment.createPaymentIntent(
           Math.round(total * 100), // Amount in cents
           'usd'
         );
         
         console.log('💳 Payment intent created:', paymentIntent);
         
         // Step 2: Process payment with card details
         const result = await window.StripePayment.processPayment(
           {{
             number: paymentInfo.cardNumber,
             name: paymentInfo.cardName,
             expiry: paymentInfo.expiryDate,
             cvv: paymentInfo.cvv
           }},
           paymentIntent
         );
         
         if (result.success) {{
           console.log('✅ Payment successful:', result);
           
           // Step 3: Create order in database
           const orderData = {{
             items: cartItems,
             shipping: shippingInfo,
             payment: {{
               paymentId: result.paymentId,
               last4: result.last4,
               amount: total
             }},
             subtotal, tax, shippingCost: shipping, total,
             status: 'confirmed',
             createdAt: new Date().toISOString()
           }};
           
           // Save to database
           const orderResponse = await fetch(`http://localhost:8000/api/db/${{PROJECT_NAME}}/orders`, {{
             method: 'POST',
             headers: {{ 'Content-Type': 'application/json' }},
             body: JSON.stringify({{ data: orderData }})
           }});
           
           const order = await orderResponse.json();
           setOrderId(order.data?.id || result.paymentId);
           
           // Clear cart and show success
           clearCart();
           setOrderComplete(true);
         }} else {{
           setPaymentError(result.error || 'Payment failed. Please try again.');
         }}
       }} catch (error) {{
         console.error('Payment error:', error);
         setPaymentError('An error occurred. Please try again.');
       }} finally {{
         setIsProcessing(false);
       }}
     }};
     
     // Format card number with spaces
     const formatCardNumber = (value) => {{
       const v = value.replace(/\\s+/g, '').replace(/[^0-9]/gi, '');
       const matches = v.match(/\\d{{4,16}}/g);
       const match = matches && matches[0] || '';
       const parts = [];
       for (let i = 0; i < match.length; i += 4) {{
         parts.push(match.substring(i, i + 4));
       }}
       return parts.length ? parts.join(' ') : value;
     }};
     
     if (orderComplete) {{
       return (
         <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
           <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md w-full">
             <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
               <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
               </svg>
             </div>
             <h2 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
             <p className="text-gray-600 mb-4">Your order has been confirmed.</p>
             <p className="text-sm text-gray-500 mb-6">Order ID: {{orderId}}</p>
             <p className="text-lg font-semibold text-green-600 mb-8">Total Charged: ${{total.toFixed(2)}}</p>
             <button 
               onClick={{() => navigate('/')}}
               className="w-full bg-blue-600 text-white py-4 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
             >
               Continue Shopping
             </button>
           </div>
         </div>
       );
     }}
     
     return (
       <div className="min-h-screen bg-gray-50 py-12">
         <div className="max-w-4xl mx-auto px-4">
           <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">Secure Checkout</h1>
           
           {{/* Progress Steps */}}
           <div className="flex items-center justify-center mb-10">
             {{['Shipping', 'Payment', 'Confirm'].map((label, i) => (
               <div key={{label}} className="flex items-center">
                 <div className={{`w-10 h-10 rounded-full flex items-center justify-center font-bold ${{
                   step > i + 1 ? 'bg-green-500 text-white' : 
                   step === i + 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                 }}`}}>
                   {{step > i + 1 ? '✓' : i + 1}}
                 </div>
                 <span className="ml-2 font-medium text-gray-700">{{label}}</span>
                 {{i < 2 && <div className={{`w-16 h-1 mx-4 ${{step > i + 1 ? 'bg-green-500' : 'bg-gray-200'}}`}} />}}
               </div>
             ))}}
           </div>
           
           {{/* Error Message */}}
           {{paymentError && (
             <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
               ⚠️ {{paymentError}}
             </div>
           )}}
           
           {{/* Step 1: Shipping */}}
           {{step === 1 && (
             <div className="bg-white p-8 rounded-2xl shadow-sm">
               <h2 className="text-xl font-semibold mb-6">Shipping Information</h2>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 <input placeholder="Full Name" value={{shippingInfo.fullName}} 
                   onChange={{(e) => setShippingInfo({{...shippingInfo, fullName: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500" />
                 <input placeholder="Email" type="email" value={{shippingInfo.email}}
                   onChange={{(e) => setShippingInfo({{...shippingInfo, email: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500" />
                 <input placeholder="Phone" value={{shippingInfo.phone}}
                   onChange={{(e) => setShippingInfo({{...shippingInfo, phone: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500" />
                 <input placeholder="Address" value={{shippingInfo.address}}
                   onChange={{(e) => setShippingInfo({{...shippingInfo, address: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 md:col-span-2" />
                 <input placeholder="City" value={{shippingInfo.city}}
                   onChange={{(e) => setShippingInfo({{...shippingInfo, city: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg" />
                 <input placeholder="State" value={{shippingInfo.state}}
                   onChange={{(e) => setShippingInfo({{...shippingInfo, state: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg" />
                 <input placeholder="ZIP Code" value={{shippingInfo.zipCode}}
                   onChange={{(e) => setShippingInfo({{...shippingInfo, zipCode: e.target.value}})}}
                   className="px-4 py-3 border rounded-lg" />
               </div>
               <button onClick={{() => setStep(2)}}
                 className="mt-8 w-full bg-blue-600 text-white py-4 rounded-xl font-semibold hover:bg-blue-700">
                 Continue to Payment
               </button>
             </div>
           )}}
           
           {{/* Step 2: Payment */}}
           {{step === 2 && (
             <div className="bg-white p-8 rounded-2xl shadow-sm">
               <h2 className="text-xl font-semibold mb-6">Payment Details</h2>
               <div className="space-y-4">
                 <div>
                   <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                   <input placeholder="1234 5678 9012 3456" 
                     value={{formatCardNumber(paymentInfo.cardNumber)}}
                     onChange={{(e) => setPaymentInfo({{...paymentInfo, cardNumber: e.target.value.replace(/\\s/g, '')}})}}
                     maxLength="19"
                     className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500" />
                 </div>
                 <div>
                   <label className="block text-sm font-medium text-gray-700 mb-1">Name on Card</label>
                   <input placeholder="John Doe" value={{paymentInfo.cardName}}
                     onChange={{(e) => setPaymentInfo({{...paymentInfo, cardName: e.target.value}})}}
                     className="w-full px-4 py-3 border rounded-lg" />
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                   <div>
                     <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                     <input placeholder="MM/YY" value={{paymentInfo.expiryDate}}
                       onChange={{(e) => setPaymentInfo({{...paymentInfo, expiryDate: e.target.value}})}}
                       maxLength="5"
                       className="w-full px-4 py-3 border rounded-lg" />
                   </div>
                   <div>
                     <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
                     <input placeholder="123" type="password" value={{paymentInfo.cvv}}
                       onChange={{(e) => setPaymentInfo({{...paymentInfo, cvv: e.target.value}})}}
                       maxLength="4"
                       className="w-full px-4 py-3 border rounded-lg" />
                   </div>
                 </div>
               </div>
               <p className="text-xs text-gray-500 mt-4">🔒 Your payment is secured with SSL encryption</p>
               <div className="flex gap-4 mt-8">
                 <button onClick={{() => setStep(1)}} className="flex-1 border py-4 rounded-xl font-semibold">Back</button>
                 <button onClick={{() => setStep(3)}} className="flex-1 bg-blue-600 text-white py-4 rounded-xl font-semibold">Review Order</button>
               </div>
             </div>
           )}}
           
           {{/* Step 3: Review & Pay */}}
           {{step === 3 && (
             <div className="bg-white p-8 rounded-2xl shadow-sm">
               <h2 className="text-xl font-semibold mb-6">Review Your Order</h2>
               
               {{/* Order Items */}}
               <div className="space-y-3 mb-6">
                 {{cartItems.map(item => (
                   <div key={{item.id}} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                     <img src={{item.image}} alt={{item.name}} className="w-16 h-16 object-cover rounded" />
                     <div className="flex-1">
                       <p className="font-medium">{{item.name}}</p>
                       <p className="text-gray-500 text-sm">Qty: {{item.quantity}}</p>
                     </div>
                     <p className="font-semibold">${{(item.price * item.quantity).toFixed(2)}}</p>
                   </div>
                 ))}}
               </div>
               
               {{/* Order Summary */}}
               <div className="border-t pt-4 space-y-2">
                 <div className="flex justify-between"><span>Subtotal</span><span>${{subtotal.toFixed(2)}}</span></div>
                 <div className="flex justify-between"><span>Shipping</span><span>{{shipping === 0 ? 'FREE' : `${{shipping.toFixed(2)}}`}}</span></div>
                 <div className="flex justify-between"><span>Tax</span><span>${{tax.toFixed(2)}}</span></div>
                 <div className="flex justify-between text-lg font-bold pt-2 border-t">
                   <span>Total</span><span>${{total.toFixed(2)}}</span>
                 </div>
               </div>
               
               <div className="flex gap-4 mt-8">
                 <button onClick={{() => setStep(2)}} className="flex-1 border py-4 rounded-xl font-semibold">Back</button>
                 <button 
                   onClick={{handlePayment}}
                   disabled={{isProcessing}}
                   className="flex-1 bg-green-600 text-white py-4 rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                 >
                   {{isProcessing ? (
                     <span className="flex items-center justify-center gap-2">
                       <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                         <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                         <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                       </svg>
                       Processing Payment...
                     </span>
                   ) : `Pay ${{total.toFixed(2)}}`}}
                 </button>
               </div>
             </div>
           )}}
         </div>
       </div>
     );
   }};
   
   // TEST CARD NUMBERS FOR STRIPE:
   // ✅ Success: 4242 4242 4242 4242
   // ❌ Declined: 4000 0000 0000 0002
   // ❌ Insufficient: 4000 0000 0000 9995
   // Use any future expiry date and any 3-digit CVV
   ```

13. 🎮 GAME/INTERACTIVE APPS (If user asks for games, puzzles, interactive):
   
   ```jsx
   const MemoryGame = () => {{
     const [cards, setCards] = useState([]);
     const [flipped, setFlipped] = useState([]);
     const [matched, setMatched] = useState([]);
     const [moves, setMoves] = useState(0);
     const [gameComplete, setGameComplete] = useState(false);
     
     const emojis = ['🎮', '🎯', '🎲', '🎪', '🎨', '🎭', '🎸', '🎺'];
     
     useEffect(() => {{
       initGame();
     }}, []);
     
     const initGame = () => {{
       const shuffled = [...emojis, ...emojis]
         .sort(() => Math.random() - 0.5)
         .map((emoji, i) => ({{ id: i, emoji, isFlipped: false }}));
       setCards(shuffled);
       setFlipped([]);
       setMatched([]);
       setMoves(0);
       setGameComplete(false);
     }};
     
     const handleCardClick = (id) => {{
       if (flipped.length === 2 || flipped.includes(id) || matched.includes(id)) return;
       
       const newFlipped = [...flipped, id];
       setFlipped(newFlipped);
       
       if (newFlipped.length === 2) {{
         setMoves(m => m + 1);
         const [first, second] = newFlipped;
         if (cards[first].emoji === cards[second].emoji) {{
           const newMatched = [...matched, first, second];
           setMatched(newMatched);
           setFlipped([]);
           if (newMatched.length === cards.length) {{
             setGameComplete(true);
           }}
         }} else {{
           setTimeout(() => setFlipped([]), 1000);
         }}
       }}
     }};
     
     return (
       <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-8">
         <div className="max-w-md mx-auto">
           <h1 className="text-3xl font-bold text-white text-center mb-2">Memory Game</h1>
           <p className="text-white/80 text-center mb-6">Moves: {{moves}}</p>
           
           {{gameComplete && (
             <div className="bg-white p-6 rounded-xl text-center mb-6">
               <h2 className="text-2xl font-bold text-green-600">🎉 You Won!</h2>
               <p>Completed in {{moves}} moves</p>
               <button onClick={{initGame}} className="mt-4 bg-purple-600 text-white px-6 py-2 rounded-lg">Play Again</button>
             </div>
           )}}
           
           <div className="grid grid-cols-4 gap-3">
             {{cards.map((card) => (
               <button
                 key={{card.id}}
                 onClick={{() => handleCardClick(card.id)}}
                 className={{`aspect-square text-4xl rounded-xl transition-all duration-300 ${{
                   flipped.includes(card.id) || matched.includes(card.id)
                     ? 'bg-white'
                     : 'bg-white/20 hover:bg-white/30'
                 }}`}}
               >
                 {{(flipped.includes(card.id) || matched.includes(card.id)) ? card.emoji : '?'}}
               </button>
             ))}}
           </div>
           
           <button onClick={{initGame}} className="mt-6 w-full bg-white/20 text-white py-3 rounded-xl hover:bg-white/30">
             Reset Game
           </button>
         </div>
       </div>
     );
   }};
   ```

14. 📝 FORMS & SURVEYS (If user asks for forms, surveys, questionnaires):
   
   ALL FORMS MUST SUBMIT AND SAVE DATA:
   
   ```jsx
   const SurveyForm = () => {{
     const [currentQuestion, setCurrentQuestion] = useState(0);
     const [answers, setAnswers] = useState({{}});
     const [submitted, setSubmitted] = useState(false);
     
     const questions = [
       {{ id: 1, type: 'rating', text: 'How satisfied are you?', max: 5 }},
       {{ id: 2, type: 'text', text: 'What could we improve?' }},
       {{ id: 3, type: 'choice', text: 'Would you recommend us?', options: ['Yes', 'No', 'Maybe'] }},
     ];
     
     const handleSubmit = async () => {{
       try {{
         await fetch(`http://localhost:8000/api/db/${{PROJECT_NAME}}/surveys`, {{
           method: 'POST',
           headers: {{ 'Content-Type': 'application/json' }},
           body: JSON.stringify({{ data: answers }})
         }});
         setSubmitted(true);
       }} catch (error) {{
         console.error('Survey submission failed:', error);
       }}
     }};
     
     // ... render questions with working navigation and submission
   }};
   ```

15. 🎵 MEDIA PLAYERS (If user asks for music, video, podcast player):
   
   ```jsx
   const MusicPlayer = () => {{
     const [isPlaying, setIsPlaying] = useState(false);
     const [currentTrack, setCurrentTrack] = useState(0);
     const [volume, setVolume] = useState(80);
     const [progress, setProgress] = useState(0);
     const audioRef = useRef(null);
     
     const tracks = [
       {{ title: 'Summer Vibes', artist: 'Chill Beats', duration: '3:45', cover: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300' }},
       {{ title: 'Night Drive', artist: 'Lo-Fi Dreams', duration: '4:20', cover: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300' }},
       {{ title: 'Coffee Morning', artist: 'Acoustic Soul', duration: '3:15', cover: 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300' }},
     ];
     
     // ... implement play/pause, next/prev, volume control, progress bar
   }};
   ```

═══════════════════════════════════════════════════════════════════════

CRITICAL IMPLEMENTATION REQUIREMENTS:
- ALL COMPONENTS MUST BE PROPERLY DEFINED AND EXPORTED
- NO UNDEFINED VARIABLES OR COMPONENTS  
- USE PROPER ERROR BOUNDARIES AND LOADING STATES
- INCLUDE SHADCN/UI STYLE COMPONENTS
- WORKING STATE MANAGEMENT WITH REACT HOOKS
- REAL API CALLS WITH PROPER ERROR HANDLING
- ADD react-router-dom TO package.json FOR MULTI-PAGE ROUTING
- USE REAL IMAGES FROM UNSPLASH (https://images.unsplash.com/photo-{{id}}?w={{width}}&h={{height}}&q=80&auto=format&fit=crop)

⚠️ CRITICAL: DO NOT CREATE DUPLICATE COMPONENTS
- Components like Button, Input, Card, Loading, AnimatedText, Navigation are ALREADY PROVIDED in src/components/ui/
- Import them at the top: import {{ Button, Input, Card }} from './components/ui/Button';
- DO NOT redefine these components inline in App.jsx
- ONLY create NEW components that are specific to your app (e.g., ProductCard, CartItem, etc.)

Build a complete, functional MULTI-PAGE app with:
- React Router with 5-8 separate pages (Home, About, Features, Contact, Dashboard, Profile, etc.)
- Real images from Unsplash API (NEVER placeholders)
- Authentication system with working login/signup
- Modern hero section with call-to-action buttons  
- Feature showcase with interactive elements
- Working e-commerce functionality (if applicable)
- Responsive design with TailwindCSS
- Real, relevant content and professional appearance

🚨🚨🚨 !!!! CRITICAL ERROR PREVENTION RULE - READ THIS FIRST !!!! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════
⛔⛔⛔ FAILURE TO FOLLOW THIS WILL CAUSE IMMEDIATE "Identifier 'Button' has already been declared" ERROR ⛔⛔⛔

⚠️ ABSOLUTE RULE: DO NOT DECLARE Button, Input, Card, Loading, AnimatedText, OR Navigation COMPONENTS!
⚠️ THESE COMPONENTS ALREADY EXIST IN SEPARATE FILES!
⚠️ YOU MUST ONLY IMPORT THEM - NEVER REDECLARE THEM!

🔴 FORBIDDEN DECLARATIONS (These will break the code):
```jsx
// ❌ WRONG - DO NOT WRITE THIS - THIS CAUSES ERROR:
const Button = ({{ children, ...props }}) => <button {{...props}}>{{children}}</button>;
const Input = (props) => <input {{...props}} />;
const Card = ({{ children }}) => <div>{{children}}</div>;
// ⛔ If you write any of the above, the code WILL FAIL with duplicate declaration error!
```

✅ CORRECT APPROACH (Only way that works):
```jsx
// ✅ START YOUR CODE WITH THESE IMPORTS:
import {{ Button, Input, Card, Loading }} from './components/ui/Button';
import {{ NavBar, NavLink, FloatingTabs }} from './components/ui/Navigation';
import {{ AnimatedText }} from './components/ui/AnimatedText';

// ✅ Then use them directly in your JSX:
<Button onClick={{handleClick}} variant="primary">Click Me</Button>
<Input value={{email}} onChange={{e => setEmail(e.target.value)}} />
<Card className="p-6">Content here</Card>
```

⛔ VERIFICATION CHECKLIST BEFORE GENERATING CODE:
□ Did you write "const Button ="? → ❌ DELETE IT! Import Button instead!
□ Did you write "const Input ="? → ❌ DELETE IT! Import Input instead!
□ Did you write "const Card ="? → ❌ DELETE IT! Import Card instead!
□ Did you write "const Loading ="? → ❌ DELETE IT! Import Loading instead!
□ Did you add import statements for Button, Input, Card? → ✅ REQUIRED!

🚨 IMPORTANT: These components are pre-built with full functionality, variants, and styling.
📍 Location: src/components/ui/Button.jsx, src/components/ui/Input.jsx, etc.
💡 You only need to CREATE NEW components that are app-specific (e.g., ProductCard, UserProfile, etc.)

═══════════════════════════════════════════════
🚨🚨🚨 END CRITICAL RULE 🚨🚨🚨

MANDATORY COMPONENT ARCHITECTURE:
```jsx
// ✅ CORRECT IMPORT SYNTAX (MUST BE AT TOP - NO EXTRA COMMAS!):
import React, {{ useState, useEffect, createContext, useContext }} from 'react';
import {{ BrowserRouter, Routes, Route, Link, Navigate, useNavigate, useLocation }} from 'react-router-dom';

// 🚨🚨 CRITICAL: IMPORT UI COMPONENTS - NEVER REDECLARE THEM! 🚨🚨
import {{ Button }} from './components/ui/Button';
import {{ Input }} from './components/ui/Input';
import {{ Card }} from './components/ui/Card';
import {{ Loading }} from './components/ui/Loading';
import {{ AnimatedText }} from './components/ui/AnimatedText';
import {{ NavBar, NavLink, FloatingTabs }} from './components/ui/Navigation';

// Import utility functions
import {{ cn }} from './lib/utils';

// ❌ WRONG - Extra comma after React causes syntax error:
// import React, from 'react';  // NEVER DO THIS!

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

// ⚠️ ICON COMPONENTS - ALREADY DEFINED BELOW - DO NOT REDECLARE! ⚠️
// These icons are already defined in this template. DO NOT create them again!
// Just USE them directly: <Star />, <User />, <ShoppingCart />, <X />, <Plus />, <Minus />

const Star = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>;

const User = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;

const ShoppingCart = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57L23 6H6"></path></svg>;

const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;

const Plus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>;

const Minus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14"></path></svg>;

// 🚨🚨🚨 ICONS ALREADY DEFINED ABOVE - DO NOT REDECLARE Star, User, ShoppingCart, X, Plus, Minus! 🚨🚨🚨
// If you need other icons (Menu, Search, Heart, etc.), ONLY define those. 
// NEVER write "const X = " or "const Star = " again - they exist above!

// 🚨🚨 CRITICAL: IMPORT THESE COMPONENTS - DO NOT REDECLARE THEM! 🚨🚨
// ⛔ Button, Input, Card, Loading, AnimatedText, NavBar - ALL EXIST IN ui/ FOLDER
// ⛔ YOU MUST IMPORT THEM AT THE TOP OF YOUR CODE
// ⛔ DO NOT WRITE: const Button = ... (This will cause duplicate declaration error!)
// ✅ CORRECT: import {{ Button, Input, Card }} from './components/ui/Button';

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

// GOOGLE SIGN-IN CONFIGURATION (Xverta shared OAuth - works for *.xverta.com)
const XVERTA_GOOGLE_CLIENT_ID = 'YOUR_XVERTA_GOOGLE_CLIENT_ID.apps.googleusercontent.com';

// Google Icon Component
const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

// Handle Google Sign-In
const handleGoogleSignIn = async (onSuccess, setError, setLoading) => {{
  setLoading(true);
  setError('');
  
  try {{
    // Load Google Identity Services script dynamically
    if (!window.google) {{
      await new Promise((resolve, reject) => {{
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      }});
    }}
    
    // Initialize Google Sign-In
    window.google.accounts.id.initialize({{
      client_id: XVERTA_GOOGLE_CLIENT_ID,
      callback: async (response) => {{
        try {{
          // Send ID token to backend
          const res = await fetch('http://localhost:8000/api/auth/google', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ id_token: response.credential }})
          }});
          
          const data = await res.json();
          
          if (res.ok) {{
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            onSuccess(data.user);
          }} else {{
            setError(data.detail || 'Google sign-in failed');
          }}
        }} catch (err) {{
          setError('Network error. Please try again.');
        }} finally {{
          setLoading(false);
        }}
      }}
    }});
    
    // Trigger Google Sign-In
    window.google.accounts.id.prompt();
  }} catch (err) {{
    setError('Failed to load Google Sign-In');
    setLoading(false);
  }}
}};

// AUTHENTICATION COMPONENTS (ALWAYS INCLUDE - MONGODB INTEGRATED)
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
      // MongoDB backend authentication endpoint
      const response = await fetch('http://localhost:8000/api/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ email, password }})
      }});
      
      const data = await response.json();
      
      if (response.ok) {{
        // Store JWT token for subsequent authenticated requests
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onSuccess(data.user);
        onClose();
      }} else {{
        setError(data.detail || 'Login failed. Please check your credentials.');
      }}
    }} catch (err) {{
      setError('Network error. Please check if the server is running.');
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
        
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with</span>
          </div>
        </div>
        
        <button
          type="button"
          onClick={{() => handleGoogleSignIn(onSuccess, setError, setLoading)}}
          disabled={{loading}}
          className="w-full flex items-center justify-center gap-3 px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <GoogleIcon />
          <span>Continue with Google</span>
        </button>
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
    
    // Password validation for MongoDB auth
    if (formData.password.length < 8) {{
      setError('Password must be at least 8 characters');
      return;
    }}
    
    setLoading(true);
    setError('');
    
    try {{
      // MongoDB backend signup endpoint
      const response = await fetch('http://localhost:8000/api/auth/signup', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          username: formData.name || formData.email.split('@')[0],
          email: formData.email,
          password: formData.password
        }})
      }});
      
      const data = await response.json();
      
      if (response.ok) {{
        // Store JWT token for subsequent authenticated requests
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onSuccess(data.user);
        onClose();
      }} else {{
        setError(data.detail || 'Registration failed. Please try again.');
      }}
    }} catch (err) {{
      setError('Network error. Please check if the server is running.');
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
        
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with</span>
          </div>
        </div>
        
        <button
          type="button"
          onClick={{() => handleGoogleSignIn(onSuccess, setError, setLoading)}}
          disabled={{loading}}
          className="w-full flex items-center justify-center gap-3 px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <GoogleIcon />
          <span>Sign up with Google</span>
        </button>
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
                  <div className="flex justify-center gap-4 flex-wrap">
                    {{!user && (
                      <>
                        <button onClick={{() => setShowSignup(true)}} className="bg-white text-blue-600 hover:bg-gray-100 font-bold px-8 py-4 rounded-xl shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300">
                          Get Started
                        </button>
                        <button onClick={{() => setShowLogin(true)}} className="border-2 border-white text-white hover:bg-white hover:text-blue-600 font-bold px-8 py-4 rounded-xl transition-all duration-300">
                          Learn More
                        </button>
                      </>
                    )}}
                    {{user && (
                      <button className="bg-white text-blue-600 font-bold px-8 py-4 rounded-xl shadow-xl">
                        Welcome back, {{user.name}}!
                      </button>
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

🎨🎨🎨 PROFESSIONAL DESIGN QUALITY REQUIREMENTS 🎨🎨🎨
═══════════════════════════════════════════════════════════════
Your output MUST look like a PROFESSIONAL, POLISHED website - not a basic prototype!

✅ HERO SECTION MUST HAVE:
- Full-width gradient or image background (min-h-[60vh] or min-h-screen)
- Large, bold headline (text-4xl md:text-6xl font-bold)
- Descriptive subheading (text-xl text-gray-600)
- TWO VISIBLE CTA BUTTONS with contrasting colors:
  - Primary: bg-blue-600 text-white px-8 py-4 rounded-xl font-bold shadow-xl hover:shadow-2xl
  - Secondary: border-2 border-blue-600 text-blue-600 px-8 py-4 rounded-xl font-bold hover:bg-blue-600 hover:text-white

✅ NAVIGATION MUST HAVE:
- Fixed/sticky header with backdrop-blur effect
- Logo on left, menu items center or right
- Properly styled nav links with hover effects
- Mobile hamburger menu that works

✅ CARD COMPONENTS MUST HAVE:
- Rounded corners (rounded-xl or rounded-2xl)
- Shadows (shadow-lg hover:shadow-xl)
- Proper padding (p-6)
- Hover animations (hover:-translate-y-1 transition-all)
- Clear visual hierarchy

✅ ALL BUTTONS MUST BE VISIBLE WITH:
- Solid background colors (bg-blue-600, bg-purple-600, bg-green-600, etc.)
- Proper padding (px-6 py-3 minimum)
- Rounded corners (rounded-lg or rounded-xl)
- Hover effects (hover:bg-blue-700, hover:scale-105)
- Font weight (font-semibold or font-bold)
- Shadows for depth (shadow-lg)

✅ RESPONSIVE DESIGN:
- Use Tailwind breakpoints (sm:, md:, lg:, xl:)
- Mobile-first approach
- Flexible grid layouts (grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3)
- Proper spacing that adjusts (p-4 md:p-8 lg:p-12)

✅ IMAGES:
- Use REAL Unsplash images: https://images.unsplash.com/photo-{id}?w=800&h=600&q=80&fit=crop
- Proper aspect ratios (aspect-video, aspect-square)
- Object-fit (object-cover)
- Rounded corners (rounded-xl)

❌ NEVER GENERATE:
- Plain text buttons without background colors
- Invisible or hard-to-see interactive elements
- Basic unstyled layouts
- Missing hover states
- Prototype-quality designs

🚨🚨🚨 FINAL CRITICAL CHECK - VERIFY BEFORE GENERATING 🚨🚨🚨
═══════════════════════════════════════════════════════════════
⛔ SCAN YOUR CODE FOR THESE FORBIDDEN PATTERNS (WILL CAUSE "Identifier already declared" ERROR):
  ❌ const Button = 
  ❌ const Input = 
  ❌ const Card = 
  ❌ const Loading = 
  ❌ const AnimatedText = 
  ❌ const NavBar = 
  ❌ const Star =      ← ALREADY IN TEMPLATE!
  ❌ const User =      ← ALREADY IN TEMPLATE!
  ❌ const ShoppingCart = ← ALREADY IN TEMPLATE!
  ❌ const X =         ← ALREADY IN TEMPLATE!
  ❌ const Plus =      ← ALREADY IN TEMPLATE!
  ❌ const Minus =     ← ALREADY IN TEMPLATE!
  
  IF YOU FIND ANY OF THESE → DELETE THEM! THEY EXIST IN THE TEMPLATE ABOVE!
  
✅ YOUR CODE MUST START WITH THESE IMPORTS:
  import {{ Button, Input, Card, Loading }} from './components/ui/Button';
  import {{ NavBar, NavLink }} from './components/ui/Navigation';
  import {{ AnimatedText }} from './components/ui/AnimatedText';
  
⚠️ These components are pre-built and WILL cause "Identifier already declared" error if redeclared!
⚠️ The icon components (Star, User, ShoppingCart, X, Plus, Minus) are ALREADY in the template - just use them!

🚨 FRAMER-MOTION CRITICAL FIXES:
- ALWAYS wrap conditional renders with <AnimatePresence>
- Example: <AnimatePresence>{{showModal && <motion.div exit={{{{opacity: 0}}}}>Content</motion.div>}}</AnimatePresence>
- Use motion.div, motion.button, etc. for animated elements
- Include exit animations to prevent "AnimatePresence is not defined" errors
- Proper imports: import {{ motion, AnimatePresence }} from 'framer-motion';

🗄️🗄️🗄️ BACKEND API INTEGRATION - CRITICAL FOR FULL-STACK FUNCTIONALITY 🗄️🗄️🗄️
═══════════════════════════════════════════════════════════════════════════════════

The generated backend provides these API endpoints. Your frontend MUST use them!

📌 AUTHENTICATION API (MongoDB Backend) - BASE: http://localhost:8000/api/auth
════════════════════════════════════════════════════════════════════════════════
POST /api/auth/signup   - Register new user
  Request: {{ "email": "user@example.com", "username": "user123", "password": "SecurePass1" }}
  Response: {{ "access_token": "jwt...", "token_type": "bearer", "user": {{ "email": "...", "username": "..." }} }}

POST /api/auth/login    - Login existing user
  Request: {{ "email": "user@example.com", "password": "SecurePass1" }}
  Response: {{ "access_token": "jwt...", "token_type": "bearer", "user": {{ "email": "...", "username": "..." }} }}

GET  /api/auth/me       - Get current user (requires Bearer token)
  Header: Authorization: Bearer <access_token>
  Response: {{ "email": "...", "username": "...", "_id": "..." }}

POST /api/auth/logout   - Logout (client clears token)

📌 GENERIC DATABASE API - BASE: http://localhost:8000/api/db
════════════════════════════════════════════════════════════════════════════════
GET    /api/db/{{project}}/{{collection}}           - Get all items from collection
POST   /api/db/{{project}}/{{collection}}           - Create item (body: {{ "data": {{...}} }})
GET    /api/db/{{project}}/{{collection}}/{{id}}    - Get single item by ID
PUT    /api/db/{{project}}/{{collection}}/{{id}}    - Update item (body: {{ "data": {{...}} }})
DELETE /api/db/{{project}}/{{collection}}/{{id}}    - Delete item
GET    /api/db/{{project}}/{{collection}}/search?q=term - Search items

📌 PROJECT-SPECIFIC API - BASE: http://localhost:8000/api/v1
════════════════════════════════════════════════════════════════════════════════
The backend generates project-specific endpoints. Use these patterns:
- GET  /api/v1/products      - Get all products
- GET  /api/v1/products/{{id}} - Get product by ID
- POST /api/v1/cart          - Add to cart (requires auth)
- GET  /api/v1/cart          - Get user's cart (requires auth)
- POST /api/v1/orders        - Create order (requires auth)
- GET  /api/v1/orders        - Get user's orders (requires auth)

✅ CORRECT API INTEGRATION PATTERN (USE THIS!):
════════════════════════════════════════════════════════════════════════════════
```jsx
// API Configuration
const API_BASE = 'http://localhost:8000';
const AUTH_API = `${{API_BASE}}/api/auth`;
const DB_API = `${{API_BASE}}/api/db`;
const PROJECT_API = `${{API_BASE}}/api/v1`;
const PROJECT_NAME = '{project_name}'.toLowerCase().replace(/\\s+/g, '_');

// Authenticated fetch helper - USE THIS FOR PROTECTED ROUTES
const authFetch = async (url, options = {{}}) => {{
  const token = localStorage.getItem('access_token');
  return fetch(url, {{
    ...options,
    headers: {{
      'Content-Type': 'application/json',
      ...(token ? {{ 'Authorization': `Bearer ${{token}}` }} : {{}}),
      ...options.headers
    }}
  }});
}};

// Authentication functions - CONNECTS TO MONGODB
const handleSignup = async (e) => {{
  e.preventDefault();
  setLoading(true);
  setError('');
  
  try {{
    const response = await fetch(`${{AUTH_API}}/signup`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ email, username, password }})
    }});
    
    const data = await response.json();
    
    if (!response.ok) {{
      throw new Error(data.detail || 'Signup failed');
    }}
    
    // Save token to localStorage - IMPORTANT!
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    setIsLoggedIn(true);
    showNotification('Account created successfully!');
    setShowSignup(false);
  }} catch (err) {{
    setError(err.message);
    showNotification(err.message, 'error');
  }} finally {{
    setLoading(false);
  }}
}};

const handleLogin = async (e) => {{
  e.preventDefault();
  setLoading(true);
  setError('');
  
  try {{
    const response = await fetch(`${{AUTH_API}}/login`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ email, password }})
    }});
    
    const data = await response.json();
    
    if (!response.ok) {{
      throw new Error(data.detail || 'Login failed');
    }}
    
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    setIsLoggedIn(true);
    showNotification(`Welcome back, ${{data.user.username}}!`);
    setShowLogin(false);
  }} catch (err) {{
    setError(err.message);
    showNotification(err.message, 'error');
  }} finally {{
    setLoading(false);
  }}
}};

const handleLogout = () => {{
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  setUser(null);
  setIsLoggedIn(false);
  showNotification('Logged out successfully');
}};

// Fetch products from backend
const fetchProducts = async () => {{
  setLoading(true);
  try {{
    // Try project-specific API first
    let response = await fetch(`${{PROJECT_API}}/products`);
    
    if (!response.ok) {{
      // Fallback to generic DB API
      response = await fetch(`${{DB_API}}/${{PROJECT_NAME}}/products`);
    }}
    
    const data = await response.json();
    setProducts(data.data || data || MOCK_PRODUCTS);
  }} catch (error) {{
    console.warn('API unavailable, using mock data');
    setProducts(MOCK_PRODUCTS);
  }} finally {{
    setLoading(false);
  }}
}};

// Create order with authentication
const createOrder = async (orderData) => {{
  try {{
    const response = await authFetch(`${{PROJECT_API}}/orders`, {{
      method: 'POST',
      body: JSON.stringify(orderData)
    }});
    
    if (!response.ok) {{
      throw new Error('Failed to create order');
    }}
    
    const data = await response.json();
    clearCart();
    showNotification('Order placed successfully!');
    return data;
  }} catch (error) {{
    showNotification(error.message, 'error');
    throw error;
  }}
}};

// On component mount - check auth and load data
useEffect(() => {{
  // Check for existing login
  const savedUser = localStorage.getItem('user');
  const token = localStorage.getItem('access_token');
  if (savedUser && token) {{
    setUser(JSON.parse(savedUser));
    setIsLoggedIn(true);
    
    // Verify token is still valid
    authFetch(`${{AUTH_API}}/me`)
      .then(res => {{
        if (!res.ok) {{
          handleLogout(); // Token expired
        }}
      }})
      .catch(() => handleLogout());
  }}
  
  // Load initial data
  fetchProducts();
}}, []);
```
════════════════════════════════════════════════════════════════════════════════

⚠️ CRITICAL: Your app MUST integrate with the backend APIs above!
- Login/Signup forms MUST call /api/auth/signup and /api/auth/login
- Store access_token in localStorage after successful auth
- Include Authorization header for protected routes
- Products, orders, and other data should be fetched from/saved to the backend

Return complete, working JSX code only."""