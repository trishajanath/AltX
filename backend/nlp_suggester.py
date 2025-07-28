def suggest_fixes(headers):
    suggestions = []

    if "Content-Security-Policy" not in headers:
        suggestions.append("Add a Content-Security-Policy header to mitigate XSS and data injection attacks.")

    if "Strict-Transport-Security" not in headers:
        suggestions.append("Add a Strict-Transport-Security header to enforce HTTPS.")

    if "X-Frame-Options" not in headers:
        suggestions.append("Add X-Frame-Options to protect against clickjacking.")

    if "X-XSS-Protection" not in headers:
        suggestions.append("Enable X-XSS-Protection to protect against reflected XSS attacks.")

    if "X-Content-Type-Options" not in headers:
        suggestions.append("Add X-Content-Type-Options to prevent MIME-type sniffing.")

    if "Referrer-Policy" not in headers:
        suggestions.append("Add Referrer-Policy to control referrer info sent with requests.")

    return suggestions

