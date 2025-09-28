"""
AltX Security Scanner - Nginx Configuration Generator
Generates and manages Nginx configurations for deployed projects
"""

import os
import subprocess
from pathlib import Path

class NginxConfigManager:
    def __init__(self):
        self.nginx_dir = "/etc/nginx"
        self.sites_available = "/etc/nginx/sites-available"
        self.sites_enabled = "/etc/nginx/sites-enabled"
        self.altx_config_dir = "/Users/trishajanath/AltX/nginx-configs"
        
        # Create AltX nginx config directory
        os.makedirs(self.altx_config_dir, exist_ok=True)
    
    def generate_site_config(self, repo_name: str, document_root: str, project_type: str = "static") -> str:
        """Generate Nginx site configuration"""
        
        config_content = f"""
# AltX Security Scanner - Auto-generated Nginx Configuration
# Repository: {repo_name}
# Project Type: {project_type}
# Generated: $(date)

server {{
    listen 80;
    listen [::]:80;
    
    server_name {repo_name}.legal-actively-glider.ngrok-free.app;
    
    # Document root
    root {document_root};
    index index.html index.htm index.php;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Main location block
    location / {{
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \\.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # Security: Deny access to sensitive files
    location ~ /\\. {{
        deny all;
    }}
    
    location ~ ^/(config|logs|cache|vendor|node_modules)/ {{
        deny all;
    }}
    
    # PHP handling (if PHP project)
    {self._get_php_config() if project_type == "php" else ""}
    
    # Node.js proxy (if Node.js app with server)
    {self._get_nodejs_proxy_config(repo_name) if project_type == "nodejs_server" else ""}
    
    # Logging
    access_log /var/log/nginx/{repo_name}_access.log;
    error_log /var/log/nginx/{repo_name}_error.log;
}}

# HTTPS redirect (when SSL is configured)
# server {{
#     listen 443 ssl http2;
#     listen [::]:443 ssl http2;
#     server_name {repo_name}.legal-actively-glider.ngrok-free.app;
#     
#     # SSL configuration would go here
#     # ssl_certificate /path/to/cert.pem;
#     # ssl_certificate_key /path/to/key.pem;
# }}
"""
        
        return config_content
    
    def _get_php_config(self) -> str:
        """Get PHP-specific Nginx configuration"""
        return r"""
    # PHP-FPM handling
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
    }
"""
    
    def _get_nodejs_proxy_config(self, repo_name: str) -> str:
        """Get Node.js proxy configuration"""
        return f"""
    # Proxy to Node.js application
    location /api/ {{
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
"""
    
    def create_site_config(self, repo_name: str, document_root: str, project_type: str = "static") -> dict:
        """Create and save Nginx site configuration"""
        try:
            # Generate configuration
            config_content = self.generate_site_config(repo_name, document_root, project_type)
            
            # Save to AltX config directory
            config_file = os.path.join(self.altx_config_dir, f"{repo_name}.conf")
            
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            print(f"✅ Nginx configuration created: {config_file}")
            
            return {
                "success": True,
                "config_file": config_file,
                "repo_name": repo_name,
                "document_root": document_root,
                "project_type": project_type
            }
            
        except Exception as e:
            print(f"❌ Failed to create Nginx config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def install_site_config(self, repo_name: str) -> dict:
        """Install site configuration to Nginx (requires sudo)"""
        try:
            source_config = os.path.join(self.altx_config_dir, f"{repo_name}.conf")
            target_config = os.path.join(self.sites_available, f"altx-{repo_name}")
            symlink_path = os.path.join(self.sites_enabled, f"altx-{repo_name}")
            
            if not os.path.exists(source_config):
                raise Exception(f"Configuration file not found: {source_config}")
            
            # Copy to sites-available (requires sudo)
            subprocess.run([
                "sudo", "cp", source_config, target_config
            ], check=True)
            
            # Create symlink in sites-enabled (requires sudo)
            subprocess.run([
                "sudo", "ln", "-sf", target_config, symlink_path
            ], check=True)
            
            # Test Nginx configuration
            result = subprocess.run([
                "sudo", "nginx", "-t"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Nginx configuration test failed: {result.stderr}")
            
            # Reload Nginx
            subprocess.run([
                "sudo", "systemctl", "reload", "nginx"
            ], check=True)
            
            print(f"✅ Nginx configuration installed and reloaded for {repo_name}")
            
            return {
                "success": True,
                "message": f"Nginx configured for {repo_name}",
                "config_path": target_config,
                "enabled": True
            }
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Nginx installation failed: {e}")
            return {
                "success": False,
                "error": f"Command failed: {e}"
            }
        except Exception as e:
            print(f"❌ Nginx installation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_altx_sites(self) -> list:
        """List all AltX-managed sites"""
        try:
            configs = []
            if os.path.exists(self.altx_config_dir):
                for file in os.listdir(self.altx_config_dir):
                    if file.endswith('.conf'):
                        repo_name = file.replace('.conf', '')
                        configs.append({
                            "repo_name": repo_name,
                            "config_file": os.path.join(self.altx_config_dir, file),
                            "nginx_enabled": os.path.exists(
                                os.path.join(self.sites_enabled, f"altx-{repo_name}")
                            )
                        })
            return configs
        except Exception as e:
            print(f"❌ Error listing sites: {e}")
            return []

# Usage example
if __name__ == "__main__":
    nginx = NginxConfigManager()
    
    # Example usage
    result = nginx.create_site_config(
        repo_name="security-scanner-test-repo",
        document_root="/Users/trishajanath/AltX/deployments/security-scanner-test-repo",
        project_type="static"
    )
    
    print("Configuration result:", result)
