"""
Automatic Error Detection and Fixing Agent
Monitors runtime errors and automatically fixes them in S3
"""

import google.generativeai as genai
import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


class AutoFixAgent:
    """AI agent that automatically detects and fixes runtime errors"""
    
    def __init__(self):
        self.fix_history = []
    
    async def analyze_and_fix_error(
        self, 
        error_message: str, 
        error_stack: str, 
        project_slug: str,
        user_id: str,
        file_path: Optional[str] = None
    ) -> Dict:
        """
        Analyze error and automatically fix it in S3
        
        Args:
            error_message: The error message from console
            error_stack: Stack trace
            project_slug: Project identifier
            user_id: User identifier
            file_path: Optional specific file path where error occurred
            
        Returns:
            Dict with fix status and details
        """
        print(f"🔧 Auto-fix agent triggered for: {error_message[:100]}")
        
        try:
            # Step 1: Parse error to identify problematic file and line
            error_info = self._parse_error(error_message, error_stack, file_path)
            
            if not error_info['file_path']:
                return {
                    'success': False,
                    'error': 'Could not identify file from error',
                    'message': error_message
                }
            
            # Step 2: Get file content from S3
            file_content = self._get_file_from_s3(
                project_slug, 
                user_id, 
                error_info['file_path']
            )
            
            if not file_content:
                return {
                    'success': False,
                    'error': f"Could not retrieve file: {error_info['file_path']}",
                    'message': error_message
                }
            
            # Step 3: Get related files for context
            related_files = await self._get_related_files(
                project_slug,
                user_id,
                error_info['file_path'],
                file_content
            )
            
            # Step 4: Use AI to fix the error
            fixed_content = await self._fix_with_ai(
                error_message=error_message,
                error_stack=error_stack,
                error_info=error_info,
                file_content=file_content,
                related_files=related_files
            )
            
            if not fixed_content:
                return {
                    'success': False,
                    'error': 'AI could not generate fix',
                    'message': error_message
                }
            
            # Step 5: Upload fixed file to S3
            success = self._upload_fixed_file(
                project_slug,
                user_id,
                error_info['file_path'],
                fixed_content
            )
            
            if success:
                fix_record = {
                    'project': project_slug,
                    'file': error_info['file_path'],
                    'error': error_message[:200],
                    'line': error_info.get('line_number'),
                    'timestamp': __import__('datetime').datetime.now().isoformat()
                }
                self.fix_history.append(fix_record)
                
                return {
                    'success': True,
                    'file_path': error_info['file_path'],
                    'error_type': error_info['error_type'],
                    'line_number': error_info.get('line_number'),
                    'fix_applied': True,
                    'message': f"✅ Auto-fixed {error_info['error_type']} in {error_info['file_path']}"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to upload fixed file',
                    'message': error_message
                }
                
        except Exception as e:
            print(f"❌ Auto-fix error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': error_message
            }
    
    def _parse_error(self, error_message: str, error_stack: str, hint_file: Optional[str]) -> Dict:
        """Parse error to extract file path, line number, and error type"""
        
        # Extract error type
        error_type = 'Unknown'
        if 'SyntaxError' in error_message:
            error_type = 'SyntaxError'
        elif 'ReferenceError' in error_message:
            error_type = 'ReferenceError'
        elif 'TypeError' in error_message:
            error_type = 'TypeError'
        elif 'already been declared' in error_message:
            error_type = 'DuplicateDeclaration'
        
        # Extract file path and line number from stack
        file_path = hint_file
        line_number = None
        
        # Parse stack trace for file path
        # Example: "at App.jsx:939:6"
        stack_pattern = r'at\s+([^:]+):(\d+):(\d+)'
        match = re.search(stack_pattern, error_stack)
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
        
        # If still no file, try to extract from error message
        if not file_path:
            # Example: "/Inline Babel script: Identifier 'Button'"
            # or "App.jsx: Identifier 'Button'"
            file_match = re.search(r'([A-Za-z]+\.jsx?)', error_message)
            if file_match:
                file_path = f"frontend/src/{file_match.group(1)}"
        
        # Extract identifier name if duplicate declaration
        identifier = None
        if 'already been declared' in error_message or 'Identifier' in error_message:
            id_match = re.search(r"Identifier\s+'(\w+)'", error_message)
            if id_match:
                identifier = id_match.group(1)
        
        return {
            'error_type': error_type,
            'file_path': file_path,
            'line_number': line_number,
            'identifier': identifier
        }
    
    def _get_file_from_s3(self, project_slug: str, user_id: str, file_path: str) -> Optional[str]:
        """Retrieve file content from S3"""
        try:
            # Try different path patterns
            possible_keys = [
                f"projects/{user_id}/{project_slug}/{file_path}",
                f"projects/{user_id}/{project_slug}/frontend/src/{file_path.split('/')[-1]}",
                f"projects/{user_id}/{project_slug}/frontend/src/App.jsx",  # Common error file
            ]
            
            for key in possible_keys:
                try:
                    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
                    content = response['Body'].read().decode('utf-8')
                    print(f"✅ Retrieved file from S3: {key}")
                    return content
                except ClientError:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error retrieving file: {str(e)}")
            return None
    
    async def _get_related_files(
        self, 
        project_slug: str, 
        user_id: str, 
        main_file: str,
        main_content: str
    ) -> Dict[str, str]:
        """Get related files for context (imports, components, etc.)"""
        related = {}
        
        try:
            # Extract imports from main file
            import_pattern = r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]'
            imports = re.findall(import_pattern, main_content)
            
            for imp in imports[:5]:  # Limit to 5 related files
                # Convert relative import to file path
                if imp.startswith('./'):
                    file_name = imp.replace('./', '') + '.jsx'
                    prefix = f"projects/{user_id}/{project_slug}/frontend/src/"
                    
                    try:
                        response = s3_client.list_objects_v2(
                            Bucket=S3_BUCKET_NAME,
                            Prefix=prefix
                        )
                        
                        if 'Contents' in response:
                            for obj in response['Contents']:
                                if file_name in obj['Key']:
                                    content = s3_client.get_object(
                                        Bucket=S3_BUCKET_NAME,
                                        Key=obj['Key']
                                    )['Body'].read().decode('utf-8')
                                    related[file_name] = content
                                    break
                    except:
                        pass
            
            return related
            
        except Exception as e:
            print(f"⚠️ Could not get related files: {str(e)}")
            return {}
    
    async def _fix_with_ai(
        self,
        error_message: str,
        error_stack: str,
        error_info: Dict,
        file_content: str,
        related_files: Dict[str, str]
    ) -> Optional[str]:
        """Use Gemini AI to fix the error"""
        
        # Build context
        related_context = "\n\n".join([
            f"=== {fname} ===\n{content[:1000]}"
            for fname, content in related_files.items()
        ])
        
        prompt = f"""You are an expert code fixing agent. Fix the following runtime error automatically.

🔴 ERROR:
{error_message}

📍 ERROR DETAILS:
- Type: {error_info['error_type']}
- File: {error_info['file_path']}
- Line: {error_info.get('line_number', 'Unknown')}
- Identifier: {error_info.get('identifier', 'N/A')}

📚 STACK TRACE:
{error_stack[:500]}

📄 FILE CONTENT:
{file_content}

📦 RELATED FILES (for context):
{related_context[:2000] if related_context else 'None'}

🎯 TASK:
1. Identify the root cause of the error
2. Fix it WITHOUT breaking any functionality
3. Return ONLY the complete fixed file content
4. DO NOT include any explanations or markdown
5. Ensure no duplicate declarations
6. Preserve all imports and logic

CRITICAL RULES:
- If error is "Identifier already declared", remove the duplicate declaration
- Keep the FIRST declaration, remove subsequent ones
- Never remove imported components
- Preserve all functionality
- Return valid, runnable code

Return ONLY the fixed code:"""

        try:
            response = model.generate_content(prompt)
            fixed_content = response.text.strip()
            
            # Remove code block markers if present
            if fixed_content.startswith('```'):
                fixed_content = '\n'.join(fixed_content.split('\n')[1:-1])
            
            print(f"✅ AI generated fix ({len(fixed_content)} bytes)")
            return fixed_content
            
        except Exception as e:
            print(f"❌ AI fix failed: {str(e)}")
            return None
    
    def _upload_fixed_file(
        self,
        project_slug: str,
        user_id: str,
        file_path: str,
        content: str
    ) -> bool:
        """Upload fixed file back to S3"""
        try:
            # Construct S3 key
            if not file_path.startswith('projects/'):
                s3_key = f"projects/{user_id}/{project_slug}/{file_path}"
            else:
                s3_key = file_path
            
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='application/javascript',
                Metadata={
                    'auto_fixed': 'true',
                    'fixed_at': __import__('datetime').datetime.now().isoformat()
                }
            )
            
            print(f"✅ Uploaded fixed file to S3: {s3_key}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to upload fixed file: {str(e)}")
            return False


# Global agent instance
auto_fix_agent = AutoFixAgent()
