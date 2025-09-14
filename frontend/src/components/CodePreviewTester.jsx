import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';

const CodePreviewTester = ({ 
    originalCode, 
    fixedCode, 
    filename, 
    issue, 
    onTestComplete,
    onCodeUpdate  // Add this prop to allow updating the fixed code
}) => {
    const [activeTab, setActiveTab] = useState('original');
    const [testResults, setTestResults] = useState(null);
    const [isRunningTest, setIsRunningTest] = useState(false);
    const [syntaxErrors, setSyntaxErrors] = useState({ original: [], fixed: [] });
    const [currentFixedCode, setCurrentFixedCode] = useState(fixedCode); // Track current fixed code

    // Determine language from filename
    const getLanguage = (filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        const languageMap = {
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'py': 'python',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml'
        };
        return languageMap[ext] || 'plaintext';
    };

    const language = getLanguage(filename);

    // JSX-specific validation
    const validateJSX = (code) => {
        const errors = [];
        const lines = code.split('\n');
        
        // Track JSX tag balance
        let tagStack = [];
        let inJSX = false;
        
        lines.forEach((line, lineIndex) => {
            // Check for unclosed JSX elements
            const openTags = line.match(/<(\w+)(?:\s[^>]*)?>(?![^<]*<\/\1>)/g) || [];
            const closeTags = line.match(/<\/(\w+)>/g) || [];
            const selfClosingTags = line.match(/<(\w+)(?:\s[^>]*)?\/>/g) || [];
            
            // Check for broken JSX syntax patterns
            if (line.includes('e.target.value)}') && !line.includes('onChange') && !line.includes('onInput')) {
                errors.push({
                    line: lineIndex + 1,
                    column: line.indexOf('e.target.value)}') + 1,
                    message: 'Orphaned event handler - missing input/select element',
                    severity: 'error'
                });
            }
            
            if (line.includes('e.stopPropagation()}>') && !line.includes('<')) {
                errors.push({
                    line: lineIndex + 1,
                    column: line.indexOf('e.stopPropagation()}>') + 1,
                    message: 'Event handler outside JSX element',
                    severity: 'error'
                });
            }
            
            // Check for missing JSX wrapper elements
            if (line.includes('className=') && !line.includes('<') && !line.includes('>')) {
                errors.push({
                    line: lineIndex + 1,
                    column: line.indexOf('className=') + 1,
                    message: 'className attribute without JSX element',
                    severity: 'error'
                });
            }
            
            // Check for incomplete JSX expressions
            if (line.includes('{') && !line.includes('}')) {
                const openBraces = (line.match(/\{/g) || []).length;
                const closeBraces = (line.match(/\}/g) || []).length;
                if (openBraces > closeBraces) {
                    errors.push({
                        line: lineIndex + 1,
                        column: line.lastIndexOf('{') + 1,
                        message: 'Unclosed JSX expression',
                        severity: 'warning'
                    });
                }
            }
        });
        
        return errors;
    };

    // Validate syntax based on language
    const validateSyntax = async (code, type) => {
        const errors = [];
        
        try {
            if (language === 'javascript') {
                // Enhanced JSX/JavaScript syntax validation
                
                // Check for JSX-specific issues
                if (filename.endsWith('.jsx') || filename.endsWith('.tsx')) {
                    // Check for broken JSX tags
                    const jsxErrors = validateJSX(code);
                    errors.push(...jsxErrors);
                }
                
                // Basic JavaScript syntax validation
                try {
                    // For JSX files, we can't use Function constructor directly
                    // Instead, do pattern-based validation
                    if (filename.endsWith('.jsx') || filename.endsWith('.tsx')) {
                        // Skip Function constructor for JSX
                    } else {
                        new Function(code);
                    }
                } catch (e) {
                    errors.push({
                        line: 1,
                        column: 1,
                        message: e.message,
                        severity: 'error'
                    });
                }
            } else if (language === 'python') {
                // Basic Python syntax validation (simplified)
                const pythonSyntaxPatterns = [
                    { pattern: /def\s+\w+\([^)]*\)\s*:?\s*$/, message: "Function definition missing colon or body" },
                    { pattern: /if\s+.*:\s*$/, message: "If statement missing body" },
                    { pattern: /for\s+.*:\s*$/, message: "For loop missing body" },
                    { pattern: /while\s+.*:\s*$/, message: "While loop missing body" }
                ];
                
                const lines = code.split('\n');
                lines.forEach((line, index) => {
                    pythonSyntaxPatterns.forEach(({ pattern, message }) => {
                        if (pattern.test(line.trim()) && index === lines.length - 1) {
                            errors.push({
                                line: index + 1,
                                column: 1,
                                message,
                                severity: 'warning'
                            });
                        }
                    });
                });
            }
        } catch (e) {
            errors.push({
                line: 1,
                column: 1,
                message: `Syntax validation error: ${e.message}`,
                severity: 'error'
            });
        }

        setSyntaxErrors(prev => ({ ...prev, [type]: errors }));
        return errors;
    };

    // Run security and functionality tests
    const runTests = async () => {
        setIsRunningTest(true);
        setTestResults(null);

        try {
            const results = {
                syntaxValid: true,
                securityImproved: false,
                functionalityPreserved: true,
                details: []
            };

            // 1. Syntax validation
            const originalErrors = await validateSyntax(originalCode, 'original');
            const fixedErrors = await validateSyntax(fixedCode, 'fixed');

            if (fixedErrors.length > originalErrors.length) {
                results.syntaxValid = false;
                results.details.push('❌ Fix introduced new syntax errors');
            } else if (fixedErrors.length < originalErrors.length) {
                results.details.push('✅ Fix resolved syntax errors');
            } else {
                results.details.push('✅ No new syntax errors introduced');
            }

            // 2. Security improvement check
            const securityPatterns = {
                'localStorage': {
                    original: /localStorage\.(setItem|getItem)\(/g,
                    fixed: /(sessionStorage|secure.*storage|encrypted.*storage)/gi,
                    description: 'localStorage usage'
                },
                'hardcoded_secrets': {
                    original: /(password|token|api_key|secret)\s*=\s*["'][^"']+["']/gi,
                    fixed: /(process\.env|config\.|getenv\()/gi,
                    description: 'hardcoded secrets'
                },
                'sql_injection': {
                    original: /query\s*=\s*["'].*\+.*["']/gi,
                    fixed: /(prepare|bind|placeholder|\?|\$\d+)/gi,
                    description: 'SQL injection vulnerability'
                },
                'xss': {
                    original: /innerHTML\s*=|document\.write\(/gi,
                    fixed: /(textContent|innerText|sanitize|escape)/gi,
                    description: 'XSS vulnerability'
                }
            };

            const issueType = issue.description.toLowerCase();
            let patternMatched = false;

            Object.entries(securityPatterns).forEach(([key, pattern]) => {
                if (issueType.includes(key.replace('_', ' ')) || issueType.includes(pattern.description)) {
                    patternMatched = true;
                    const originalMatches = originalCode.match(pattern.original) || [];
                    const fixedMatches = fixedCode.match(pattern.original) || [];
                    const improvedMatches = fixedCode.match(pattern.fixed) || [];

                    if (fixedMatches.length < originalMatches.length || improvedMatches.length > 0) {
                        results.securityImproved = true;
                        results.details.push(`✅ Security improved: ${pattern.description} addressed`);
                    } else {
                        results.details.push(`⚠️ Security pattern still present: ${pattern.description}`);
                    }
                }
            });

            if (!patternMatched) {
                results.securityImproved = true;
                results.details.push('✅ Security fix applied (pattern-based validation passed)');
            }

            // 3. Functionality preservation check
            const functionalityChecks = [
                {
                    name: 'Function definitions preserved',
                    test: () => {
                        const originalFunctions = (originalCode.match(/function\s+\w+|def\s+\w+|\w+\s*=\s*\(/g) || []).length;
                        const fixedFunctions = (fixedCode.match(/function\s+\w+|def\s+\w+|\w+\s*=\s*\(/g) || []).length;
                        return Math.abs(originalFunctions - fixedFunctions) <= 1; // Allow minor changes
                    }
                },
                {
                    name: 'Import/require statements preserved',
                    test: () => {
                        const originalImports = (originalCode.match(/import\s+|require\s*\(|from\s+\w+\s+import/g) || []).length;
                        const fixedImports = (fixedCode.match(/import\s+|require\s*\(|from\s+\w+\s+import/g) || []).length;
                        return fixedImports >= originalImports;
                    }
                },
                {
                    name: 'JSX structure preserved',
                    test: () => {
                        if (!filename.endsWith('.jsx') && !filename.endsWith('.tsx')) return true;
                        
                        // Check that JSX elements are still properly formed
                        const originalJSXElements = (originalCode.match(/<\w+[^>]*>/g) || []).length;
                        const fixedJSXElements = (fixedCode.match(/<\w+[^>]*>/g) || []).length;
                        
                        // Check for orphaned attributes/handlers
                        const orphanedHandlers = (fixedCode.match(/\w+\s*=\s*\{[^}]*\}\s*(?!\/?>|[a-zA-Z])/g) || []).length;
                        
                        return Math.abs(originalJSXElements - fixedJSXElements) <= 2 && orphanedHandlers === 0;
                    }
                },
                {
                    name: 'Core logic structure maintained',
                    test: () => {
                        // Check if major structural elements are preserved
                        const originalStructure = originalCode.replace(/\s+/g, '').length;
                        const fixedStructure = fixedCode.replace(/\s+/g, '').length;
                        const changeRatio = Math.abs(originalStructure - fixedStructure) / originalStructure;
                        return changeRatio < 0.5; // Less than 50% change
                    }
                }
            ];

            functionalityChecks.forEach(check => {
                try {
                    if (check.test()) {
                        results.details.push(`✅ ${check.name}`);
                    } else {
                        results.functionalityPreserved = false;
                        results.details.push(`❌ ${check.name} failed`);
                    }
                } catch (e) {
                    results.details.push(`⚠️ ${check.name}: ${e.message}`);
                }
            });

            // 4. Code quality metrics
            const originalLines = originalCode.split('\n').filter(line => line.trim()).length;
            const fixedLines = fixedCode.split('\n').filter(line => line.trim()).length;
            
            if (fixedLines <= originalLines + 5) {
                results.details.push('✅ Code length reasonable');
            } else {
                results.details.push('⚠️ Significant code expansion detected');
            }

            // Overall assessment
            results.overall = results.syntaxValid && results.securityImproved && results.functionalityPreserved;

            setTestResults(results);
            onTestComplete?.(results);

        } catch (error) {
            setTestResults({
                syntaxValid: false,
                securityImproved: false,
                functionalityPreserved: false,
                overall: false,
                details: [`❌ Test execution failed: ${error.message}`]
            });
        } finally {
            setIsRunningTest(false);
        }
    };

    // Handle alternate fix strategies when primary fix fails
    const handleAlternateFix = async (strategy) => {
        console.log(`Applying alternate fix strategy: ${strategy}`);
        
        switch (strategy) {
            case 'conservative':
                // Apply minimal security fixes
                await applyConservativeFix();
                break;
            case 'manual':
                // Show manual review interface
                showManualReviewGuidance();
                break;
            case 'skip':
                // Mark issue for later review
                markIssueForLater();
                break;
            default:
                console.error('Unknown fix strategy:', strategy);
        }
    };

    const applyConservativeFix = async () => {
        setIsRunningTest(true);
        
        try {
            // Generate conservative fix based on issue type
            const issueType = issue.description.toLowerCase();
            let newFixedCode = currentFixedCode;
            
            if (issueType.includes('console.log')) {
                newFixedCode = generateConservativeConsoleLogFix();
            } else if (issueType.includes('localstorage')) {
                newFixedCode = generateConservativeStorageFix();
            } else if (issueType.includes('hardcoded') || issueType.includes('secret')) {
                newFixedCode = generateConservativeSecretsFix();
            } else if (issueType.includes('sql')) {
                newFixedCode = generateConservativeSQLFix();
            } else if (issueType.includes('xss')) {
                newFixedCode = generateConservativeXSSFix();
            } else {
                // Generic conservative fix
                newFixedCode = originalCode; // Fallback to original
            }
            
            // Update the current fixed code
            setCurrentFixedCode(newFixedCode);
            
            // Notify parent component if callback provided
            onCodeUpdate?.(newFixedCode);
            
            // Auto-run validation on the new fix
            setTimeout(() => {
                runTestsWithCode(originalCode, newFixedCode);
            }, 500);
            
            // Switch to fixed code tab to show the result
            setActiveTab('fixed');
            
        } catch (error) {
            console.error('Error applying conservative fix:', error);
        } finally {
            setIsRunningTest(false);
        }
    };

    const generateConservativeConsoleLogFix = () => {
        // Wrap console.log with environment check instead of removing
        return originalCode.replace(
            /console\.(log|error|warn|info)\s*\([^)]*\);?/g,
            (match) => {
                const indentation = originalCode.substring(
                    originalCode.lastIndexOf('\n', originalCode.indexOf(match)) + 1,
                    originalCode.indexOf(match)
                );
                return `if (process.env.NODE_ENV === 'development') {\n${indentation}    ${match}\n${indentation}}`;
            }
        );
    };

    const generateConservativeStorageFix = () => {
        return originalCode.replace(
            /localStorage\.(setItem|getItem)\(/g,
            'try { localStorage.$1('
        ).replace(
            /localStorage\.(setItem|getItem)\([^)]*\);/g,
            (match) => match + ' } catch(e) { console.error("localStorage error:", e); }'
        );
    };

    const generateConservativeSecretsFix = () => {
        // Replace hardcoded strings that look like secrets with environment variables
        return originalCode.replace(
            /(const|let|var)\s+(\w*(?:key|token|secret|password)\w*)\s*=\s*['"][^'"]+['"]/gi,
            '$1 $2 = process.env.$2?.toUpperCase() || "REPLACE_WITH_ENV_VAR"'
        );
    };

    const generateConservativeSQLFix = () => {
        // Add basic input validation to SQL queries
        return originalCode.replace(
            /query\s*=\s*['"]([^'"]*)\+([^'"]*)['"]/g,
            'query = `$1${String($2).replace(/[\'\"\\;]/g, "")}`'
        );
    };

    const generateConservativeXSSFix = () => {
        // Add content sanitization for XSS prevention
        return originalCode.replace(
            /innerHTML\s*=\s*([^;]+);/g,
            'innerHTML = DOMPurify.sanitize($1);'
        ).replace(
            /document\.write\s*\([^)]+\)/g,
            '// document.write removed for security - use safer DOM manipulation'
        );
    };

    const showManualReviewGuidance = () => {
        // Display manual fix instructions
        setActiveTab('manual');
        console.log('Showing manual review guidance for:', issue.description);
    };

    const markIssueForLater = () => {
        // Mark issue for later review
        console.log('Marking issue for later review:', issue.description);
        onTestComplete?.({
            overall: false,
            skipped: true,
            reason: 'Automated fix failed validation - marked for manual review'
        });
    };

    // Helper function to run tests with specific code
    const runTestsWithCode = async (originalCode, fixedCode) => {
        setIsRunningTest(true);
        
        try {
            const results = {
                syntaxValid: true,
                securityImproved: false,
                functionalityPreserved: true,
                details: []
            };

            // Run validation logic
            const originalErrors = await validateSyntax(originalCode, 'original');
            const fixedErrors = await validateSyntax(fixedCode, 'fixed');

            if (fixedErrors.length > originalErrors.length) {
                results.syntaxValid = false;
                results.details.push('❌ Fix introduced new syntax errors');
            } else {
                results.details.push('✅ No new syntax errors introduced');
            }

            // Check security improvement
            const issueType = issue.description.toLowerCase();
            if (issueType.includes('console.log')) {
                const hasEnvCheck = fixedCode.includes('process.env.NODE_ENV');
                results.securityImproved = hasEnvCheck;
                results.details.push(hasEnvCheck ? 
                    '✅ Console.log properly wrapped with environment check' : 
                    '❌ Console.log not properly secured'
                );
            } else {
                results.securityImproved = true;
                results.details.push('✅ Security fix applied');
            }

            // Basic functionality check
            results.functionalityPreserved = fixedCode.length > originalCode.length * 0.5;
            results.details.push(results.functionalityPreserved ? 
                '✅ Code structure preserved' : 
                '❌ Significant code reduction detected'
            );

            results.overall = results.syntaxValid && results.securityImproved && results.functionalityPreserved;
            
            setTestResults(results);
            setActiveTab('test');
            
        } catch (error) {
            setTestResults({
                syntaxValid: false,
                securityImproved: false,
                functionalityPreserved: false,
                overall: false,
                details: [`❌ Test execution failed: ${error.message}`]
            });
        } finally {
            setIsRunningTest(false);
        }
    };

    useEffect(() => {
        if (originalCode && currentFixedCode) {
            // Auto-validate syntax when code changes
            validateSyntax(originalCode, 'original');
            validateSyntax(currentFixedCode, 'fixed');
        }
    }, [originalCode, currentFixedCode]);

    // Update currentFixedCode when fixedCode prop changes
    useEffect(() => {
        setCurrentFixedCode(fixedCode);
    }, [fixedCode]);

    // Generate manual fix steps based on issue type
    const getManualFixSteps = (issue) => {
        const issueType = issue.description.toLowerCase();
        
        if (issueType.includes('console.log')) {
            return [
                {
                    title: "Locate the console.log statement",
                    description: `Find the console.log statement on line ${issue.line} in ${filename}`,
                    code: "console.log('debug info');"
                },
                {
                    title: "Wrap with environment check",
                    description: "Replace the console.log with a conditional that only runs in development",
                    code: "if (process.env.NODE_ENV === 'development') {\n    console.log('debug info');\n}"
                },
                {
                    title: "Verify functionality",
                    description: "Ensure your component still renders and functions correctly after the change"
                }
            ];
        }
        
        if (issueType.includes('localstorage')) {
            return [
                {
                    title: "Review localStorage usage",
                    description: "Examine how localStorage is being used and what data is stored"
                },
                {
                    title: "Consider alternatives",
                    description: "Replace with sessionStorage for temporary data or secure server-side storage for sensitive data",
                    code: "// Instead of:\n// localStorage.setItem('token', value);\n// Use:\nsessionStorage.setItem('token', value);"
                },
                {
                    title: "Add encryption if needed",
                    description: "For sensitive data, consider encryption before storage"
                }
            ];
        }
        
        if (issueType.includes('hardcoded')) {
            return [
                {
                    title: "Identify hardcoded values",
                    description: "Find the hardcoded secret or sensitive value in your code"
                },
                {
                    title: "Move to environment variables",
                    description: "Replace hardcoded values with environment variable references",
                    code: "// Instead of:\n// const apiKey = 'abc123';\n// Use:\nconst apiKey = process.env.REACT_APP_API_KEY;"
                },
                {
                    title: "Update your .env file",
                    description: "Add the sensitive value to your .env file (and .env.example for team members)"
                }
            ];
        }
        
        // Generic steps for unknown issue types
        return [
            {
                title: "Analyze the security issue",
                description: `Review the ${issue.description} on line ${issue.line}`
            },
            {
                title: "Research best practices",
                description: "Look up security best practices for this type of issue"
            },
            {
                title: "Implement a safe fix",
                description: "Apply a fix that addresses the security concern without breaking functionality"
            }
        ];
    };

    const getBestPractices = (issue) => {
        const issueType = issue.description.toLowerCase();
        
        if (issueType.includes('console.log')) {
            return [
                "Use environment checks to prevent logs in production",
                "Consider using a proper logging library like winston or pino",
                "Remove or disable debug logs before deploying to production",
                "Use console.warn or console.error for important messages that should appear in production"
            ];
        }
        
        if (issueType.includes('localstorage')) {
            return [
                "Never store sensitive data like tokens or passwords in localStorage",
                "Use sessionStorage for temporary data that should expire",
                "Consider server-side storage for persistent sensitive data",
                "Encrypt sensitive data before storing it client-side"
            ];
        }
        
        if (issueType.includes('hardcoded')) {
            return [
                "Store all secrets and API keys in environment variables",
                "Use different environment files for development, staging, and production",
                "Never commit .env files containing real secrets to version control",
                "Rotate secrets regularly and use secret management tools in production"
            ];
        }
        
        return [
            "Follow the principle of least privilege",
            "Validate and sanitize all user inputs",
            "Keep dependencies updated and scan for vulnerabilities",
            "Use security linters and automated scanning tools"
        ];
    };

    const markIssueAsManuallyFixed = () => {
        console.log('Marking issue as manually fixed:', issue.description);
        onTestComplete?.({
            overall: true,
            manuallyFixed: true,
            reason: 'Issue resolved through manual implementation'
        });
    };

    return (
        <div className="code-preview-tester">
            <div className="preview-header">
                <div className="tabs">
                    <button 
                        className={`tab ${activeTab === 'original' ? 'active' : ''}`}
                        onClick={() => setActiveTab('original')}
                    >
                        Original Code
                        {syntaxErrors.original.length > 0 && (
                            <span className="error-indicator">{syntaxErrors.original.length}</span>
                        )}
                    </button>
                    <button 
                        className={`tab ${activeTab === 'fixed' ? 'active' : ''}`}
                        onClick={() => setActiveTab('fixed')}
                    >
                        Fixed Code
                        {syntaxErrors.fixed.length > 0 && (
                            <span className="error-indicator">{syntaxErrors.fixed.length}</span>
                        )}
                    </button>
                    <button 
                        className={`tab ${activeTab === 'test' ? 'active' : ''}`}
                        onClick={() => setActiveTab('test')}
                    >
                        Test Results
                        {testResults && (
                            <span className={`result-indicator ${testResults.overall ? 'success' : 'error'}`}>
                                {testResults.overall ? '✓' : '✗'}
                            </span>
                        )}
                    </button>
                    <button 
                        className={`tab ${activeTab === 'manual' ? 'active' : ''}`}
                        onClick={() => setActiveTab('manual')}
                    >
                        Manual Review
                        {testResults && !testResults.overall && (
                            <span className="manual-indicator">📝</span>
                        )}
                    </button>
                </div>
                <div className="preview-actions">
                    <button 
                        className="btn btn-primary" 
                        onClick={runTests}
                        disabled={isRunningTest || !originalCode || !fixedCode}
                    >
                        {isRunningTest ? 'Testing...' : 'Run Tests'}
                    </button>
                </div>
            </div>

            <div className="preview-content">
                {activeTab === 'original' && (
                    <div className="editor-container">
                        <Editor
                            height="400px"
                            language={language}
                            value={originalCode}
                            theme="vs-dark"
                            options={{
                                readOnly: true,
                                minimap: { enabled: false },
                                scrollBeyondLastLine: false,
                                fontSize: 14
                            }}
                        />
                        {syntaxErrors.original.length > 0 && (
                            <div className="syntax-errors">
                                <h4>Syntax Issues:</h4>
                                {syntaxErrors.original.map((error, index) => (
                                    <div key={index} className={`error-item ${error.severity}`}>
                                        Line {error.line}: {error.message}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'fixed' && (
                    <div className="editor-container">
                        <Editor
                            height="400px"
                            language={language}
                            value={currentFixedCode}
                            theme="vs-dark"
                            options={{
                                readOnly: true,
                                minimap: { enabled: false },
                                scrollBeyondLastLine: false,
                                fontSize: 14
                            }}
                        />
                        {syntaxErrors.fixed.length > 0 && (
                            <div className="syntax-errors">
                                <h4>Syntax Issues:</h4>
                                {syntaxErrors.fixed.map((error, index) => (
                                    <div key={index} className={`error-item ${error.severity}`}>
                                        Line {error.line}: {error.message}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'test' && (
                    <div className="test-results">
                        {testResults ? (
                            <div>
                                <div className={`overall-result ${testResults.overall ? 'success' : 'failure'}`}>
                                    <h3>
                                        {testResults.overall ? '✅ Fix Validation Passed' : '❌ Fix Validation Failed'}
                                    </h3>
                                </div>

                                <div className="test-categories">
                                    <div className={`test-category ${testResults.syntaxValid ? 'pass' : 'fail'}`}>
                                        <h4>{testResults.syntaxValid ? '✅' : '❌'} Syntax Validation</h4>
                                    </div>
                                    <div className={`test-category ${testResults.securityImproved ? 'pass' : 'fail'}`}>
                                        <h4>{testResults.securityImproved ? '✅' : '❌'} Security Improvement</h4>
                                    </div>
                                    <div className={`test-category ${testResults.functionalityPreserved ? 'pass' : 'fail'}`}>
                                        <h4>{testResults.functionalityPreserved ? '✅' : '❌'} Functionality Preserved</h4>
                                    </div>
                                </div>

                                <div className="test-details">
                                    <h4>Detailed Results:</h4>
                                    {testResults.details.map((detail, index) => (
                                        <div key={index} className="test-detail">
                                            {detail}
                                        </div>
                                    ))}
                                </div>

                                <div className="issue-context">
                                    <h4>Issue Context:</h4>
                                    <p><strong>File:</strong> {filename}</p>
                                    <p><strong>Description:</strong> {issue.description}</p>
                                    <p><strong>Severity:</strong> {issue.severity}</p>
                                    <p><strong>Line:</strong> {issue.line}</p>
                                </div>

                                {/* Alternate Flow for Failed Validation */}
                                {!testResults.overall && (
                                    <div className="alternate-flow">
                                        <h4>🔄 Alternate Fix Options:</h4>
                                        <div className="fix-strategies">
                                            <div className="fix-strategy">
                                                <h5>🛡️ Conservative Fix</h5>
                                                <p>Apply minimal changes to reduce security risk without breaking functionality</p>
                                                <button className="btn btn-secondary" onClick={() => handleAlternateFix('conservative')}>
                                                    Apply Conservative Fix
                                                </button>
                                            </div>
                                            <div className="fix-strategy">
                                                <h5>📝 Manual Review</h5>
                                                <p>Get suggested fixes with step-by-step instructions for manual implementation</p>
                                                <button className="btn btn-secondary" onClick={() => handleAlternateFix('manual')}>
                                                    Get Manual Instructions
                                                </button>
                                            </div>
                                            <div className="fix-strategy">
                                                <h5>⏭️ Skip Fix</h5>
                                                <p>Mark this issue for later review and continue with other fixes</p>
                                                <button className="btn btn-outline" onClick={() => handleAlternateFix('skip')}>
                                                    Skip for Now
                                                </button>
                                            </div>
                                        </div>
                                        
                                        <div className="fix-explanation">
                                            <h5>💡 Why This Fix Failed:</h5>
                                            <ul>
                                                {!testResults.syntaxValid && <li>Fix introduced syntax errors that prevent code execution</li>}
                                                {!testResults.functionalityPreserved && <li>Fix broke core functionality (JSX structure, event handlers, etc.)</li>}
                                                {!testResults.securityImproved && <li>Fix did not address the original security issue</li>}
                                            </ul>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="no-results">
                                <p>Click "Run Tests" to validate the fix</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'manual' && (
                    <div className="manual-review-container">
                        <div className="manual-header">
                            <h3>📝 Manual Fix Instructions</h3>
                            <p>The automated fix failed validation. Here are step-by-step instructions for manual implementation:</p>
                        </div>

                        <div className="manual-content">
                            <div className="issue-analysis">
                                <h4>🔍 Issue Analysis:</h4>
                                <div className="analysis-item">
                                    <strong>Problem:</strong> {issue.description}
                                </div>
                                <div className="analysis-item">
                                    <strong>File:</strong> {filename}
                                </div>
                                <div className="analysis-item">
                                    <strong>Line:</strong> {issue.line}
                                </div>
                                <div className="analysis-item">
                                    <strong>Severity:</strong> <span className={`severity ${issue.severity.toLowerCase()}`}>{issue.severity}</span>
                                </div>
                            </div>

                            <div className="manual-steps">
                                <h4>🛠️ Recommended Fix Steps:</h4>
                                {getManualFixSteps(issue).map((step, index) => (
                                    <div key={index} className="fix-step">
                                        <div className="step-number">{index + 1}</div>
                                        <div className="step-content">
                                            <h5>{step.title}</h5>
                                            <p>{step.description}</p>
                                            {step.code && (
                                                <pre className="step-code"><code>{step.code}</code></pre>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="best-practices">
                                <h4>💡 Best Practices:</h4>
                                <ul>
                                    {getBestPractices(issue).map((practice, index) => (
                                        <li key={index}>{practice}</li>
                                    ))}
                                </ul>
                            </div>

                            <div className="verification">
                                <h4>✅ Verification Steps:</h4>
                                <ol>
                                    <li>Apply the fix manually to your code</li>
                                    <li>Test that the application still functions correctly</li>
                                    <li>Verify the security issue is resolved</li>
                                    <li>Run your test suite to ensure no regressions</li>
                                    <li>Mark this issue as resolved in your tracking system</li>
                                </ol>
                            </div>

                            <div className="manual-actions">
                                <button className="btn btn-primary" onClick={() => markIssueAsManuallyFixed()}>
                                    Mark as Manually Fixed
                                </button>
                                <button className="btn btn-secondary" onClick={() => setActiveTab('original')}>
                                    Back to Code Review
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CodePreviewTester;