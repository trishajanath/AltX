def suggest_fixes(headers):
    suggestions = []

    if 'Content-Security-Policy' not in headers:
        suggestions.append("Add a Content-Security-Policy to prevent XSS.")
    if 'X-Frame-Options' not in headers:
        suggestions.append("Add X-Frame-Options to prevent clickjacking.")
    if 'Strict-Transport-Security' not in headers:
        suggestions.append("Use HSTS to enforce HTTPS.")
    if 'X-Content-Type-Options' not in headers:
        suggestions.append("Add X-Content-Type-Options to prevent MIME-sniffing.")

    return suggestions
