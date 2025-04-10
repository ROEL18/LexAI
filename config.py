import os
import logging

def configure_app(app):
    """Configure Flask application with environment settings."""
    # API keys and credentials
    gemini_key = os.environ.get('GEMINI_KEY', '')
    
    if gemini_key:
        app.logger.info(f"GEMINI_KEY loaded: {gemini_key[:5]}...")
    else:
        app.logger.error("GEMINI_KEY not found in environment")
    
    # Set both config keys to ensure compatibility
    app.config['GEMINI_API_KEY'] = gemini_key
    app.config['GEMINI_KEY'] = gemini_key
    
    # Firebase configuration
    app.config['FIREBASE_API_KEY'] = os.environ.get('FIREBASE_API_KEY', '')
    app.config['FIREBASE_PROJECT_ID'] = os.environ.get('FIREBASE_PROJECT_ID', '')
    app.config['FIREBASE_APP_ID'] = os.environ.get('FIREBASE_APP_ID', '')
    app.config['FIREBASE_AUTH_DOMAIN'] = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    app.config['FIREBASE_STORAGE_BUCKET'] = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    app.config['FIREBASE_MESSAGING_SENDER_ID'] = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    app.config['FIREBASE_DATABASE_URL'] = os.environ.get('FIREBASE_DATABASE_URL', '')
    app.config['FIREBASE_MEASUREMENT_ID'] = os.environ.get('FIREBASE_MEASUREMENT_ID', '')
    
    # File upload configurations
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'doc', 'docx', 'rtf'}
    
    # Session configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "lex-ai-secure-session-key-2025")
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
