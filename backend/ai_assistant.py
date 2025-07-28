from google import genai
from google.genai import types

import os
from typing import List, Dict


client = genai.Client(
    api_key='AIzaSyBHvyscC7Ss8TlN3FXdMlTlh5-maW6Mp1g',
    http_options=types.HttpOptions(api_version='v1alpha')
)

def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict) -> str:
    """
    Analyzes web security scan results using the Gemini Pro model.
    """
    system_prompt = "You are a web security expert helping developers fix insecure websites. Be clear, concise, and provide actionable advice."
    user_prompt = f"""
    A website security scan returned the following data:

    - HTTPS enabled: {https}
    - Missing or insecure headers: {flags}
    - Present headers: {headers}

    Based on this information, please perform the following:
    1. Provide a concise analysis of the site's current security posture.
    2. Suggest specific improvements to mitigate the identified risks.
    3. Recommend exact header values or server configuration snippets (e.g., for Nginx or Apache) for the missing headers.
    """

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        generation_config = types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=800
        )
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-001', 
            contents=full_prompt,
            config=generation_config
        )

        return response.text.strip()
    except Exception as e:
        return f"API Error: {str(e)}"

if __name__ == "__main__":
    https_enabled = True
    missing_headers = [
        "Content-Security-Policy",
        "Permissions-Policy"
    ]
    present_headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff"
    }

    analysis_result = analyze_scan_with_llm(https_enabled, missing_headers, present_headers)

    print("--- Security Analysis Result ---")
    print(analysis_result)
    print("------------------------------")