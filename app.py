import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import json
import uuid
import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
from config import configure_app
configure_app(app)

# Firebase configuration
try:
    import firebase_config
    app.logger.info("Firebase configuration loaded")
except ImportError:
    app.logger.warning("Firebase configuration not found. Firebase features will be disabled.")

# Import utilities after app configuration
from utils.gemini_api import analyze_text_with_gemini
from utils.document_parser import extract_text_from_document

# Helper functions
def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_firebase_config_for_template():
    """Get Firebase configuration for templates."""
    firebase_config = {}
    try:
        from firebase_config import get_firebase_config
        firebase_config = get_firebase_config()
    except ImportError:
        app.logger.warning("Firebase config module not available")
    
    return {
        'firebase_api_key': firebase_config.get('apiKey', app.config.get('FIREBASE_API_KEY', '')),
        'firebase_project_id': firebase_config.get('projectId', app.config.get('FIREBASE_PROJECT_ID', '')),
        'firebase_app_id': firebase_config.get('appId', app.config.get('FIREBASE_APP_ID', ''))
    }

def get_legal_bert_validation(text, analysis_type='compliance'):
    """Simulate a Legal BERT validation result"""
    # This would typically be a call to a specific model or API
    # For now, we'll generate a simulated validation based on text length
    text_length = len(text)
    
    # Generate compliance score based on text length (just for demonstration)
    # In a real implementation, this would come from an actual ML model
    compliance_score = min(0.95, max(0.35, (text_length % 100) / 100))
    
    # Determine status based on score
    if compliance_score > 0.85:
        status = 'valid'
        red_flags = 0
    elif compliance_score > 0.65:
        status = 'review_recommended'
        red_flags = 2
    else:
        status = 'potential_issues'
        red_flags = 5
    
    # Identify common legal terms
    legal_terms = []
    common_terms = ['agreement', 'contract', 'party', 'liability', 'indemnity', 
                   'term', 'clause', 'herein', 'pursuant', 'warrant']
    
    for term in common_terms:
        if term in text.lower():
            legal_terms.append(term)
    
    return {
        'compliance_status': status,
        'compliance_score': compliance_score,
        'legal_terms_found': legal_terms,
        'red_flags_count': red_flags
    }

# Routes
@app.route('/')
def index():
    """Render the homepage."""
    # Get Firebase config using the helper function
    firebase_config = get_firebase_config_for_template()
    
    # Pass Firebase configuration to the template
    return render_template('index.html', **firebase_config)

@app.route('/login')
def login():
    """Render the login page."""
    # Get Firebase config using the helper function
    firebase_config = get_firebase_config_for_template()
    
    # Pass Firebase configuration to the template
    return render_template('login.html', **firebase_config)

@app.route('/document-analysis')
def document_analysis():
    """Render the document analysis page."""
    # Get Firebase config using the helper function
    firebase_config = get_firebase_config_for_template()
    
    # Pass Firebase configuration to the template
    return render_template('document_analysis.html', **firebase_config)

@app.route('/about')
def about():
    """Render the about page."""
    firebase_config = get_firebase_config_for_template()
    return render_template('about.html', **firebase_config)

@app.route('/templates')
def templates():
    """Render the document templates page."""
    firebase_config = get_firebase_config_for_template()
    return render_template('templates.html', **firebase_config)
    
@app.route('/history')
def history():
    """Render the document history page."""
    firebase_config = get_firebase_config_for_template()
    return render_template('history.html', **firebase_config)

@app.route('/generating')
def generating():
    """Render the document generation page."""
    firebase_config = get_firebase_config_for_template()
    redirect_url = request.args.get('redirect_url', url_for('document_analysis'))
    return render_template('generating.html', redirect_url=redirect_url, **firebase_config)

@app.route('/generate')
def generate():
    """Render the document generation page."""
    firebase_config = get_firebase_config_for_template()
    return render_template('generating.html', **firebase_config)

# API endpoints
@app.route('/api/analyze-document', methods=['POST'])
def analyze_document():
    """API endpoint to analyze uploaded documents."""
    try:
        # Check if a document was included in the request
        if 'document' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No document part in the request'
            }), 400
        
        file = request.files['document']
        analysis_type = request.form.get('analysis_type', 'summary')
        
        # Check if a file was selected
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Check if the file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': f'File type not allowed. Please upload one of: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
            }), 400
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        # Extract text from the document
        document_text = extract_text_from_document(file_path)
        document_length = len(document_text)
        
        # Use Gemini to analyze the document
        analysis_prompt = f"You are a legal document analyzer. Please provide a {analysis_type} of the following document:\n\n{document_text}"
        analysis_result = analyze_text_with_gemini(analysis_prompt, app.config['GEMINI_API_KEY'])
        
        # Generate legal BERT validation
        legal_bert_validation = get_legal_bert_validation(document_text, analysis_type)
        
        # Return the analysis result
        return jsonify({
            'status': 'success',
            'document_name': filename,
            'document_length': document_length,
            'analysis_type': analysis_type,
            'result': analysis_result,
            'legal_bert_validation': legal_bert_validation,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error analyzing document: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing document: {str(e)}'
        }), 500

@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    """API endpoint to analyze text input."""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No text provided for analysis'
            }), 400
        
        legal_text = data['text']
        analysis_type = data.get('analysis_type', 'summary')
        
        # Use Gemini to analyze the text
        analysis_prompt = f"You are a legal document analyzer. Please provide a {analysis_type} of the following legal text:\n\n{legal_text}"
        analysis_result = analyze_text_with_gemini(analysis_prompt, app.config['GEMINI_API_KEY'])
        
        # Generate legal BERT validation
        legal_bert_validation = get_legal_bert_validation(legal_text, analysis_type)
        
        # Return the analysis result
        return jsonify({
            'status': 'success',
            'document_name': 'Text Input',
            'document_length': len(legal_text),
            'analysis_type': analysis_type,
            'result': analysis_result,
            'legal_bert_validation': legal_bert_validation,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error analyzing text: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing text: {str(e)}'
        }), 500
        
@app.route('/api/auth/signin', methods=['POST'])
def auth_signin():
    """Handle Firebase authentication signin."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No user data provided'
            }), 400
        
        # Get user data
        uid = data.get('uid')
        email = data.get('email')
        display_name = data.get('displayName')
        photo_url = data.get('photoURL')
        
        if not uid:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        # Store user info in session
        session['user_id'] = uid
        session['email'] = email
        session['display_name'] = display_name
        session['photo_url'] = photo_url
        session['logged_in'] = True
        session['login_time'] = datetime.datetime.now().isoformat()
        
        app.logger.info(f"User signed in: {email} ({uid})")
        
        # Try to store in Firestore if Firebase is initialized with server-side SDK
        firestore_success = False
        try:
            if 'firebase_config' in sys.modules:
                from firebase_config import get_firestore_db, is_firebase_initialized, is_client_side_only_mode
                
                if is_firebase_initialized() and not is_client_side_only_mode():
                    db = get_firestore_db()
                    if db:
                        # Store user data in Firestore
                        user_data = {
                            'email': email,
                            'displayName': display_name,
                            'photoURL': photo_url,
                            'lastLogin': datetime.datetime.now().isoformat(),
                            'loginCount': 1,  # Will be incremented with arrayUnion
                            'userAgent': request.headers.get('User-Agent', 'Unknown'),
                            'ipAddress': request.remote_addr
                        }
                        
                        # Check if user document already exists
                        user_ref = db.collection('users').document(uid)
                        user_doc = user_ref.get()
                        
                        if user_doc.exists:
                            # Update existing user
                            user_ref.update({
                                'email': email,
                                'displayName': display_name,
                                'photoURL': photo_url,
                                'lastLogin': datetime.datetime.now().isoformat(),
                                'loginCount': user_doc.get('loginCount', 0) + 1,
                                'userAgent': request.headers.get('User-Agent', 'Unknown'),
                                'ipAddress': request.remote_addr,
                                'lastSeen': datetime.datetime.now().isoformat()
                            })
                            app.logger.info(f"Updated existing user in Firestore: {uid}")
                        else:
                            # Create new user
                            user_data['createdAt'] = datetime.datetime.now().isoformat()
                            user_data['lastSeen'] = datetime.datetime.now().isoformat()
                            user_ref.set(user_data)
                            app.logger.info(f"Created new user in Firestore: {uid}")
                            
                            # Also create an empty history collection for the user
                            history_ref = user_ref.collection('history')
                            history_ref.document('info').set({
                                'created': datetime.datetime.now().isoformat(),
                                'count': 0
                            })
                            
                        firestore_success = True
                else:
                    # Using client-side only mode
                    app.logger.info("Using client-side only Firebase auth - user data stored in session")
            else:
                app.logger.warning("Firebase config module not available")
                        
        except Exception as e:
            app.logger.warning(f"Could not store user data in Firestore: {e}")
            
        # Set up local storage for history if Firestore is not available
        if not firestore_success:
            # Store history in session as a fallback
            if 'user_history' not in session:
                session['user_history'] = []
                
        return jsonify({
            'status': 'success',
            'message': 'User signed in successfully',
            'user': {
                'uid': uid,
                'email': email,
                'displayName': display_name
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error during authentication: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error during authentication: {str(e)}'
        }), 500
        
@app.route('/api/auth/signout', methods=['POST'])
def auth_signout():
    """Handle user sign out."""
    try:
        # Get user ID before clearing the session
        user_id = session.get('user_id')
        
        if user_id:
            # Try to update the user's last logout time in Firestore
            try:
                if 'firebase_config' in sys.modules:
                    from firebase_config import get_firestore_db, is_firebase_initialized, is_client_side_only_mode
                    
                    if is_firebase_initialized() and not is_client_side_only_mode():
                        db = get_firestore_db()
                        if db:
                            # Update user document with logout time
                            user_ref = db.collection('users').document(user_id)
                            user_ref.update({
                                'lastLogout': datetime.datetime.now().isoformat(),
                                'lastSeen': datetime.datetime.now().isoformat()
                            })
                            app.logger.info(f"Updated user logout time in Firestore: {user_id}")
            except Exception as e:
                app.logger.warning(f"Could not update user logout time in Firestore: {e}")
        
        # Clear the session
        session.clear()
        
        return jsonify({
            'status': 'success',
            'message': 'User signed out successfully'
        })
    except Exception as e:
        app.logger.error(f"Error during sign out: {str(e)}")
        # Still clear the session even if there was an error
        session.clear()
        return jsonify({
            'status': 'error',
            'message': f'Error during sign out: {str(e)}'
        }), 500

@app.route('/api/generate-document', methods=['POST'])
def generate_document():
    """API endpoint to generate legal documents using Gemini."""
    try:
        data = request.json
        if not data or 'documentType' not in data or 'fields' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required data for document generation'
            }), 400
        
        document_type = data['documentType']
        fields = data['fields']
        
        # Build a prompt for Gemini based on document type and fields
        prompt = f"You are an expert legal document generator specialized in Indian law. Generate a professional {document_type} with the following details:\n\n"
        
        # Add fields to prompt
        for field_name, field_value in fields.items():
            # Convert field name from kebab-case to readable format
            readable_field = field_name.replace('-', ' ').title()
            prompt += f"{readable_field}: {field_value}\n"
        
        # Additional instructions based on document type
        if document_type == 'employment':
            prompt += "\nThis should be a comprehensive employment contract compliant with Indian labor laws. Include sections for compensation, working hours, confidentiality, intellectual property, termination conditions, and dispute resolution."
        elif document_type == 'nda':
            prompt += "\nThis should be a detailed non-disclosure agreement that protects confidential information under Indian law. Include sections defining confidential information, obligations of the receiving party, exclusions, term of agreement, and remedies for breach."
        elif document_type == 'lease':
            prompt += "\nThis should be a comprehensive lease agreement compliant with Indian property laws and Rent Control Acts. Include sections on rent, security deposit, maintenance responsibilities, term of lease, conditions for termination, and dispute resolution."
        elif document_type == 'service':
            prompt += "\nThis should be a detailed service agreement compliant with Indian contract law. Include sections on scope of services, payment terms, intellectual property rights, confidentiality, term and termination, warranties, and limitations of liability."
        elif document_type == 'shareholders':
            prompt += "\nThis should be a comprehensive shareholders agreement compliant with the Indian Companies Act, 2013. Include sections on share ownership, transfer restrictions, management structure, dividend policy, reserved matters, dispute resolution, and exit provisions."
        else:  # custom
            prompt += "\nThis should be a professional legal document that addresses the specified requirements while ensuring compliance with relevant Indian laws and regulations."
        
        # Add general instructions
        prompt += "\n\nFormat the document professionally with clear sections, numbering, and legal language. Ensure all provisions are legally sound and compliant with current Indian legislation."
        
        # Use Gemini to generate the document
        document_content = analyze_text_with_gemini(prompt, app.config['GEMINI_API_KEY'])
        
        # Return the generated document
        return jsonify({
            'status': 'success',
            'document_type': document_type,
            'document': document_content,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error generating document: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating document: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
