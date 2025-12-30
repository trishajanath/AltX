"""Comprehensive fix for the e-commerce project - Fix all issues"""
from s3_storage import s3_client, S3_BUCKET_NAME
import re

project_id = '6917910c004fca6f164755e6'
project_name = 'e-commerce-selling-groceries-736975'

def get_file(path):
    key = f'projects/{project_id}/{project_name}/{path}'
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"❌ Could not fetch {path}: {e}")
        return None

def put_file(path, content, content_type='text/javascript'):
    key = f'projects/{project_id}/{project_name}/{path}'
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=content.encode('utf-8'), ContentType=content_type)
    print(f"✅ Uploaded {path}")

# ==================== FIX 1: Button Component ====================
print("\n=== FIXING Button.jsx ===")
button_jsx = '''// motion is provided globally by the sandbox environment
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className = '',
  type = 'button',
  ...props
}) => {
  const baseClasses = 'relative inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg hover:shadow-xl focus:ring-cyan-500',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-white shadow-md hover:shadow-lg focus:ring-slate-500',
    outline: 'border-2 border-current bg-transparent hover:bg-white/10 text-current focus:ring-current',
    ghost: 'bg-transparent hover:bg-white/10 text-current focus:ring-white/20',
    danger: 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-400 hover:to-pink-500 text-white shadow-lg focus:ring-red-500',
    success: 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white shadow-lg focus:ring-green-500',
    default: 'bg-slate-600 hover:bg-slate-500 text-white shadow-md focus:ring-slate-400'
  };

  const sizes = {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
    xl: 'px-8 py-4 text-lg'
  };

  const variantClass = variants[variant] || variants.primary;
  const sizeClass = sizes[size] || sizes.md;

  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.02, y: disabled ? 0 : -1 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      type={type}
      className={`${baseClasses} ${variantClass} ${sizeClass} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </motion.button>
  );
};

export default Button;
'''
put_file('frontend/src/components/ui/Button.jsx', button_jsx)

# ==================== FIX 2: CSS - Remove double braces ====================
print("\n=== FIXING index.css ===")
css_content = get_file('frontend/src/index.css')
if css_content:
    if '{{' in css_content or '}}' in css_content:
        css_content = css_content.replace('{{', '{').replace('}}', '}')
        put_file('frontend/src/index.css', css_content, 'text/css')
        print("   Fixed double braces in CSS")
    else:
        print("   CSS already fixed")

# ==================== FIX 3: App.jsx - Add min-h-screen and ensure exports ====================
print("\n=== FIXING App.jsx ===")
app_jsx = get_file('frontend/src/App.jsx')
if app_jsx:
    fixes = []
    
    # Fix 1: Add min-h-screen to main container
    if 'min-h-screen' not in app_jsx:
        app_jsx = app_jsx.replace(
            '<div className="bg-slate-900 font-sans">',
            '<div className="min-h-screen bg-slate-900 font-sans">'
        )
        fixes.append("Added min-h-screen")
    
    # Fix 2: Ensure export default App at the end
    if 'export default App' not in app_jsx:
        app_jsx = app_jsx.rstrip() + '\n\nexport default App;\n'
        fixes.append("Added export default App")
    
    # Fix 3: Remove any duplicate exports
    export_count = app_jsx.count('export default')
    if export_count > 1:
        # Remove all exports except keep one at end
        app_jsx = re.sub(r'export default \w+;\s*', '', app_jsx)
        app_jsx = app_jsx.rstrip() + '\n\nexport default App;\n'
        fixes.append(f"Fixed {export_count} duplicate exports")
    
    if fixes:
        put_file('frontend/src/App.jsx', app_jsx)
        print(f"   Applied fixes: {', '.join(fixes)}")
    else:
        print("   App.jsx looks good")

# ==================== FIX 4: Card Component ====================
print("\n=== FIXING Card.jsx ===")
card_jsx = '''// motion is provided globally by the sandbox environment
export const Card = ({
  children,
  className = '',
  hover = true,
  ...props
}) => {
  const baseClasses = 'bg-slate-800/60 backdrop-blur-sm ring-1 ring-white/10 rounded-xl overflow-hidden';
  
  const CardContent = (
    <div className={`${baseClasses} ${className}`} {...props}>
      {children}
    </div>
  );

  if (hover) {
    return (
      <motion.div
        whileHover={{ y: -4, scale: 1.01 }}
        transition={{ duration: 0.2 }}
      >
        {CardContent}
      </motion.div>
    );
  }

  return CardContent;
};

export default Card;
'''
put_file('frontend/src/components/ui/Card.jsx', card_jsx)

# ==================== FIX 5: Input Component ====================
print("\n=== FIXING Input.jsx ===")
input_jsx = '''// motion is provided globally by the sandbox environment
export const Input = ({
  type = 'text',
  placeholder = '',
  value,
  onChange,
  className = '',
  disabled = false,
  label = '',
  error = '',
  ...props
}) => {
  const baseClasses = 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all duration-200';
  
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>
      )}
      <motion.input
        whileFocus={{ scale: 1.01 }}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`${baseClasses} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${error ? 'border-red-500' : ''} ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
};

export default Input;
'''
put_file('frontend/src/components/ui/Input.jsx', input_jsx)

# ==================== FIX 6: Loading Component ====================
print("\n=== FIXING Loading.jsx ===")
loading_jsx = '''// motion is provided globally by the sandbox environment
export const Loading = ({ size = 'md', className = '', text = '' }) => {
  const sizes = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const sizeClass = sizes[size] || sizes.md;

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        className={`${sizeClass} border-2 border-cyan-500/30 border-t-cyan-500 rounded-full`}
      />
      {text && (
        <p className="mt-3 text-slate-400 text-sm">{text}</p>
      )}
    </div>
  );
};

export default Loading;
'''
put_file('frontend/src/components/ui/Loading.jsx', loading_jsx)

print("\n✅ All fixes applied! Refresh your browser to see the improvements.")
