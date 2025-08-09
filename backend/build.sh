#!/bin/bash

# Professional CI/CD Build Script for AltX Security Scanner
# This script runs inside Docker containers to build projects safely

set -e  # Exit on any error

PROJECT_DIR="/app"
PROJECT_TYPE=""
BUILD_OUTPUT=""

echo "🔧 AltX CI/CD Build System Starting..."
echo "📁 Project Directory: $PROJECT_DIR"
echo "⏰ Build Time: $(date)"

# Function to detect project type
detect_project_type() {
    echo "🔍 Detecting project type..."
    
    if [ -f "$PROJECT_DIR/package.json" ]; then
        PROJECT_TYPE="nodejs"
        echo "📦 Node.js project detected"
    elif [ -f "$PROJECT_DIR/requirements.txt" ] || [ -f "$PROJECT_DIR/setup.py" ]; then
        PROJECT_TYPE="python"
        echo "🐍 Python project detected"
    elif [ -f "$PROJECT_DIR/Dockerfile" ]; then
        PROJECT_TYPE="docker"
        echo "🐳 Docker project detected"
    elif [ -f "$PROJECT_DIR/composer.json" ]; then
        PROJECT_TYPE="php"
        echo "🐘 PHP project detected"
    elif [ -f "$PROJECT_DIR/Cargo.toml" ]; then
        PROJECT_TYPE="rust"
        echo "🦀 Rust project detected"
    elif [ -f "$PROJECT_DIR/go.mod" ]; then
        PROJECT_TYPE="go"
        echo "🐹 Go project detected"
    elif [ -f "$PROJECT_DIR/index.html" ]; then
        PROJECT_TYPE="static"
        echo "📄 Static HTML project detected"
    else
        PROJECT_TYPE="unknown"
        echo "❓ Unknown project type - will treat as static files"
    fi
}

# Function to install dependencies
install_dependencies() {
    echo "⏳ Installing dependencies for $PROJECT_TYPE project..."
    
    case $PROJECT_TYPE in
        "nodejs")
            cd $PROJECT_DIR
            
            # Check for package manager preference
            if [ -f "yarn.lock" ]; then
                echo "📦 Using Yarn package manager"
                yarn install --frozen-lockfile --production=false
            elif [ -f "pnpm-lock.yaml" ]; then
                echo "📦 Using PNPM package manager"
                pnpm install --frozen-lockfile
            else
                echo "📦 Using NPM package manager"
                npm ci || npm install
            fi
            ;;
            
        "python")
            cd $PROJECT_DIR
            echo "🐍 Setting up Python environment"
            
            # Create virtual environment
            python3 -m venv venv
            source venv/bin/activate
            
            # Upgrade pip
            pip install --upgrade pip
            
            # Install dependencies
            if [ -f "requirements.txt" ]; then
                pip install -r requirements.txt
            fi
            
            if [ -f "setup.py" ]; then
                pip install -e .
            fi
            ;;
            
        "php")
            cd $PROJECT_DIR
            echo "🐘 Installing PHP dependencies"
            composer install --no-dev --optimize-autoloader
            ;;
            
        "rust")
            cd $PROJECT_DIR
            echo "🦀 Building Rust project"
            cargo build --release
            ;;
            
        "go")
            cd $PROJECT_DIR
            echo "🐹 Building Go project"
            go mod download
            go build -o main .
            ;;
            
        "static"|"unknown")
            echo "📄 No dependencies to install for static project"
            ;;
    esac
    
    echo "✅ Dependencies installed successfully"
}

# Function to build the project
build_project() {
    echo "🔨 Building $PROJECT_TYPE project..."
    
    case $PROJECT_TYPE in
        "nodejs")
            cd $PROJECT_DIR
            
            # Check package.json for build scripts
            if command -v jq >/dev/null 2>&1; then
                BUILD_SCRIPT=$(jq -r '.scripts.build // empty' package.json)
                DIST_SCRIPT=$(jq -r '.scripts.dist // empty' package.json)
                PROD_SCRIPT=$(jq -r '.scripts.production // empty' package.json)
            fi
            
            # Run build command
            if [ ! -z "$BUILD_SCRIPT" ]; then
                echo "🏗️ Running npm run build"
                npm run build
                
                # Find build output directory
                for dir in "dist" "build" "public" "out" ".next/static"; do
                    if [ -d "$dir" ]; then
                        BUILD_OUTPUT="$dir"
                        echo "📦 Build output found in: $BUILD_OUTPUT"
                        break
                    fi
                done
                
            elif [ ! -z "$DIST_SCRIPT" ]; then
                echo "🏗️ Running npm run dist"
                npm run dist
                BUILD_OUTPUT="dist"
                
            elif [ ! -z "$PROD_SCRIPT" ]; then
                echo "🏗️ Running npm run production"
                npm run production
                BUILD_OUTPUT="dist"
                
            else
                echo "📄 No build script found - treating as static files"
                BUILD_OUTPUT="."
            fi
            ;;
            
        "python")
            cd $PROJECT_DIR
            source venv/bin/activate
            
            # Check for Django
            if [ -f "manage.py" ]; then
                echo "🎯 Django project detected"
                python manage.py collectstatic --noinput --clear || echo "⚠️ collectstatic failed"
                BUILD_OUTPUT="staticfiles"
                
            # Check for Flask
            elif grep -q "Flask" requirements.txt 2>/dev/null; then
                echo "🌶️ Flask project detected"
                BUILD_OUTPUT="."
                
            else
                echo "🐍 Generic Python project"
                BUILD_OUTPUT="."
            fi
            ;;
            
        "php")
            cd $PROJECT_DIR
            echo "🐘 PHP project ready"
            BUILD_OUTPUT="."
            ;;
            
        "rust")
            BUILD_OUTPUT="target/release"
            ;;
            
        "go")
            BUILD_OUTPUT="."
            ;;
            
        "static"|"unknown")
            echo "📄 Static files ready"
            BUILD_OUTPUT="."
            ;;
    esac
    
    echo "✅ Build completed successfully"
    echo "📁 Build output directory: $BUILD_OUTPUT"
}

# Function to optimize build output
optimize_build() {
    echo "⚡ Optimizing build output..."
    
    cd $PROJECT_DIR
    
    if [ "$PROJECT_TYPE" = "nodejs" ] && [ -d "$BUILD_OUTPUT" ]; then
        # Compress JavaScript and CSS if tools are available
        if command -v gzip >/dev/null 2>&1; then
            find "$BUILD_OUTPUT" -name "*.js" -o -name "*.css" | while read file; do
                gzip -k "$file" 2>/dev/null || true
            done
            echo "🗜️ Gzipped static assets"
        fi
    fi
    
    # Remove development files
    find "$BUILD_OUTPUT" -name "*.map" -delete 2>/dev/null || true
    find "$BUILD_OUTPUT" -name "*.log" -delete 2>/dev/null || true
    
    echo "✅ Build optimization completed"
}

# Function to prepare deployment package
prepare_deployment() {
    echo "📦 Preparing deployment package..."
    
    cd $PROJECT_DIR
    
    # Create deployment directory
    mkdir -p /deployment
    
    # Copy build output to deployment directory
    if [ "$BUILD_OUTPUT" = "." ]; then
        # Copy everything except excluded directories
        rsync -av --exclude='.git' --exclude='node_modules' --exclude='.env*' \
               --exclude='*.log' --exclude='.DS_Store' --exclude='__pycache__' \
               --exclude='venv' --exclude='.pytest_cache' \
               "$PROJECT_DIR/" /deployment/
    else
        # Copy specific build output
        cp -r "$PROJECT_DIR/$BUILD_OUTPUT/"* /deployment/ 2>/dev/null || \
        cp -r "$PROJECT_DIR/$BUILD_OUTPUT" /deployment/ 2>/dev/null || \
        echo "⚠️ Build output directory not found, copying project root"
    fi
    
    # Create deployment metadata
    cat > /deployment/.deployment-info << EOL
{
    "project_type": "$PROJECT_TYPE",
    "build_output": "$BUILD_OUTPUT",
    "build_time": "$(date -Iseconds)",
    "build_script_version": "1.0.0"
}
EOL
    
    echo "✅ Deployment package ready"
    echo "📊 Files in deployment:"
    ls -la /deployment/ | head -10
}

# Function to run security scan on build
security_scan() {
    echo "🔒 Running security scan on build output..."
    
    cd $PROJECT_DIR
    
    # Check for common security issues
    if [ -f ".env" ]; then
        echo "⚠️ WARNING: .env file found in project root"
    fi
    
    if [ -f "config/database.yml" ] && grep -q "password" config/database.yml 2>/dev/null; then
        echo "⚠️ WARNING: Potential credentials in database.yml"
    fi
    
    # Check for exposed secrets in build output
    if [ -d "/deployment" ]; then
        SECRET_PATTERNS="password|secret|key|token|api_key"
        if grep -r -i "$SECRET_PATTERNS" /deployment/ --exclude-dir=node_modules 2>/dev/null | head -5; then
            echo "⚠️ WARNING: Potential secrets found in build output"
        fi
    fi
    
    echo "✅ Security scan completed"
}

# Main execution flow
main() {
    echo "🚀 Starting AltX CI/CD Build Process"
    echo "=================================="
    
    detect_project_type
    install_dependencies
    build_project
    optimize_build
    prepare_deployment
    security_scan
    
    echo "=================================="
    echo "✅ Build process completed successfully!"
    echo "📁 Deployment ready in: /deployment"
    echo "🎯 Project type: $PROJECT_TYPE"
    echo "⏰ Completed at: $(date)"
}

# Execute main function
main

# Exit with success
exit 0
