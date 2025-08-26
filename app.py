from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import hashlib
import uuid
import altair as alt
from functools import wraps
import pickle
from datetime import datetime
import hashlib

# Configure Altair to use inline data for web serving
alt.data_transformers.disable_max_rows()
alt.data_transformers.enable('default')

class ServerSideSession:
    """Server-side session storage to bypass cookie size limits"""
    
    def __init__(self, base_dir='server_sessions'):
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    
    def get_session_file_path(self, session_id):
        """Get the file path for a session ID"""
        # Use first 2 chars of session_id for subdirectory to avoid too many files in one dir
        subdir = os.path.join(self.base_dir, session_id[:2])
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        return os.path.join(subdir, f"{session_id}.pkl")
    
    def load_session_data(self, session_id):
        """Load session data from file"""
        if not session_id:
            return {}
        
        file_path = self.get_session_file_path(session_id)
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                # Check if data is expired (optional - 24 hour expiry)
                if 'last_accessed' in data:
                    last_accessed = datetime.fromisoformat(data['last_accessed'])
                    if datetime.now() - last_accessed > timedelta(hours=24):
                        os.remove(file_path)
                        return {}
                return data.get('session_data', {})
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return {}
    
    def save_session_data(self, session_id, data):
        """Save session data to file"""
        if not session_id:
            return False
        
        file_path = self.get_session_file_path(session_id)
        try:
            session_wrapper = {
                'session_data': data,
                'last_accessed': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(session_wrapper, f)
            return True
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id):
        """Delete a session file"""
        if not session_id:
            return False
        
        file_path = self.get_session_file_path(session_id)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

# Initialize server-side session storage
server_session = ServerSideSession()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'hoysportsdata_secret_key_2025'  # For session management

# Configure session to handle larger data sets
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Password protection configuration
SITE_PASSWORDS = ['scots25', 'hunt25', 'cobble25', 'eagleton25']  # Regular user passwords
ADMIN_PASSWORD = 'Jackets21!'

# User account mapping - each password maps to a specific username for cross-device data access
PASSWORD_TO_USERNAME = {
    'scots25': 'scots_user',
    'hunt25': 'hunt_user', 
    'cobble25': 'cobble_user',
    'eagleton25': 'eagleton_user'
}

# Maintenance mode state (stored in memory for simplicity)
maintenance_mode = False

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            return render_template('error.html', 
                                 error_title='Access Denied',
                                 error_message='Admin access required for this feature.',
                                 back_url=url_for('index')), 403
        return f(*args, **kwargs)
    return decorated_function

# Configure Altair to use JSON renderer
alt.data_transformers.enable('json')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for password protection"""
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Check for admin password
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            session['is_admin'] = True
            session['username'] = 'admin'  # Set admin username for data access
            return redirect(url_for('admin_dashboard'))
        
        # Check for regular user passwords
        elif password in SITE_PASSWORDS:
            # Check if maintenance mode is active
            if maintenance_mode:
                return render_template('login.html', 
                    error='Site is currently under maintenance. Please try again later.',
                    maintenance_mode=True)
            session['authenticated'] = True
            session['is_admin'] = False
            # Set username based on password for cross-device data access - NO FALLBACK TO ANONYMOUS
            if password in PASSWORD_TO_USERNAME:
                session['username'] = PASSWORD_TO_USERNAME[password]
            else:
                # This should never happen if SITE_PASSWORDS and PASSWORD_TO_USERNAME are in sync
                return render_template('login.html', error='Authentication error. Please contact administrator.')
            return redirect(url_for('index'))
        
        else:
            return render_template('login.html', error='Invalid password. Please try again.')
    
    # Show maintenance message if maintenance mode is active
    return render_template('login.html', maintenance_mode=maintenance_mode if maintenance_mode else None)

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard with maintenance mode controls"""
    # Check if user is admin
    if not session.get('is_admin', False):
        return redirect(url_for('index'))
    
    return render_template('admin.html', maintenance_mode=maintenance_mode)

@app.route('/toggle_maintenance', methods=['POST'])
@login_required
def toggle_maintenance():
    """Toggle maintenance mode on/off"""
    global maintenance_mode
    
    # Check if user is admin
    if not session.get('is_admin', False):
        return jsonify({'error': 'Admin access required'}), 403
    
    maintenance_mode = not maintenance_mode
    status = 'enabled' if maintenance_mode else 'disabled'
    
    return jsonify({
        'success': True,
        'maintenance_mode': maintenance_mode,
        'message': f'Maintenance mode {status}'
    })

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.pop('authenticated', None)
    session.pop('is_admin', None)
    session.pop('username', None)  # Clear username for proper session cleanup
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Analytics selection dashboard"""
    return render_template('analytics_menu.html')

@app.route('/analytics/offensive-hoy')
@login_required
def offensive_hoy_analysis():
    """Offensive Self Scout Analysis (Hoy's Template) - Current functionality"""
    return render_template('index.html')

@app.route('/analytics/defensive-hoy')
@login_required
def defensive_hoy_analysis():
    """Defensive Self Scout Analysis (Hoy's Template) - Current functionality"""
    return render_template('defensive_index.html')

@app.route('/analytics/offensive-hudl')
@admin_required
def offensive_hudl_analysis():
    """Offensive Self Scout Analysis (Hudl Excel Export) - Dynamic Column Recognition"""
    return render_template('hudl_analysis.html',
                         analysis_type='offensive',
                         title='Offensive Self Scout Analysis (Hudl Excel Export)',
                         description='Upload your Hudl Excel export and we\'ll automatically detect and analyze your offensive stats.')

@app.route('/analytics/defensive-hudl')
@admin_required
def defensive_hudl_analysis():
    """Defensive Self Scout Analysis (Hudl Excel Export) - Dynamic Column Recognition"""
    return render_template('hudl_analysis.html',
                         analysis_type='defensive',
                         title='Defensive Self Scout Analysis (Hudl Excel Export)',
                         description='Upload your Hudl Excel export and we\'ll automatically detect and analyze your defensive stats.')

@app.route('/analytics/player-grades')
@login_required
def player_grades_analysis():
    """Player Grade Analysis (Hoy's Template) - Coming Soon"""
    return render_template('coming_soon.html',
                         title='Player Grade Analysis (Hoy\'s Template)',
                         description='Individual player performance grading and analysis.')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle Excel file upload and return sheet names"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Store file path in session for later use
        session['uploaded_file_path'] = filepath
        
        # Read Excel file and get sheet names
        xls = pd.ExcelFile(filepath)
        sheet_names = xls.sheet_names
        
        return jsonify({
            'success': True,
            'filename': filename,
            'sheets': sheet_names
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/upload_plays', methods=['POST'])
@login_required
def upload_plays():
    """Handle Excel file upload for play analysis (both offensive and defensive)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
    
    try:
        # Get analysis type from form data
        analysis_type = request.form.get('analysis_type', 'offensive')
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Store file path and analysis type in session
        session['uploaded_file_path'] = filepath
        session['analysis_type'] = analysis_type
        
        # Read Excel file and get sheet names
        xls = pd.ExcelFile(filepath)
        sheet_names = xls.sheet_names
        
        return jsonify({
            'success': True,
            'filename': filename,
            'sheets': sheet_names,
            'analysis_type': analysis_type
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_data():
    """Analyze the selected sheets and return data for visualization"""
    data = request.get_json()
    filename = data.get('filename')
    selected_sheets = data.get('sheets', [])
    
    if not filename or not selected_sheets:
        return jsonify({'error': 'Missing filename or sheets'}), 400
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"DEBUG: Loading data from {filepath} with sheets {selected_sheets}")
        combined_df = load_and_process_data(filepath, selected_sheets)
        print(f"DEBUG: Combined dataframe shape: {combined_df.shape}")
        print(f"DEBUG: Combined dataframe columns: {list(combined_df.columns)}")
        
        # Get available columns for comparison
        available_columns = get_available_columns(combined_df)
        print(f"DEBUG: Available columns: {available_columns}")
        
        # Generate summary statistics
        summary_stats = generate_summary_stats(combined_df)
        print(f"DEBUG: Summary stats: {summary_stats}")
        
        # Generate run vs pass chart
        run_pass_chart = generate_run_pass_chart(combined_df)
        print(f"DEBUG: Run pass chart generated: {run_pass_chart is not None}")
        
        # Generate run vs pass trends
        run_pass_chart = generate_run_pass_chart(combined_df)
        
        return jsonify({
            'success': True,
            'summary_stats': summary_stats,
            'available_columns': available_columns,
            'run_pass_chart': run_pass_chart,
            'total_plays': len(combined_df)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error analyzing data: {str(e)}'}), 500

@app.route('/analyze_plays', methods=['POST'])
@login_required
def analyze_plays():
    """Analyze plays for both offensive and defensive analysis using the same logic as offensive analysis"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        selected_sheets = data.get('sheets', [])
        analysis_type = data.get('analysis_type', session.get('analysis_type', 'offensive'))
        
        if not filename or not selected_sheets:
            return jsonify({'error': 'Missing filename or sheets'}), 400
        
        # Get the uploaded file path from session
        filepath = session.get('uploaded_file_path')
        if not filepath:
            return jsonify({'error': 'No file uploaded'}), 400
        
        print(f"DEBUG: Loading data from {filepath} with sheets {selected_sheets}")
        
        # Use the same data processing as offensive analysis
        combined_df = load_and_process_data(filepath, selected_sheets)
        print(f"DEBUG: Combined dataframe shape: {combined_df.shape}")
        print(f"DEBUG: Combined dataframe columns: {list(combined_df.columns)}")
        
        # Get available columns for comparison (same as offensive)
        available_columns = get_available_columns(combined_df)
        print(f"DEBUG: Available columns: {available_columns}")
        
        # Generate summary statistics (same as offensive)
        summary_stats = generate_summary_stats(combined_df)
        print(f"DEBUG: Summary stats: {summary_stats}")
        
        # Generate run vs pass chart (same as offensive)
        run_pass_chart = generate_run_pass_chart(combined_df)
        print(f"DEBUG: Run pass chart generated: {run_pass_chart is not None}")
        
        # Prepare play data for comparison
        play_data = combined_df.fillna('').to_dict('records')
        
        return jsonify({
            'success': True,
            'analysis_type': analysis_type,
            'summary_stats': summary_stats,
            'available_columns': available_columns,
            'run_pass_chart': run_pass_chart,
            'play_data': play_data,
            'total_plays': len(combined_df),
            'sheets_analyzed': len(selected_sheets)
        })
    
    except Exception as e:
        print(f"ERROR in analyze_plays: {str(e)}")
        return jsonify({'error': f'Error analyzing plays: {str(e)}'}), 500

@app.route('/compare', methods=['POST'])
@login_required
def compare_stats():
    """Compare a specific stat across sheets"""
    data = request.get_json()
    filename = data.get('filename')
    selected_sheets = data.get('sheets', [])
    compare_column = data.get('column')
    
    if not all([filename, selected_sheets, compare_column]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Use session-stored file path if available, otherwise fall back to uploads folder
        filepath = session.get('uploaded_file_path')
        if not filepath:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        combined_df = load_and_process_data(filepath, selected_sheets)
        
        # Generate comparison chart
        comparison_chart = generate_comparison_chart(combined_df, compare_column)
        
        return jsonify({
            'success': True,
            'chart': comparison_chart
        })
    
    except Exception as e:
        return jsonify({'error': f'Error comparing stats: {str(e)}'}), 500

@app.route('/preview', methods=['POST'])
@login_required
def preview_data():
    """Get preview of uploaded data for display in table"""
    data = request.get_json()
    filename = data.get('filename')
    selected_sheets = data.get('sheets', [])
    
    if not filename or not selected_sheets:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Use session-stored file path if available, otherwise fall back to uploads folder
        filepath = session.get('uploaded_file_path')
        if not filepath:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        combined_df = load_and_process_data(filepath, selected_sheets)
        
        # Get all data for preview (like Streamlit)
        preview_df = combined_df.copy()
        
        # Handle NaN values that can't be serialized to JSON
        preview_df = preview_df.fillna('')  # Replace NaN with empty string
        
        # Convert to records format that frontend expects
        preview_data = preview_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'preview_data': preview_data,
            'total_rows': len(combined_df)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error loading preview data: {str(e)}'}), 500

@app.route('/get_plays', methods=['POST'])
@login_required
def get_plays():
    """Get list of all plays for selection in play comparison"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        selected_sheets = data.get('sheets', [])
        
        if not filename or not selected_sheets:
            return jsonify({'error': 'Missing filename or sheets'}), 400
            
        # Use session-stored file path instead of constructing from filename
        filepath = session.get('uploaded_file_path')
        if not filepath:
            return jsonify({'error': 'No file uploaded'}), 400
            
        combined_df = load_and_process_data(filepath, selected_sheets)
        
        # Get unique Front/Coverage values for defensive data, or play identifiers for offensive data
        front_coverage_col = None
        for col in ['Front/Coverage', 'front/coverage', 'FRONT/COVERAGE', 'Coverage', 'Front']:
            if col in combined_df.columns:
                front_coverage_col = col
                break
        
        if front_coverage_col:
            # For defensive data: get unique Front/Coverage values
            unique_fronts = combined_df[front_coverage_col].dropna().unique()
            plays = []
            for front_name in sorted(unique_fronts):
                # Count how many times this front/coverage appears
                count = len(combined_df[combined_df[front_coverage_col] == front_name])
                plays.append({
                    'id': front_name,  # Use the actual front/coverage name as ID
                    'display': f"{front_name} ({count} plays)",
                    'front_name': front_name
                })
        else:
            # For offensive data: use row-based approach
            plays = []
            for idx, row in combined_df.iterrows():
                # Try to find a play identifier column
                play_id = None
                for col in ['Play', 'PlayNumber', 'Play_Number', 'play', 'play_number']:
                    if col in combined_df.columns and pd.notna(row[col]):
                        play_id = str(row[col])
                        break
                
                if not play_id:
                    play_id = f"Row {idx + 1}"
                
                # Create a description for the play
                description_parts = []
                for col in ['Down', 'Distance', 'Formation', 'PlayType', 'Result', 'Yards', 'Hash', 'Field Position']:
                    if col in combined_df.columns and pd.notna(row[col]):
                        description_parts.append(f"{col}: {row[col]}")
                
                description = " | ".join(description_parts) if description_parts else "No description"
                
                plays.append({
                    'id': idx,  # Use DataFrame index as unique identifier
                    'display': f"{play_id} - {description[:100]}{'...' if len(description) > 100 else ''}",
                    'play_id': play_id
                })
        
        return jsonify({
            'success': True,
            'plays': plays
        })
    
    except Exception as e:
        return jsonify({'error': f'Error loading plays: {str(e)}'}), 500

@app.route('/compare_plays', methods=['POST'])
@login_required
def compare_plays():
    try:
        data = request.get_json()
        play_indices = data.get('play_indices', [])
        filename = data.get('filename', '')
        sheets = data.get('sheets', [])
        
        if not play_indices:
            return jsonify({'error': 'No plays selected'}), 400
        
        filepath = session.get('uploaded_file_path')
        if not filepath:
            return jsonify({'error': 'No file uploaded'}), 400
        
        xls = pd.ExcelFile(filepath)
        sheet_names = sheets if sheets else xls.sheet_names
        
        all_plays = []
        
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                df.columns = df.columns.str.strip()
                df['sheet_name'] = sheet_name
                df['sheet_order'] = list(xls.sheet_names).index(sheet_name)
                df['row_index'] = df.index
                all_plays.append(df)
            except Exception as e:
                continue
        
        if not all_plays:
            return jsonify({'error': 'No data found in sheets'}), 404
        
        combined_df = pd.concat(all_plays, ignore_index=True)
        
        # Check if we're dealing with Front/Coverage names or row indices
        front_coverage_col = None
        for col in ['Front/Coverage', 'front/coverage', 'FRONT/COVERAGE', 'Coverage', 'Front']:
            if col in combined_df.columns:
                front_coverage_col = col
                break
        
        if front_coverage_col and all(isinstance(idx, str) for idx in play_indices):
            # Filter by Front/Coverage names
            selected_plays = combined_df[combined_df[front_coverage_col].isin(play_indices)]
        else:
            # Filter by row indices (for offensive data or numeric indices)
            numeric_indices = [int(idx) for idx in play_indices if str(idx).isdigit()]
            selected_plays = combined_df.iloc[numeric_indices] if numeric_indices else combined_df
        
        result_data = selected_plays.fillna('').to_dict('records')
        
        return jsonify({
            'success': True,
            'comparison_data': result_data,
            'total_plays': len(result_data)
        })
    except Exception as e:
        return jsonify({'error': f'Error comparing plays: {str(e)}'}), 500

def load_and_process_data(filepath, selected_sheets):
    """Load and process data from Excel file - converted from Streamlit logic"""
    xls = pd.ExcelFile(filepath)
    
    # Store original sheet order for later use
    sheet_order = {sheet: i for i, sheet in enumerate(selected_sheets)}
    
    # Load and combine sheets
    dfs = []
    for sheet in selected_sheets:
        df = pd.read_excel(filepath, sheet_name=sheet)
        df['SheetName'] = sheet
        df['SheetOrder'] = sheet_order[sheet]  # Add ordering column
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Infer play type from sheet name
    def infer_play_type(sheet_name):
        name = sheet_name.strip().lower()
        if "run" in name:
            return "Run"
        elif "pass" in name:
            return "Pass"
        else:
            return "Unknown"
    
    combined_df["InferredPlayType"] = combined_df["SheetName"].apply(infer_play_type)
    
    # Convert numeric columns
    for col in combined_df.columns:
        if combined_df[col].dtype == object and col not in ["Play", "SheetName"]:
            try:
                converted = pd.to_numeric(combined_df[col], errors='coerce')
                if converted.notna().sum() > 0:
                    combined_df[col] = converted
            except:
                continue
    
    # Normalize column names
    combined_df.columns = combined_df.columns.str.strip().str.lower()
    column_mapping = {
        "situational efficiency": "situational_efficiency",
        "efficiency %": "efficiency_pct",
        "negative plays": "negative_plays",
        "explosive %": "explosive_pct",
        "total explosive plays": "explosive_plays",
        "completion %": "completion_pct",
        "completions": "completions",
        "pressure %": "pressure_pct",
        "pressures": "pressures",
        "calls": "calls"
    }
    
    combined_df.rename(columns={k: v for k, v in column_mapping.items() if k.lower() in combined_df.columns}, inplace=True)
    
    return combined_df

def get_available_columns(combined_df):
    """Get available columns for comparison - converted from Streamlit logic"""
    # Function to format column titles consistently
    def format_column_title(col_name):
        if col_name == "Avg Yards (Calculated)":
            return "Avg Yards (Calculated)"
        if col_name == "Scramble %":
            return "Scramble %"
        
        formatted = col_name.replace('_', ' ').title()
        replacements = {
            'Pct': '%', 'Avg': 'Avg', 'Yds': 'Yards', 'Completions': 'Completions',
            'Calls': 'Calls', 'Total': 'Total', 'Explosive': 'Explosive',
            'Situational': 'Situational', 'Efficiency': 'Efficiency',
            'Negative': 'Negative', 'Pressure': 'Pressure', 'Completion': 'Completion'
        }
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)
        return formatted
    
    percent_column_mappings = {
        "Efficiency %": "situational_efficiency",
        "Negative %": "negative_plays", 
        "Explosive %": "explosive_pct",
        "Completion %": "completion_pct",
        "Pressure %": "pressure_pct"
    }
    
    mapped_columns = list(percent_column_mappings.values())
    exclude_columns = ['negative %', 'efficiency_pct', 'avg. yards', 'avg yards', 'scramble %']
    
    # Find special columns
    yards_columns = [col for col in combined_df.columns 
                    if pd.api.types.is_numeric_dtype(combined_df[col]) and 
                    ('yard' in col.lower() or 'gain' in col.lower()) and 
                    'total' in col.lower()]
    
    scrambles_columns = [col for col in combined_df.columns 
                       if pd.api.types.is_numeric_dtype(combined_df[col]) and 
                       'scramble' in col.lower()]
    
    raw_columns = list(percent_column_mappings.keys()) + [
        col for col in combined_df.columns
        if pd.api.types.is_numeric_dtype(combined_df[col]) and 
        col not in mapped_columns and 
        col.lower() not in [exc.lower() for exc in exclude_columns]
    ]
    
    # Add calculated options
    if yards_columns and "calls" in combined_df.columns:
        raw_columns.append("Avg Yards (Calculated)")
    if scrambles_columns and "calls" in combined_df.columns:
        raw_columns.append("Scramble %")
    
    # Format column names
    formatted_columns = [format_column_title(col) for col in raw_columns]
    
    return list(zip(raw_columns, formatted_columns))

def generate_summary_stats(combined_df):
    """Generate summary statistics"""
    stats = {
        'total_plays': len(combined_df),
        'columns': list(combined_df.columns)
    }
    
    # Add average gain if available
    gain_col = next((col for col in combined_df.columns if "gain" in col), None)
    if gain_col:
        stats['avg_gain'] = round(combined_df[gain_col].mean(), 2)
    
    return stats

def generate_run_pass_chart(combined_df):
    """Generate run vs pass distribution chart"""
    if 'inferredplaytype' not in combined_df.columns:
        return None
    
    call_sums = combined_df.groupby("inferredplaytype")["calls"].sum().reset_index()
    call_sums.columns = ["PlayType", "TotalCalls"]
    
    total_calls = call_sums["TotalCalls"].sum()
    call_sums["Percentage"] = (call_sums["TotalCalls"] / total_calls) * 100
    
    # Convert to dictionary for inline data
    chart_data = call_sums.to_dict('records')
    
    chart = alt.Chart(alt.InlineData(values=chart_data)).mark_bar().encode(
        x=alt.X("PlayType:N", title="Play Type"),
        y=alt.Y("Percentage:Q", title="Percentage of Calls"),
        color=alt.Color("PlayType:N"),
        tooltip=[alt.Tooltip("PlayType:N"), alt.Tooltip("Percentage:Q")]
    ).properties(
        title="Run vs Pass Call Percentage",
        width=400,
        height=300
    )
    
    # Convert to JSON with inline data to avoid 404 errors
    return chart.to_json()

def generate_comparison_chart(combined_df, compare_column):
    """Generate comparison chart for selected column - full Streamlit logic"""
    
    # Find special columns for calculated options
    yards_columns = [col for col in combined_df.columns 
                    if pd.api.types.is_numeric_dtype(combined_df[col]) and 
                    ('yard' in col.lower() or 'gain' in col.lower()) and 
                    'total' in col.lower()]
    
    scrambles_columns = [col for col in combined_df.columns 
                       if pd.api.types.is_numeric_dtype(combined_df[col]) and 
                       'scramble' in col.lower()]
    
    # Create summary dataframe with preserved sheet order
    if "calls" in combined_df.columns:
        combined_df["calls"] = pd.to_numeric(combined_df["calls"], errors='coerce').fillna(0)
        summary_df = combined_df.groupby(["sheetname", "sheetorder"])["calls"].sum().reset_index(name='TotalCalls')
        summary_df = summary_df.sort_values('sheetorder').reset_index(drop=True)
    else:
        summary_df = combined_df.groupby(["sheetname", "sheetorder"]).size().reset_index(name='TotalCalls')
        summary_df = summary_df.sort_values('sheetorder').reset_index(drop=True)
    
    chart_col = None
    
    # Handle calculated options
    if compare_column == "Avg Yards (Calculated)":
        if yards_columns and "calls" in combined_df.columns:
            yards_col = yards_columns[0]
            combined_df[yards_col] = pd.to_numeric(combined_df[yards_col], errors='coerce').fillna(0)
            
            grouped = combined_df.groupby(["sheetname", "sheetorder"]).agg({
                yards_col: 'sum',
                'calls': 'sum'
            }).reset_index()
            
            grouped["Avg Yards (Calculated)"] = grouped[yards_col] / grouped['calls']
            grouped = grouped[['sheetname', 'sheetorder', "Avg Yards (Calculated)"]]
            grouped = grouped.sort_values('sheetorder').reset_index(drop=True)
            
            summary_df = summary_df.merge(grouped, on=["sheetname", "sheetorder"])
            chart_col = "Avg Yards (Calculated)"
    
    elif compare_column == "Scramble %":
        if scrambles_columns and "calls" in combined_df.columns:
            scrambles_col = scrambles_columns[0]
            combined_df[scrambles_col] = pd.to_numeric(combined_df[scrambles_col], errors='coerce').fillna(0)
            
            grouped = combined_df.groupby(["sheetname", "sheetorder"]).agg({
                scrambles_col: 'sum',
                'calls': 'sum'
            }).reset_index()
            
            grouped["Scramble %"] = (grouped[scrambles_col] / grouped['calls']) * 100
            grouped = grouped[['sheetname', 'sheetorder', "Scramble %"]]
            grouped = grouped.sort_values('sheetorder').reset_index(drop=True)
            
            summary_df = summary_df.merge(grouped, on=["sheetname", "sheetorder"])
            chart_col = "Scramble %"
    
    # Handle percentage mappings
    else:
        percent_column_mappings = {
            "Efficiency %": "situational_efficiency",
            "Negative %": "negative_plays", 
            "Explosive %": "explosive_pct",
            "Completion %": "completion_pct",
            "Pressure %": "pressure_pct"
        }
        
        if compare_column in percent_column_mappings:
            raw_col = percent_column_mappings[compare_column]
            
            if raw_col in combined_df.columns:
                combined_df[raw_col] = pd.to_numeric(combined_df[raw_col], errors='coerce').fillna(0)
                
                if compare_column == "Efficiency %" and "calls" in combined_df.columns:
                    grouped = combined_df.groupby(["sheetname", "sheetorder"]).agg({
                        raw_col: 'sum',
                        'calls': 'sum'
                    }).reset_index()
                    grouped[compare_column] = (grouped[raw_col] / grouped['calls']) * 100
                    grouped = grouped[['sheetname', 'sheetorder', compare_column]]
                    grouped = grouped.sort_values('sheetorder').reset_index(drop=True)
                
                elif compare_column == "Negative %" and "calls" in combined_df.columns:
                    grouped = combined_df.groupby(["sheetname", "sheetorder"]).agg({
                        raw_col: 'sum',
                        'calls': 'sum'
                    }).reset_index()
                    grouped[compare_column] = (grouped[raw_col] / grouped['calls']) * 100
                    grouped = grouped[['sheetname', 'sheetorder', compare_column]]
                    grouped = grouped.sort_values('sheetorder').reset_index(drop=True)
                
                elif compare_column == "Explosive %":
                    grouped = combined_df.groupby(["sheetname", "sheetorder"])[raw_col].mean().reset_index(name=compare_column)
                    grouped = grouped.sort_values('sheetorder').reset_index(drop=True)
                
                else:
                    grouped = combined_df.groupby(["sheetname", "sheetorder"])[raw_col].mean().reset_index(name=compare_column)
                    grouped = grouped.sort_values('sheetorder').reset_index(drop=True)
                    max_val = grouped[compare_column].max()
                    if max_val <= 1.0:
                        grouped[compare_column] = grouped[compare_column] * 100
                
                summary_df = summary_df.merge(grouped, on=["sheetname", "sheetorder"])
                chart_col = compare_column
        
        # Handle regular numeric columns
        elif compare_column in combined_df.columns and pd.api.types.is_numeric_dtype(combined_df[compare_column]):
            value_stats = combined_df.groupby(["sheetname", "sheetorder"])[compare_column].sum().reset_index(name=compare_column)
            value_stats = value_stats.sort_values('sheetorder').reset_index(drop=True)
            summary_df = summary_df.merge(value_stats, on=["sheetname", "sheetorder"])
            chart_col = compare_column
    
    if chart_col and chart_col in summary_df.columns:
        # Convert to dictionary for inline data
        chart_data = summary_df.to_dict('records')
        
        # Create ordered list of sheet names for proper x-axis ordering
        sheet_order_list = summary_df.sort_values('sheetorder')['sheetname'].tolist()
        
        chart = alt.Chart(alt.InlineData(values=chart_data)).mark_bar().encode(
            x=alt.X('sheetname:N', title='Sheet', sort=sheet_order_list),
            y=alt.Y(f'{chart_col}:Q', title=chart_col),
            color=alt.Color('sheetname:N', legend=None),
            tooltip=[alt.Tooltip('sheetname:N'), alt.Tooltip(f'{chart_col}:Q')]
        ).properties(
            title=f"Comparison: {chart_col}",
            width=320,
            height=280
        )
        
        return chart.to_json()
    
    # Fallback chart with preserved sheet order
    chart_data_df = combined_df.groupby(["sheetname", "sheetorder"]).size().reset_index(name='count')
    chart_data_df = chart_data_df.sort_values('sheetorder').reset_index(drop=True)
    chart_data = chart_data_df.to_dict('records')
    
    # Create ordered list of sheet names for proper x-axis ordering
    sheet_order_list = chart_data_df.sort_values('sheetorder')['sheetname'].tolist()
    
    chart = alt.Chart(alt.InlineData(values=chart_data)).mark_bar().encode(
        x=alt.X('sheetname:N', title='Sheet', sort=sheet_order_list),
        y=alt.Y('count:Q', title='Count'),
        tooltip=[alt.Tooltip('sheetname:N'), alt.Tooltip('count:Q')]
    ).properties(
        title=f"Data Count by Sheet",
        width=320,
        height=280
    )
    
    return chart.to_json()

# Hudl Excel Dynamic Column Recognition Functions
def categorize_columns(columns, analysis_type='offensive'):
    """Dynamically categorize columns based on their names and analysis type"""
    categories = {
        'identifiers': [],
        'basic_stats': [],
        'percentages': [],
        'totals': [],
        'averages': [],
        'situational': [],
        'advanced': [],
        'unknown': []
    }
    
    # Define patterns for different categories
    identifier_patterns = ['play', 'down', 'distance', 'hash', 'field_position', 'formation', 'personnel', 'concept']
    
    if analysis_type == 'offensive':
        basic_patterns = ['yards', 'gain', 'rush', 'pass', 'completion', 'attempt', 'carry', 'target']
        percentage_patterns = ['completion_%', 'efficiency_%', 'success_%', 'explosive_%', 'negative_%', 'pressure_%']
        total_patterns = ['total_', 'sum_', 'count_', 'calls']
        average_patterns = ['avg_', 'average_', 'mean_']
        situational_patterns = ['red_zone', 'third_down', 'goal_line', 'short_yardage', 'two_minute']
        advanced_patterns = ['epa', 'success_rate', 'explosiveness', 'pff_', 'grade']
    else:  # defensive
        basic_patterns = ['tackle', 'assist', 'miss', 'sack', 'pressure', 'hurry', 'hit', 'interception', 'deflection']
        percentage_patterns = ['tackle_%', 'pressure_%', 'coverage_%', 'miss_%', 'success_%']
        total_patterns = ['total_', 'sum_', 'count_', 'calls']
        average_patterns = ['avg_', 'average_', 'mean_']
        situational_patterns = ['red_zone', 'third_down', 'goal_line', 'short_yardage', 'two_minute']
        advanced_patterns = ['epa', 'success_rate', 'pff_', 'grade', 'coverage_grade']
    
    # Categorize each column
    for col in columns:
        col_lower = col.lower().strip()
        categorized = False
        
        # Check identifier patterns
        if any(pattern in col_lower for pattern in identifier_patterns):
            categories['identifiers'].append(col)
            categorized = True
        
        # Check percentage patterns
        elif any(pattern in col_lower for pattern in percentage_patterns) or col_lower.endswith('%'):
            categories['percentages'].append(col)
            categorized = True
        
        # Check total patterns
        elif any(pattern in col_lower for pattern in total_patterns):
            categories['totals'].append(col)
            categorized = True
        
        # Check average patterns
        elif any(pattern in col_lower for pattern in average_patterns):
            categories['averages'].append(col)
            categorized = True
        
        # Check situational patterns
        elif any(pattern in col_lower for pattern in situational_patterns):
            categories['situational'].append(col)
            categorized = True
        
        # Check advanced patterns
        elif any(pattern in col_lower for pattern in advanced_patterns):
            categories['advanced'].append(col)
            categorized = True
        
        # Check basic patterns
        elif any(pattern in col_lower for pattern in basic_patterns):
            categories['basic_stats'].append(col)
            categorized = True
        
        # If not categorized, add to unknown
        if not categorized:
            categories['unknown'].append(col)
    
    return categories

def suggest_calculations(categorized_columns, analysis_type='offensive'):
    """Suggest possible calculations based on available columns"""
    suggestions = []
    
    totals = categorized_columns.get('totals', [])
    percentages = categorized_columns.get('percentages', [])
    basic_stats = categorized_columns.get('basic_stats', [])
    
    # Find calls/attempts column for percentage calculations
    calls_col = None
    for col in totals + basic_stats:
        if any(word in col.lower() for word in ['calls', 'attempts', 'plays']):
            calls_col = col
            break
    
    if analysis_type == 'offensive':
        # Suggest offensive calculations
        if calls_col:
            for stat_col in basic_stats:
                if 'yards' in stat_col.lower() or 'gain' in stat_col.lower():
                    suggestions.append({
                        'name': f'Average {stat_col.title()}',
                        'description': f'Calculate average {stat_col.lower()} per play',
                        'formula': f'{stat_col} / {calls_col}',
                        'type': 'average'
                    })
            
            # Success rate calculations
            for stat_col in basic_stats:
                if any(word in stat_col.lower() for word in ['completion', 'success', 'explosive']):
                    suggestions.append({
                        'name': f'{stat_col.title()} Rate',
                        'description': f'Calculate {stat_col.lower()} percentage',
                        'formula': f'({stat_col} / {calls_col}) * 100',
                        'type': 'percentage'
                    })
    
    else:  # defensive
        # Suggest defensive calculations
        if calls_col:
            for stat_col in basic_stats:
                if any(word in stat_col.lower() for word in ['tackle', 'sack', 'pressure', 'interception']):
                    suggestions.append({
                        'name': f'{stat_col.title()} Rate',
                        'description': f'Calculate {stat_col.lower()} per play',
                        'formula': f'({stat_col} / {calls_col}) * 100',
                        'type': 'percentage'
                    })
    
    return suggestions

@app.route('/hudl_upload', methods=['POST'])
@admin_required
def hudl_upload():
    """Handle Hudl Excel file upload and analyze columns"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        analysis_type = request.form.get('analysis_type', 'offensive')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Store file path in session
        session['hudl_file_path'] = filepath
        session['hudl_analysis_type'] = analysis_type
        
        # Read Excel file and get sheet names
        xls = pd.ExcelFile(filepath)
        sheet_names = xls.sheet_names
        
        # Analyze first sheet to get column structure
        first_sheet = pd.read_excel(filepath, sheet_name=sheet_names[0])
        columns = first_sheet.columns.tolist()
        
        # Categorize columns
        categorized = categorize_columns(columns, analysis_type)
        
        # Suggest calculations
        suggestions = suggest_calculations(categorized, analysis_type)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'sheet_names': sheet_names,
            'columns': columns,
            'categorized_columns': categorized,
            'suggested_calculations': suggestions,
            'analysis_type': analysis_type
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/hudl_analyze', methods=['POST'])
@admin_required
def hudl_analyze():
    """Analyze Hudl data with selected sheets and calculations"""
    try:
        data = request.get_json()
        selected_sheets = data.get('selected_sheets', [])
        selected_calculations = data.get('selected_calculations', [])
        
        filepath = session.get('hudl_file_path')
        analysis_type = session.get('hudl_analysis_type', 'offensive')
        
        if not filepath:
            return jsonify({'error': 'No file uploaded'}), 400
        
        if not selected_sheets:
            return jsonify({'error': 'Please select at least one sheet'}), 400
        
        # Load and process selected sheets
        combined_data = []
        for sheet_name in selected_sheets:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                df.columns = df.columns.str.strip()
                df['sheet_name'] = sheet_name
                df['sheet_order'] = selected_sheets.index(sheet_name)
                combined_data.append(df)
            except Exception as e:
                continue
        
        if not combined_data:
            return jsonify({'error': 'No valid data found in selected sheets'}), 400
        
        combined_df = pd.concat(combined_data, ignore_index=True)
        
        # Clean the DataFrame to handle NaN values early
        combined_df = combined_df.fillna('')
        
        # Apply selected calculations
        calculated_stats = {}
        for calc in selected_calculations:
            try:
                calc_name = calc['name']
                calc_formula = calc['formula']
                
                # Parse and execute calculation
                if '/' in calc_formula and '*' in calc_formula:
                    # Handle percentage calculations like (stat / calls) * 100
                    parts = calc_formula.replace('(', '').replace(')', '').split('*')
                    if len(parts) == 2:
                        division_part = parts[0].strip()
                        multiplier = float(parts[1].strip())
                        
                        if '/' in division_part:
                            numerator, denominator = division_part.split('/')
                            numerator = numerator.strip()
                            denominator = denominator.strip()
                            
                            if numerator in combined_df.columns and denominator in combined_df.columns:
                                combined_df[numerator] = pd.to_numeric(combined_df[numerator], errors='coerce').fillna(0)
                                combined_df[denominator] = pd.to_numeric(combined_df[denominator], errors='coerce').fillna(0)
                                
                                # Calculate by sheet
                                sheet_stats = combined_df.groupby('sheet_name').agg({
                                    numerator: 'sum',
                                    denominator: 'sum'
                                }).reset_index()
                                
                                sheet_stats[calc_name] = (sheet_stats[numerator] / sheet_stats[denominator]) * multiplier
                                calculated_stats[calc_name] = sheet_stats[['sheet_name', calc_name]].to_dict('records')
                
                elif '/' in calc_formula:
                    # Handle simple division like stat / calls
                    numerator, denominator = calc_formula.split('/')
                    numerator = numerator.strip()
                    denominator = denominator.strip()
                    
                    if numerator in combined_df.columns and denominator in combined_df.columns:
                        combined_df[numerator] = pd.to_numeric(combined_df[numerator], errors='coerce').fillna(0)
                        combined_df[denominator] = pd.to_numeric(combined_df[denominator], errors='coerce').fillna(0)
                        
                        sheet_stats = combined_df.groupby('sheet_name').agg({
                            numerator: 'sum',
                            denominator: 'sum'
                        }).reset_index()
                        
                        sheet_stats[calc_name] = sheet_stats[numerator] / sheet_stats[denominator]
                        calculated_stats[calc_name] = sheet_stats[['sheet_name', calc_name]].to_dict('records')
                        
            except Exception as e:
                continue
        
        # Generate summary statistics
        summary_stats = {
            'total_plays': len(combined_df),
            'sheets_analyzed': len(selected_sheets),
            'columns_available': len(combined_df.columns)
        }
        
        # Generate basic visualizations
        charts = {}
        
        # Sheet distribution chart
        sheet_counts = combined_df['sheet_name'].value_counts().reset_index()
        sheet_counts.columns = ['sheet_name', 'count']
        
        sheet_chart = alt.Chart(alt.InlineData(values=sheet_counts.to_dict('records'))).mark_bar().encode(
            x=alt.X('sheet_name:N', title='Sheet'),
            y=alt.Y('count:Q', title='Number of Plays'),
            color=alt.Color('sheet_name:N', legend=None),
            tooltip=['sheet_name:N', 'count:Q']
        ).properties(
            title='Plays by Sheet',
            width=400,
            height=300
        )
        
        charts['sheet_distribution'] = sheet_chart.to_json()
        
        # Handle NaN values for JSON serialization
        data_preview = combined_df.head(10).fillna('').to_dict('records')
        
        # Clean calculated_stats to handle NaN values
        cleaned_calculated_stats = {}
        for stat_name, stat_data in calculated_stats.items():
            cleaned_data = []
            for record in stat_data:
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = None
                    elif isinstance(value, float) and (value == float('inf') or value == float('-inf')):
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                cleaned_data.append(cleaned_record)
            cleaned_calculated_stats[stat_name] = cleaned_data
        
        # Generate play filtering options
        filter_options = generate_filter_options(combined_df)
        
        return jsonify({
            'success': True,
            'summary_stats': summary_stats,
            'calculated_stats': cleaned_calculated_stats,
            'charts': charts,
            'data_preview': data_preview,
            'filter_options': filter_options
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing data: {str(e)}'}), 500

def generate_filter_options(df):
    """Generate filtering options based on available columns"""
    filter_options = {}
    
    # Common filter column patterns
    filter_patterns = {
        'play_type': ['play type', 'play_type', 'playtype'],
        'formation': ['off form', 'formation', 'off_form', 'offensive_formation'],
        'play_call': ['off play', 'play_call', 'off_play', 'offensive_play'],
        'concept': ['concept', 'play_concept'],
        'down': ['dn', 'down'],
        'distance': ['dist', 'distance', 'yards_to_go'],
        'hash': ['hash', 'field_hash'],
        'result': ['result', 'play_result'],
        'efficiency': ['eff', 'efficiency', 'successful'],
        'yard_line': ['yard ln', 'yard_line', 'field_position'],
        'strength': ['off str', 'strength', 'off_strength'],
        'backfield': ['backfield', 'personnel']
    }
    
    # Find matching columns in the dataframe
    for filter_type, patterns in filter_patterns.items():
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(pattern in col_lower for pattern in patterns):
                # Get unique values for this filter
                unique_values = df[col].dropna().unique().tolist()
                if len(unique_values) > 0 and len(unique_values) <= 50:  # Reasonable filter size
                    filter_options[filter_type] = {
                        'column': col,
                        'display_name': filter_type.replace('_', ' ').title(),
                        'values': sorted([str(v) for v in unique_values if str(v) != 'nan'])
                    }
                break
    
    return filter_options

@app.route('/hudl_filter_plays', methods=['POST'])
@admin_required
def hudl_filter_plays():
    """Filter plays based on selected criteria and return analysis"""
    try:
        data = request.get_json()
        filters = data.get('filters', {})
        group_by = data.get('group_by', None)
        selected_sheets = data.get('selected_sheets', [])
        
        filepath = session.get('hudl_file_path')
        if not filepath:
            return jsonify({'error': 'No file uploaded'}), 400
        
        if not selected_sheets:
            return jsonify({'error': 'No sheets selected'}), 400
        
        # Load and process selected sheets
        combined_data = []
        for sheet_name in selected_sheets:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                df.columns = df.columns.str.strip()
                df['sheet_name'] = sheet_name
                df['sheet_order'] = selected_sheets.index(sheet_name)
                combined_data.append(df)
            except Exception as e:
                continue
        
        if not combined_data:
            return jsonify({'error': 'No valid data found'}), 400
        
        combined_df = pd.concat(combined_data, ignore_index=True)
        combined_df = combined_df.fillna('')
        
        # Apply filters
        filtered_df = combined_df.copy()
        applied_filters = []
        
        # Simple filter mapping based on Sewanee data structure
        filter_column_map = {
            'play_type': 'PLAY TYPE',
            'formation': 'OFF FORM', 
            'play_call': 'OFF PLAY',
            'concept': 'CONCEPT',
            'down': 'DN',
            'distance': 'DIST',
            'hash': 'HASH',
            'result': 'RESULT',
            'efficiency': 'EFF'
        }
        
        for filter_type, filter_value in filters.items():
            if filter_value and filter_value != 'all':
                col_name = filter_column_map.get(filter_type)
                if col_name and col_name in combined_df.columns:
                    filtered_df = filtered_df[filtered_df[col_name].astype(str) == str(filter_value)]
                    applied_filters.append(f"{col_name}: {filter_value}")
        
        # Generate summary for filtered data
        filtered_summary = {
            'total_plays': len(filtered_df),
            'applied_filters': applied_filters,
            'percentage_of_total': round((len(filtered_df) / len(combined_df)) * 100, 1) if len(combined_df) > 0 else 0
        }
        
        # Generate efficiency breakdown if efficiency column exists
        efficiency_breakdown = {}
        if 'EFF' in filtered_df.columns:
            eff_counts = filtered_df['EFF'].value_counts().to_dict()
            total_with_eff = sum(eff_counts.values())
            if total_with_eff > 0:
                efficiency_breakdown = {
                    'efficient_plays': eff_counts.get('Y', 0),
                    'inefficient_plays': eff_counts.get('N', 0),
                    'efficiency_rate': round((eff_counts.get('Y', 0) / total_with_eff) * 100, 1)
                }
        
        # Generate grouped analysis if group_by is specified
        grouped_analysis = {}
        if group_by and group_by in combined_df.columns and len(filtered_df) > 0:
            try:
                group_stats = filtered_df.groupby(group_by).size().reset_index(name='play_count')
                group_stats = group_stats.fillna('')
                grouped_analysis = {
                    'group_by': group_by,
                    'data': group_stats.to_dict('records')
                }
            except Exception as e:
                grouped_analysis = {}
        
        # Simple charts
        charts = {}
        if 'PLAY TYPE' in filtered_df.columns and len(filtered_df) > 0:
            try:
                play_type_counts = filtered_df['PLAY TYPE'].value_counts().reset_index()
                play_type_counts.columns = ['play_type', 'count']
                play_type_counts = play_type_counts.fillna('')
                
                if len(play_type_counts) > 0:
                    chart_data = play_type_counts.to_dict('records')
                    play_type_chart = alt.Chart(alt.InlineData(values=chart_data)).mark_bar().encode(
                        x=alt.X('play_type:N', title='Play Type'),
                        y=alt.Y('count:Q', title='Count'),
                        color=alt.Color('play_type:N', legend=None),
                        tooltip=['play_type:N', 'count:Q']
                    ).properties(
                        title='Filtered Play Type Distribution',
                        width=400,
                        height=300
                    )
                    charts['play_type_distribution'] = play_type_chart.to_json()
            except Exception as e:
                pass
        
        # Clean data preview
        data_preview = filtered_df.head(20).fillna('').to_dict('records')
        
        return jsonify({
            'success': True,
            'filtered_summary': filtered_summary,
            'grouped_analysis': grouped_analysis,
            'efficiency_breakdown': efficiency_breakdown,
            'charts': charts,
            'filtered_data_preview': data_preview
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in hudl_filter_plays: {error_details}")
        return jsonify({'error': f'Error filtering plays: {str(e)}'}), 500

def generate_defensive_analysis(df):
    """Generate defensive-specific analysis and charts"""
    try:
        # Basic summary statistics
        summary = {
            'total_plays': len(df),
            'total_sheets': len(df['sheet_name'].unique()) if 'sheet_name' in df.columns else 1
        }
        
        # Defensive-specific column analysis
        defensive_columns = [
            'Formation', 'FORMATION', 'DEF FORM', 'Defense', 'DEFENSE',
            'Coverage', 'COVERAGE', 'COV', 'Blitz', 'BLITZ', 'RUSH',
            'Personnel', 'PERSONNEL', 'PERS', 'Down', 'DOWN', 'DN',
            'Distance', 'DISTANCE', 'DIST', 'Result', 'RESULT', 'GAIN',
            'Success', 'SUCCESS', 'STOP', 'TFL', 'SACK', 'INT', 'PBU'
        ]
        
        # Find available defensive columns
        available_cols = [col for col in df.columns if any(def_col.lower() in col.lower() for def_col in defensive_columns)]
        
        charts = {}
        
        # Generate formation distribution chart if formation data exists
        formation_cols = [col for col in df.columns if any(term in col.upper() for term in ['FORM', 'FORMATION', 'DEF'])]
        if formation_cols:
            formation_col = formation_cols[0]
            formation_counts = df[formation_col].value_counts().head(10)
            if len(formation_counts) > 0:
                formation_chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": "Defensive Formation Distribution",
                    "data": {"values": [{"formation": str(k), "count": int(v)} for k, v in formation_counts.items()]},
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "formation", "type": "nominal", "title": "Formation"},
                        "y": {"field": "count", "type": "quantitative", "title": "Number of Plays"},
                        "color": {"value": "#1f77b4"}
                    }
                }
                charts['formation_distribution'] = json.dumps(formation_chart)
        
        # Generate down and distance analysis
        down_cols = [col for col in df.columns if col.upper() in ['DOWN', 'DN']]
        dist_cols = [col for col in df.columns if col.upper() in ['DISTANCE', 'DIST']]
        
        if down_cols and dist_cols:
            down_col, dist_col = down_cols[0], dist_cols[0]
            down_dist_data = df.groupby([down_col, dist_col]).size().reset_index(name='count')
            down_dist_data = down_dist_data.head(20)  # Limit for readability
            
            if len(down_dist_data) > 0:
                down_dist_chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": "Down and Distance Analysis",
                    "data": {"values": down_dist_data.to_dict('records')},
                    "mark": "circle",
                    "encoding": {
                        "x": {"field": down_col, "type": "ordinal", "title": "Down"},
                        "y": {"field": dist_col, "type": "quantitative", "title": "Distance"},
                        "size": {"field": "count", "type": "quantitative", "title": "Play Count"},
                        "color": {"value": "#ff7f0e"}
                    }
                }
                charts['down_distance'] = json.dumps(down_dist_chart)
        
        # Generate success rate analysis if success/result columns exist
        result_cols = [col for col in df.columns if any(term in col.upper() for term in ['RESULT', 'SUCCESS', 'STOP', 'GAIN'])]
        if result_cols:
            result_col = result_cols[0]
            result_counts = df[result_col].value_counts()
            if len(result_counts) > 0:
                result_chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": "Defensive Results",
                    "data": {"values": [{"result": str(k), "count": int(v)} for k, v in result_counts.items()]},
                    "mark": "arc",
                    "encoding": {
                        "theta": {"field": "count", "type": "quantitative"},
                        "color": {"field": "result", "type": "nominal", "title": "Result"}
                    }
                }
                charts['defensive_results'] = json.dumps(result_chart)
        
        return {
            'summary': summary,
            'charts': charts
        }
    
    except Exception as e:
        return {
            'summary': {'total_plays': len(df), 'error': str(e)},
            'charts': {}
        }

def generate_offensive_analysis(df):
    """Generate offensive-specific analysis and charts"""
    try:
        # Basic summary statistics
        summary = {
            'total_plays': len(df),
            'total_sheets': len(df['sheet_name'].unique()) if 'sheet_name' in df.columns else 1
        }
        
        # Offensive-specific column analysis
        offensive_columns = [
            'Formation', 'FORMATION', 'OFF FORM', 'Offense', 'OFFENSE',
            'Play Type', 'PLAY TYPE', 'PLAY_TYPE', 'Run', 'RUN', 'Pass', 'PASS',
            'Personnel', 'PERSONNEL', 'PERS', 'Down', 'DOWN', 'DN',
            'Distance', 'DISTANCE', 'DIST', 'Result', 'RESULT', 'GAIN',
            'Yards', 'YARDS', 'YDS', 'Success', 'SUCCESS', 'EFF', 'EFFICIENCY'
        ]
        
        # Find available offensive columns
        available_cols = [col for col in df.columns if any(off_col.lower() in col.lower() for off_col in offensive_columns)]
        
        charts = {}
        
        # Generate play type distribution chart
        play_type_cols = [col for col in df.columns if any(term in col.upper() for term in ['PLAY TYPE', 'PLAY_TYPE', 'RUN', 'PASS'])]
        if play_type_cols:
            play_type_col = play_type_cols[0]
            play_type_counts = df[play_type_col].value_counts()
            if len(play_type_counts) > 0:
                play_type_chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": "Play Type Distribution",
                    "data": {"values": [{"play_type": str(k), "count": int(v)} for k, v in play_type_counts.items()]},
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "play_type", "type": "nominal", "title": "Play Type"},
                        "y": {"field": "count", "type": "quantitative", "title": "Number of Plays"},
                        "color": {"field": "play_type", "type": "nominal"}
                    }
                }
                charts['play_type_distribution'] = json.dumps(play_type_chart)
        
        # Generate formation analysis
        formation_cols = [col for col in df.columns if any(term in col.upper() for term in ['FORM', 'FORMATION', 'OFF'])]
        if formation_cols:
            formation_col = formation_cols[0]
            formation_counts = df[formation_col].value_counts().head(10)
            if len(formation_counts) > 0:
                formation_chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": "Offensive Formation Usage",
                    "data": {"values": [{"formation": str(k), "count": int(v)} for k, v in formation_counts.items()]},
                    "mark": "arc",
                    "encoding": {
                        "theta": {"field": "count", "type": "quantitative"},
                        "color": {"field": "formation", "type": "nominal", "title": "Formation"}
                    }
                }
                charts['formation_usage'] = json.dumps(formation_chart)
        
        # Generate efficiency analysis if available
        eff_cols = [col for col in df.columns if any(term in col.upper() for term in ['EFF', 'EFFICIENCY', 'SUCCESS'])]
        if eff_cols:
            eff_col = eff_cols[0]
            eff_counts = df[eff_col].value_counts()
            if len(eff_counts) > 0:
                eff_chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": "Play Efficiency",
                    "data": {"values": [{"efficiency": str(k), "count": int(v)} for k, v in eff_counts.items()]},
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "efficiency", "type": "nominal", "title": "Efficiency"},
                        "y": {"field": "count", "type": "quantitative", "title": "Number of Plays"},
                        "color": {"value": "#2ca02c"}
                    }
                }
                charts['efficiency_analysis'] = json.dumps(eff_chart)
        
        return {
            'summary': summary,
            'charts': charts
        }
    
    except Exception as e:
        return {
            'summary': {'total_plays': len(df), 'error': str(e)},
            'charts': {}
        }

# =====================================
# IN-GAME BOX STATS ANALYTICS ROUTES
# =====================================

@app.route('/analytics/box-stats')
@login_required
def box_stats_analytics():
    """In-Game Box Stats Analytics main page"""
    return render_template('box_stats.html')

@app.route('/box_stats/add_play', methods=['POST'])
@login_required
def add_box_stats_play():
    """Add a single play's box stats"""
    try:
        data = request.get_json()
        
        # Get or create server-side session ID
        if 'server_session_id' not in session:
            session['server_session_id'] = str(uuid.uuid4())
            session.permanent = True
        
        session_id = session['server_session_id']
        
        # Load box stats from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        
        # Initialize box stats if not exists
        if 'box_stats' not in box_stats_data:
            box_stats_data['box_stats'] = {
                'plays': [],
                'players': {},
                'game_info': {},
                'team_stats': {
                    'total_plays': 0,
                    'efficient_plays': 0,
                    'explosive_plays': 0,
                    'total_yards': 0,
                    'efficiency_rate': 0.0,
                    'explosive_rate': 0.0,
                    'avg_yards_per_play': 0.0,
                    'success_rate': 0.0
                }
            }
        
        # Get reference to box_stats for easier access
        box_stats = box_stats_data['box_stats']
        
        # Ensure phase-specific team_stats exists in existing sessions (backward compatibility)
        if 'team_stats' not in box_stats:
            box_stats['team_stats'] = {}
        
        # Initialize phase-specific team stats
        phases = ['offense', 'defense', 'special_teams']
        for phase in phases:
            if phase not in box_stats['team_stats']:
                box_stats['team_stats'][phase] = {
                    'total_plays': 0,
                    'efficient_plays': 0,
                    'explosive_plays': 0,
                    'negative_plays': 0,
                    'total_yards': 0,
                    'touchdowns': 0,
                    'turnovers': 0,
                    'interceptions': 0,
                    'efficiency_rate': 0.0,
                    'explosive_rate': 0.0,
                    'negative_rate': 0.0,
                    'nee_score': 0.0,
                    'avg_yards_per_play': 0.0,
                    'success_rate': 0.0,
                    # Progression tracking
                    'nee_progression': [],
                    'efficiency_progression': [],
                    'avg_yards_progression': []
                }
        
        # Maintain overall team stats for backward compatibility
        if 'overall' not in box_stats['team_stats']:
            box_stats['team_stats']['overall'] = {
                'total_plays': 0,
                'efficient_plays': 0,
                'explosive_plays': 0,
                'negative_plays': 0,
                'total_yards': 0,
                'touchdowns': 0,
                'turnovers': 0,
                'interceptions': 0,
                'efficiency_rate': 0.0,
                'explosive_rate': 0.0,
                'negative_rate': 0.0,
                'nee_score': 0.0,
                'avg_yards_per_play': 0.0,
                'success_rate': 0.0,
                # Progression tracking
                'nee_progression': [],
                'efficiency_progression': [],
                'avg_yards_progression': []
            }
        
        # Ensure all advanced analytics fields exist in all phase-specific team_stats (backward compatibility)
        required_team_fields = {
            'negative_plays': 0,
            'efficiency_rate': 0.0,
            'explosive_rate': 0.0,
            'negative_rate': 0.0,
            'nee_score': 0.0,
            'avg_yards_per_play': 0.0,
            'success_rate': 0.0,
            'nee_progression': [],
            'efficiency_progression': [],
            'avg_yards_progression': []
        }
        
        # Apply backward compatibility to all phases (including overall)
        all_phases = ['offense', 'defense', 'special_teams', 'overall']
        for phase in all_phases:
            if phase in box_stats['team_stats']:
                for field, default_value in required_team_fields.items():
                    if field not in box_stats['team_stats'][phase]:
                        box_stats['team_stats'][phase][field] = default_value
        
        # Ensure play_call_stats exists in existing sessions (backward compatibility)
        if 'play_call_stats' not in box_stats:
            box_stats['play_call_stats'] = {}
        
        # Extract play data
        play_data = {
            'play_number': data.get('play_number'),
            'down': data.get('down'),
            'distance': data.get('distance'),
            'field_position': data.get('field_position'),
            'play_type': data.get('play_type'),
            'play_call': data.get('play_call'),  # Optional play call field
            'result': data.get('result'),
            'yards_gained': data.get('yards_gained', 0),
            'players_involved': data.get('players_involved', []),
            'timestamp': data.get('timestamp')
        }
        
        # DEBUG: Log the incoming data to diagnose player selection issue
        print(f"DEBUG PLAY SUBMISSION: Received data: {data}")
        print(f"DEBUG PLAY SUBMISSION: Players involved count: {len(play_data['players_involved'])}")
        print(f"DEBUG PLAY SUBMISSION: Players involved data: {play_data['players_involved']}")
        
        # Add penalty-specific data if this is a penalty
        if data.get('play_type') == 'penalty':
            play_data.update({
                'penalty_type': data.get('penalty_type'),
                'penalty_yards': data.get('penalty_yards', 0),
                'penalty_on': data.get('penalty_on', 'offense')
            })
        
        # Add play to server-side storage with size monitoring
        box_stats['plays'].append(play_data)
        
        # Save to server-side storage
        server_session.save_session_data(session_id, box_stats_data)
        
        # Monitor session size and warn if getting large
        play_count = len(box_stats['plays'])
        print(f"DEBUG: Added play #{play_count}. Total plays in session: {play_count}")
        if play_count % 10 == 0:  # Check every 10 plays for debugging
            print(f"INFO: Session now contains {play_count} plays")
            if play_count > 200:
                print(f"WARNING: Large session detected with {play_count} plays - consider implementing data archiving")
        
        # Calculate next play situation based on play type
        if data.get('play_type') == 'penalty':
            next_situation = calculate_penalty_situation(play_data, box_stats['plays'])
        else:
            next_situation = calculate_next_situation(play_data, box_stats['plays'])
        box_stats['next_situation'] = next_situation
        
        # Update team-level analytics (skip penalties - they don't count as offensive plays)
        if data.get('play_type') != 'penalty':
            yards_gained = int(play_data.get('yards_gained', 0))
            
            # Determine the phase for this play
            current_phase = data.get('phase', 'offense').lower()
            if current_phase not in ['offense', 'defense', 'special_teams']:
                current_phase = 'offense'  # Default to offense if phase not specified
            
            # Get phase-specific team stats
            phase_team_stats = box_stats['team_stats'][current_phase]
            overall_team_stats = box_stats['team_stats']['overall']
            
            # Update basic team stats for both phase-specific and overall
            phase_team_stats['total_plays'] += 1
            phase_team_stats['total_yards'] += yards_gained
            overall_team_stats['total_plays'] += 1
            overall_team_stats['total_yards'] += yards_gained
            
            # Calculate team efficiency and explosiveness for this play
            # For team calculation, pass None as player_data to check all players for turnovers
            is_team_efficient = calculate_play_efficiency(play_data, yards_gained, None)
                
            if is_team_efficient:
                phase_team_stats['efficient_plays'] += 1
                overall_team_stats['efficient_plays'] += 1
                
            # For team explosive rate, check if any player had an explosive play
            # BUT if ANY player on the play has a turnover, the team play is not explosive
            team_explosive_this_play = False
            team_negative_this_play = False
            
            # First check if ANY player on the play has a turnover
            play_has_turnover = False
            for player in play_data['players_involved']:
                if player.get('fumble', False) or player.get('interception', False):
                    play_has_turnover = True
                    break
            
            for player in play_data['players_involved']:
                role = str(player.get('role', ''))
                
                # For team explosive calculation, don't count as explosive if ANY player on play has turnover
                if not play_has_turnover and calculate_play_explosiveness(role, yards_gained, player):
                    team_explosive_this_play = True
                    
                if calculate_play_negativeness(play_data, yards_gained, player):
                    team_negative_this_play = True
                
                # Update team-level special stats
                if player.get('touchdown', False):
                    phase_team_stats['touchdowns'] += 1
                    overall_team_stats['touchdowns'] += 1
                if player.get('interception', False):
                    phase_team_stats['interceptions'] += 1
                    phase_team_stats['turnovers'] += 1  # Interceptions count as turnovers
                    overall_team_stats['interceptions'] += 1
                    overall_team_stats['turnovers'] += 1
                if player.get('fumble', False):
                    phase_team_stats['turnovers'] += 1  # Fumbles count as turnovers
                    overall_team_stats['turnovers'] += 1
            
            # Debug logging for this play's calculations
            print(f"DEBUG PLAY: Down {play_data.get('down')}, Distance {play_data.get('distance')}, Yards {yards_gained}")
            print(f"DEBUG PLAY: Efficient: {is_team_efficient}, Explosive: {team_explosive_this_play}, Negative: {team_negative_this_play}")
            player_roles = [f"{p.get('role', 'unknown')}-#{p.get('number', 'N/A')}" for p in play_data['players_involved']]
            print(f"DEBUG PLAY: Players involved: {player_roles}")
            
            if team_explosive_this_play:
                phase_team_stats['explosive_plays'] += 1
                overall_team_stats['explosive_plays'] += 1
                
            if team_negative_this_play:
                phase_team_stats['negative_plays'] += 1
                overall_team_stats['negative_plays'] += 1
        else:
            # For penalties, get the current phase for consistency
            current_phase = data.get('phase', 'offense').lower()
            if current_phase not in ['offense', 'defense', 'special_teams']:
                current_phase = 'offense'
            phase_team_stats = box_stats['team_stats'][current_phase]
            overall_team_stats = box_stats['team_stats']['overall']
        
        # Update team rates for both phase-specific and overall stats
        def update_team_rates(stats):
            stats['efficiency_rate'] = round((stats['efficient_plays'] / stats['total_plays']) * 100, 1) if stats['total_plays'] > 0 else 0.0
            stats['explosive_rate'] = round((stats['explosive_plays'] / stats['total_plays']) * 100, 1) if stats['total_plays'] > 0 else 0.0
            stats['negative_rate'] = round((stats['negative_plays'] / stats['total_plays']) * 100, 1) if stats['total_plays'] > 0 else 0.0
            stats['avg_yards_per_play'] = round(stats['total_yards'] / stats['total_plays'], 1) if stats['total_plays'] > 0 else 0.0
            # Calculate NEE (Net Explosive Efficiency): Efficiency Rate + Explosive Rate - Negative Rate
            stats['nee_score'] = round(stats['efficiency_rate'] + stats['explosive_rate'] - stats['negative_rate'], 1)
        
        update_team_rates(phase_team_stats)
        update_team_rates(overall_team_stats)
        
        # Debug logging for team advanced analytics
        print(f"DEBUG TEAM ANALYTICS ({current_phase}): Total plays: {phase_team_stats['total_plays']}, Efficient plays: {phase_team_stats['efficient_plays']}, Explosive plays: {phase_team_stats['explosive_plays']}, Negative plays: {phase_team_stats['negative_plays']}")
        print(f"DEBUG TEAM ANALYTICS ({current_phase}): Efficiency rate: {phase_team_stats['efficiency_rate']}%, Explosive rate: {phase_team_stats['explosive_rate']}%, Negative rate: {phase_team_stats['negative_rate']}%, NEE: {phase_team_stats['nee_score']}")
        print(f"DEBUG TEAM ANALYTICS (OVERALL): Total plays: {overall_team_stats['total_plays']}, Efficient plays: {overall_team_stats['efficient_plays']}, Explosive plays: {overall_team_stats['explosive_plays']}, Negative plays: {overall_team_stats['negative_plays']}")
        
        # Record team progression data (play number and various metrics) for both phase-specific and overall
        current_play_number = len(box_stats['plays']) + 1
        
        def update_progression(stats):
            # NEE progression
            if 'nee_progression' not in stats:
                stats['nee_progression'] = []
            stats['nee_progression'].append({
                'play': current_play_number,
                'nee': stats['nee_score']
            })
            
            # Efficiency progression
            if 'efficiency_progression' not in stats:
                stats['efficiency_progression'] = []
            stats['efficiency_progression'].append({
                'play': current_play_number,
                'efficiency': stats['efficiency_rate']
            })
            
            # Explosive progression
            if 'explosive_progression' not in stats:
                stats['explosive_progression'] = []
            stats['explosive_progression'].append({
                'play': current_play_number,
                'explosive_rate': stats['explosive_rate']
            })
            
            # Average yards progression
            if 'avg_yards_progression' not in stats:
                stats['avg_yards_progression'] = []
            stats['avg_yards_progression'].append({
                'play': current_play_number,
                'avg_yards': stats['avg_yards_per_play']
            })
        
        update_progression(phase_team_stats)
        update_progression(overall_team_stats)
        
        # Debug: Check progression data was added
        print(f"DEBUG PROGRESSION: Phase {current_phase} NEE progression length: {len(phase_team_stats.get('nee_progression', []))}")
        print(f"DEBUG PROGRESSION: Overall NEE progression length: {len(overall_team_stats.get('nee_progression', []))}")
        print(f"DEBUG PROGRESSION: Overall explosive progression length: {len(overall_team_stats.get('explosive_progression', []))}")
        if overall_team_stats.get('nee_progression'):
            print(f"DEBUG PROGRESSION: Latest overall NEE entry: {overall_team_stats['nee_progression'][-1]}")
        if overall_team_stats.get('explosive_progression'):
            print(f"DEBUG PROGRESSION: Latest overall explosive entry: {overall_team_stats['explosive_progression'][-1]}")
        
        # Update play call analytics if play call is provided
        play_call = play_data.get('play_call')
        if play_call and play_call.strip():
            print(f"DEBUG: Processing play call '{play_call}' for analytics")
            update_play_call_analytics(box_stats, play_call, play_data, yards_gained, is_team_efficient, team_explosive_this_play, team_negative_this_play)
        else:
            print(f"DEBUG: No play call provided or empty play call: '{play_call}'")
        
        # Success rate: percentage of plays that are either efficient OR explosive
        # We need to track this properly by checking each play individually
        # For now, use a simplified calculation: (efficient + explosive) / total, capped at 100%
        success_percentage = min(100.0, phase_team_stats['efficiency_rate'] + phase_team_stats['explosive_rate'])
        phase_team_stats['success_rate'] = round(success_percentage, 1)
        
        # Also update overall team stats success rate
        overall_success_percentage = min(100.0, overall_team_stats['efficiency_rate'] + overall_team_stats['explosive_rate'])
        overall_team_stats['success_rate'] = round(overall_success_percentage, 1)
        
        # Mark session as modified
        session.modified = True
        
        # Update player stats (skip penalties - they don't affect individual player stats)
        if data.get('play_type') != 'penalty':
            # Smart passing automation: detect if this is a passing play
            play_type = data.get('play_type', '').lower()
            is_passing_play = play_type == 'pass'
            yards_gained = int(play_data.get('yards_gained', 0))
            
            # For passing plays, determine if it's a completion or incompletion
            is_completion = False
            if is_passing_play:
                # Check if any player has completion marked, or if there are positive yards with a receiver
                for player in play_data['players_involved']:
                    if player.get('completion', False):
                        is_completion = True
                        break
                    # If there's a receiver with positive yards, it's likely a completion
                    if player.get('role') == 'receiver' and yards_gained > 0:
                        is_completion = True
                        break
                
                # If zero yards and no completion checkbox, it's an incompletion
                if yards_gained == 0 and not is_completion:
                    is_completion = False
            
            # Find QB for passing plays (look for passer role or QB position)
            qb_player = None
            if is_passing_play:
                for player in play_data['players_involved']:
                    if player.get('role') == 'passer':
                        qb_player = player
                        break
                    elif player.get('position', '').upper() == 'QB':
                        qb_player = player
                        break
            
            print(f"DEBUG: Players involved in play: {play_data['players_involved']}")
            print(f"DEBUG: Number of players involved: {len(play_data['players_involved'])}")
            
            for player in play_data['players_involved']:
                player_num = player.get('number')
                print(f"DEBUG: Processing player - raw data: {player}")
                if player_num:
                    # Ensure player_num is a string for consistent session storage
                    player_key = str(player_num)
                    print(f"DEBUG: Player key: {player_key}, Player number: {player_num}")
                    if player_key not in box_stats['players']:
                        box_stats['players'][player_key] = {
                            'number': int(player_num),  # Store as int for display
                            'name': str(player.get('name', f'Player #{player_num}')),
                            'position': str(player.get('position', '')),
                            # Offensive stats
                            'rushing_attempts': 0,
                            'rushing_yards': 0,
                            'receptions': 0,
                            'receiving_yards': 0,
                            'passing_attempts': 0,
                            'passing_completions': 0,
                            'passing_yards': 0,
                            'touchdowns': 0,
                            'fumbles': 0,
                            'interceptions': 0,
                            # Defensive stats
                            'tackles_solo': 0,
                            'defensive_td': 0,
                            'return_yards': 0,
                            'tackles_total': 0,
                            'sacks': 0,
                            'qb_hits': 0,
                            'interceptions_def': 0,
                            'pass_breakups': 0,
                            'fumble_recoveries': 0,
                            'forced_fumbles': 0,
                            'defensive_tds': 0,
                            'tackles_for_loss': 0,
                            # Special teams stats
                            'field_goals_made': 0,
                            'field_goals_attempted': 0,
                            'extra_points_made': 0,
                            'extra_points_attempted': 0,
                            'punts': 0,
                            'punt_yards': 0,
                            'kickoff_returns': 0,
                            'kickoff_return_yards': 0,
                            'punt_returns': 0,
                            'punt_return_yards': 0,
                            'blocked_kicks': 0,
                            'coverage_tackles': 0,
                            # Advanced analytics
                            'total_plays': 0,
                            'efficient_plays': 0,
                            'explosive_plays': 0,
                            'negative_plays': 0,
                            'efficiency_rate': 0.0,
                            'explosive_rate': 0.0,
                            'negative_rate': 0.0,
                            'nee_score': 0.0,
                            # Progression tracking
                            'nee_progression': [],
                            'efficiency_progression': [],
                            'avg_yards_progression': []
                        }
                    
                    # Update stats based on player's role in the play
                    player_stats = box_stats['players'][player_key]
                    
                    # Ensure all advanced analytics fields exist in existing player stats (backward compatibility)
                    required_player_fields = {
                        'negative_plays': 0,
                        'efficiency_rate': 0.0,
                        'explosive_rate': 0.0,
                        'negative_rate': 0.0,
                        'nee_score': 0.0,
                        'nee_progression': [],
                        'efficiency_progression': [],
                        'avg_yards_progression': []
                    }
                    
                    for field, default_value in required_player_fields.items():
                        if field not in player_stats:
                            player_stats[field] = default_value
                    
                    role = str(player.get('role', ''))
                    
                    # Update basic stats based on role
                    if role == 'rusher':
                        player_stats['rushing_attempts'] += 1
                        player_stats['rushing_yards'] += yards_gained
                    elif role == 'receiver':
                        player_stats['receptions'] += 1
                        player_stats['receiving_yards'] += yards_gained
                    elif role == 'passer':
                        player_stats['passing_attempts'] += 1
                        if player.get('completion', False) or is_completion:
                            player_stats['passing_completions'] += 1
                            player_stats['passing_yards'] += yards_gained
                    
                    # Defensive stats
                    elif role == 'tackler':
                        player_stats['tackles_solo'] += 1
                        player_stats['tackles_total'] += 1
                        if yards_gained < 0:
                            player_stats['tackles_for_loss'] += 1
                    elif role == 'assist':
                        player_stats['tackles_assisted'] += 1
                        player_stats['tackles_total'] += 1
                    elif role == 'sacker':
                        player_stats['sacks'] += 1
                        player_stats['tackles_solo'] += 1
                        player_stats['tackles_total'] += 1
                        player_stats['tackles_for_loss'] += 1
                    elif role == 'interceptor':
                        player_stats['interceptions_def'] += 1
                        if player.get('touchdown', False):
                            player_stats['defensive_tds'] += 1
                    elif role == 'fumble_forcer':
                        player_stats['forced_fumbles'] += 1
                    elif role == 'fumble_recoverer':
                        player_stats['fumble_recoveries'] += 1
                        if player.get('touchdown', False):
                            player_stats['defensive_tds'] += 1
                    elif role == 'pass_breakup':
                        player_stats['pass_breakups'] += 1
                    
                    # Special teams stats
                    elif role == 'kicker':
                        play_type = play_data.get('play_type', '')
                        result = play_data.get('result', '')
                        if play_type == 'field_goal':
                            player_stats['field_goals_attempted'] += 1
                            if result == 'good':
                                player_stats['field_goals_made'] += 1
                        elif play_type == 'extra_point':
                            player_stats['extra_points_attempted'] += 1
                            if result == 'good':
                                player_stats['extra_points_made'] += 1
                    elif role == 'punter':
                        player_stats['punts'] += 1
                        player_stats['punt_yards'] += abs(yards_gained)
                    elif role == 'returner':
                        play_type = play_data.get('play_type', '')
                        if play_type == 'kickoff_return':
                            player_stats['kickoff_returns'] += 1
                            player_stats['kickoff_return_yards'] += yards_gained
                        elif play_type == 'punt_return':
                            player_stats['punt_returns'] += 1
                            player_stats['punt_return_yards'] += yards_gained
                    elif role == 'coverage' or role == 'coverage_tackler':
                        player_stats['coverage_tackles'] += 1
                        player_stats['tackles_total'] += 1
                    
                    # Smart RB reception automation: If this is a passing play and player is RB, auto-credit reception
                    if is_passing_play and is_completion:
                        player_position = player.get('position', '').upper()
                        if player_position == 'RB' and role != 'receiver':  # RB involved but not marked as receiver
                            player_stats['receptions'] += 1
                            player_stats['receiving_yards'] += yards_gained
                            print(f"DEBUG: Auto-credited RB #{player.get('number')} with reception on pass play")
                    
                    # Update special stats - Offensive
                    if player.get('touchdown', False):
                        player_stats['touchdowns'] += 1
                    if player.get('fumble', False):
                        player_stats['fumbles'] += 1
                    if player.get('interception', False):
                        player_stats['interceptions'] += 1
                    
                    # Update special stats - Defensive (from checkboxes)
                    if player.get('tackle', False):
                        player_stats['tackles_solo'] += 1
                        player_stats['tackles_total'] += 1
                    if player.get('sack', False):
                        player_stats['sacks'] += 1
                        player_stats['tackles_solo'] += 1
                        player_stats['tackles_total'] += 1
                        player_stats['tackles_for_loss'] += 1
                    if player.get('interception_def', False):
                        player_stats['interceptions_def'] += 1
                        player_stats['return_yards'] += player.get('return_yards', 0)
                    if player.get('fumble_recovery', False):
                        player_stats['fumble_recoveries'] += 1
                        player_stats['return_yards'] += player.get('return_yards', 0)
                    if player.get('pass_breakup', False):
                        player_stats['pass_breakups'] += 1
                    if player.get('forced_fumble', False):
                        player_stats['forced_fumbles'] += 1
                    if player.get('tackle_for_loss', False):
                        player_stats['tackles_for_loss'] += 1
                        player_stats['tackles_solo'] += 1
                        player_stats['tackles_total'] += 1
                    if player.get('defensive_td', False):
                        player_stats['defensive_tds'] += 1
                        player_stats['touchdowns'] += 1  # Also count in general TDs
                    
                    # Update special stats - Special Teams (from checkboxes)
                    if player.get('field_goal_made', False):
                        player_stats['field_goals_attempted'] += 1
                        player_stats['field_goals_made'] += 1
                    if player.get('extra_point_made', False):
                        player_stats['extra_points_attempted'] += 1
                        player_stats['extra_points_made'] += 1
                    if player.get('punt_return', False):
                        player_stats['punt_returns'] += 1
                        player_stats['punt_return_yards'] += yards_gained
                    if player.get('kickoff_return', False):
                        player_stats['kickoff_returns'] += 1
                        player_stats['kickoff_return_yards'] += yards_gained
                    if player.get('coverage_tackle', False):
                        player_stats['coverage_tackles'] += 1
                        player_stats['tackles_total'] += 1
                    if player.get('blocked_kick', False):
                        player_stats['blocked_kicks'] += 1
                    if player.get('special_teams_td', False):
                        player_stats['touchdowns'] += 1  # Count in general TDs
                    
                    # Update advanced analytics for all players
                    player_stats['total_plays'] += 1
                    
                    # Calculate if play was efficient
                    # For individual player calculation, pass the player data to check only their turnover
                    is_efficient = calculate_play_efficiency(play_data, yards_gained, player)
                    if is_efficient:
                        player_stats['efficient_plays'] += 1
                    
                    # Calculate if play was explosive
                    is_explosive = calculate_play_explosiveness(role, yards_gained, player)
                    if is_explosive:
                        player_stats['explosive_plays'] += 1
                    
                    # Calculate if play was negative
                    is_negative = calculate_play_negativeness(play_data, yards_gained, player)
                    if is_negative:
                        player_stats['negative_plays'] += 1
                    
                    # Update rates
                    player_stats['efficiency_rate'] = round((player_stats['efficient_plays'] / player_stats['total_plays']) * 100, 1) if player_stats['total_plays'] > 0 else 0.0
                    player_stats['explosive_rate'] = round((player_stats['explosive_plays'] / player_stats['total_plays']) * 100, 1) if player_stats['total_plays'] > 0 else 0.0
                    player_stats['negative_rate'] = round((player_stats['negative_plays'] / player_stats['total_plays']) * 100, 1) if player_stats['total_plays'] > 0 else 0.0
                    
                    # Calculate NEE (Net Explosive Efficiency): Efficiency Rate + Explosive Rate - Negative Rate
                    player_stats['nee_score'] = round(player_stats['efficiency_rate'] + player_stats['explosive_rate'] - player_stats['negative_rate'], 1)
                    
                    # Record progression data (play number and various metrics)
                    current_play_number = len(box_stats['plays']) + 1
                    
                    # NEE progression
                    if 'nee_progression' not in player_stats:
                        player_stats['nee_progression'] = []
                    player_stats['nee_progression'].append({
                        'play': current_play_number,
                        'nee': player_stats['nee_score']
                    })
                    
                    # Efficiency progression
                    if 'efficiency_progression' not in player_stats:
                        player_stats['efficiency_progression'] = []
                    player_stats['efficiency_progression'].append({
                        'play': current_play_number,
                        'efficiency': player_stats['efficiency_rate']
                    })
                    
                    # Average yards progression (calculate avg yards per play for this player)
                    player_avg_yards = 0.0
                    if player_stats['total_plays'] > 0:
                        total_yards = (player_stats.get('rushing_yards', 0) + 
                                     player_stats.get('receiving_yards', 0) + 
                                     player_stats.get('passing_yards', 0))
                        player_avg_yards = round(total_yards / player_stats['total_plays'], 1)
                    
                    # Explosive progression
                    if 'explosive_progression' not in player_stats:
                        player_stats['explosive_progression'] = []
                    player_stats['explosive_progression'].append({
                        'play': current_play_number,
                        'explosive_rate': player_stats['explosive_rate']
                    })
                    
                    print(f"DEBUG: Updated advanced analytics for player #{player_key} - Total plays: {player_stats['total_plays']}, Efficiency: {player_stats['efficiency_rate']}%, Explosive: {player_stats['explosive_rate']}%, NEE: {player_stats['nee_score']}")
            
            # Smart QB automation: If this is a passing play and we found a QB, update their passing stats
            if is_passing_play and qb_player and qb_player.get('number'):
                qb_key = str(qb_player.get('number'))
                
                # Ensure QB exists in stats
                if qb_key not in box_stats['players']:
                    box_stats['players'][qb_key] = {
                        'number': int(qb_player.get('number')),
                        'name': str(qb_player.get('name', f'Player #{qb_player.get("number")}')),
                        'position': str(qb_player.get('position', 'QB')),
                        'rushing_attempts': 0,
                        'rushing_yards': 0,
                        'receptions': 0,
                        'receiving_yards': 0,
                        'passing_attempts': 0,
                        'passing_completions': 0,
                        'passing_yards': 0,
                        'touchdowns': 0,
                        'fumbles': 0,
                        'interceptions': 0,
                        'total_plays': 0,
                        'efficient_plays': 0,
                        'explosive_plays': 0,
                        'negative_plays': 0,
                        'efficiency_rate': 0.0,
                        'explosive_rate': 0.0,
                        'negative_rate': 0.0,
                        'nee_score': 0.0
                    }
                
                qb_stats = box_stats['players'][qb_key]
                
                # Only update QB stats if they weren't already updated as a 'passer'
                qb_already_processed = False
                for p in play_data['players_involved']:
                    if str(p.get('number')) == qb_key and p.get('role') == 'passer':
                        qb_already_processed = True
                        break
                
                if not qb_already_processed:
                    qb_stats['passing_attempts'] += 1
                    if is_completion:
                        qb_stats['passing_completions'] += 1
                        qb_stats['passing_yards'] += yards_gained
                    
                    print(f"DEBUG: Auto-updated QB #{qb_key} passing stats - Attempt: +1, Completion: {'+1' if is_completion else '0'}, Yards: {'+' + str(yards_gained) if is_completion else '0'}")
                    
                    # Note: Advanced analytics for QB will be handled in the main player loop if QB is in players_involved
        
        # Save updated data to server-side storage before returning
        server_session.save_session_data(session_id, box_stats_data)
        
        # Debug: Verify progression data was saved
        test_load = server_session.load_session_data(session_id)
        test_overall = test_load.get('box_stats', {}).get('team_stats', {}).get('overall', {})
        print(f"DEBUG POST-SAVE: Overall NEE progression length: {len(test_overall.get('nee_progression', []))}")
        print(f"DEBUG POST-SAVE: Overall explosive progression length: {len(test_overall.get('explosive_progression', []))}")
        
        return jsonify({
            'success': True,
            'play_count': len(box_stats['plays']),
            'message': 'Play added successfully',
            'next_situation': box_stats.get('next_situation', {}),
            'team_stats': box_stats['team_stats']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error adding play: {str(e)}'}), 500

def calculate_play_efficiency(play_data, yards_gained, player_data=None):
    """
    Calculate if a play was efficient based on down and distance
    - 1st Down: ≥4 yards gained = efficient
    - 2nd Down: Yards to go cut in half or more = efficient  
    - 3rd/4th Down: Conversion achieved = efficient
    - NOTE: For individual players, only their own turnover negates efficiency
    - NOTE: For team-level, any turnover on the play negates efficiency
    """
    try:
        # If player_data is provided, check only that player's turnover
        # If player_data is None, this is for team-level calculation - check all players
        if player_data is not None:
            # Individual player calculation - only their own turnover matters
            if player_data.get('fumble', False) or player_data.get('interception', False):
                return False
        else:
            # Team-level calculation - any turnover on the play negates efficiency
            players_involved = play_data.get('players_involved', [])
            for player in players_involved:
                if player.get('fumble', False) or player.get('interception', False):
                    return False
        
        current_down = int(play_data.get('down', 1))
        current_distance = int(play_data.get('distance', 10))
        yards_gained = int(yards_gained)
        
        if current_down == 1:
            # 1st down: efficient if 4+ yards gained
            return yards_gained >= 4
        elif current_down == 2:
            # 2nd down: efficient if yards to go cut in half or more
            return yards_gained >= (current_distance / 2)
        elif current_down in [3, 4]:
            # 3rd/4th down: efficient if converted (gained enough for first down)
            return yards_gained >= current_distance
        else:
            return False
            
    except (ValueError, TypeError):
        return False

def calculate_play_explosiveness(role, yards_gained, player_data=None):
    """
    Calculate if a play was explosive
    - Rushing plays: ≥10 yards = explosive
    - Passing plays: ≥15 yards = explosive
    - NOTE: If play ends with a turnover (fumble/interception), it is NOT explosive regardless of yardage
    """
    try:
        # First check if this player had a turnover - if so, not explosive
        if player_data and (player_data.get('fumble', False) or player_data.get('interception', False)):
            return False
            
        yards_gained = int(yards_gained)
        
        if role == 'rusher':
            return yards_gained >= 10
        elif role in ['receiver', 'passer']:
            return yards_gained >= 15
        else:
            return False
            
    except (ValueError, TypeError):
        return False

def calculate_play_negativeness(play_data, yards_gained, player):
    """
    Calculate if a play was negative (fumble, interception, or negative yards)
    """
    # Check for turnovers
    if player.get('fumble', False) or player.get('interception', False):
        return True
    
    # Check for negative yards
    if yards_gained < 0:
        return True
    
    return False

def get_saved_games_dir():
    """Get the directory for saved games"""
    saved_games_dir = os.path.join(os.path.dirname(__file__), 'saved_games')
    if not os.path.exists(saved_games_dir):
        os.makedirs(saved_games_dir)
    return saved_games_dir

def get_user_games_dir(username):
    """Get the directory for a specific user's saved games"""
    user_dir = os.path.join(get_saved_games_dir(), hashlib.md5(username.encode()).hexdigest())
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def get_saved_rosters_dir():
    """Get the directory for saved rosters"""
    saved_rosters_dir = os.path.join(os.path.dirname(__file__), 'saved_rosters')
    if not os.path.exists(saved_rosters_dir):
        os.makedirs(saved_rosters_dir)
    return saved_rosters_dir

def get_user_rosters_dir(username):
    """Get the rosters directory for a specific user"""
    user_hash = hashlib.md5(username.encode()).hexdigest()
    user_dir = os.path.join('user_data', f'rosters_{user_hash}')
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def create_safe_roster_filename(roster_name):
    """Create a safe filename from roster name with consistent logic"""
    safe_filename = "".join(c for c in roster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_filename = safe_filename.replace(' ', '_')
    if not safe_filename:
        safe_filename = f"roster_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return f"{safe_filename}.json"

def save_roster_data(username, roster_name, roster_data):
    """Save roster data to file for a specific user"""
    try:
        # Security check: prevent saving to anonymous or invalid usernames
        if not username or username == 'anonymous' or len(username.strip()) == 0:
            print(f"WARNING: Blocked roster save for invalid username: '{username}'")
            return False, "Access denied"
        
        user_dir = get_user_rosters_dir(username)
        
        # Additional security: verify the directory belongs to this user
        expected_hash = hashlib.md5(username.encode()).hexdigest()
        if expected_hash not in user_dir:
            print(f"WARNING: Directory hash mismatch during save for user {username}")
            return False, "Access denied"
        
        # Create safe filename using consistent helper function
        filename = create_safe_roster_filename(roster_name)
        filepath = os.path.join(user_dir, filename)
        
        # Add metadata to roster data
        roster_data_with_meta = {
            'roster_name': roster_name,
            'player_count': len(roster_data.get('players', [])),
            'created_at': datetime.now().isoformat(),
            'username': username,  # Track which user created this
            **roster_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(roster_data_with_meta, f, indent=2)
        
        return True, filename
    except Exception as e:
        print(f"Error saving roster data: {e}")
        return False, str(e)

def load_roster_data(username, roster_filename):
    """Load roster data from file for a specific user"""
    try:
        # Security check: prevent access to anonymous or invalid usernames
        if not username or username == 'anonymous' or len(username.strip()) == 0:
            print(f"WARNING: Blocked roster load for invalid username: '{username}'")
            return None, "Access denied"
        
        user_dir = get_user_rosters_dir(username)
        filepath = os.path.join(user_dir, roster_filename)
        
        # Additional security: verify the directory belongs to this user
        expected_hash = hashlib.md5(username.encode()).hexdigest()
        if expected_hash not in user_dir:
            print(f"WARNING: Directory hash mismatch during load for user {username}")
            return None, "Access denied"
        
        if not os.path.exists(filepath):
            return None, f"Roster file not found: {roster_filename}"
        
        with open(filepath, 'r') as f:
            roster_data = json.load(f)
        
        return roster_data, None
    except Exception as e:
        print(f"Error loading roster data: {e}")
        return None, str(e)

def get_user_saved_rosters(username):
    """Get list of saved rosters for a specific user"""
    try:
        # Security check: prevent access to anonymous or invalid usernames
        if not username or username == 'anonymous' or len(username.strip()) == 0:
            print(f"WARNING: Blocked roster access for invalid username: '{username}'")
            return []
        
        user_dir = get_user_rosters_dir(username)
        rosters = []
        
        # Additional security: verify the directory belongs to this user
        expected_hash = hashlib.md5(username.encode()).hexdigest()
        if expected_hash not in user_dir:
            print(f"WARNING: Directory hash mismatch for user {username}")
            return []
        
        for filename in os.listdir(user_dir):
            if filename.endswith('.json'):
                try:
                    roster_data, error = load_roster_data(username, filename)
                    if roster_data and not error:
                        rosters.append({
                            'filename': filename,
                            'name': roster_data.get('roster_name', filename[:-5]),
                            'player_count': roster_data.get('player_count', 0),
                            'created_at': roster_data.get('created_at', ''),
                        })
                except Exception as e:
                    print(f"Error reading roster file {filename}: {e}")
                    continue
        
        # Sort by creation date (newest first)
        rosters.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return rosters
    except Exception as e:
        print(f"Error getting saved rosters: {e}")
        return []

def delete_roster_data(username, roster_filename):
    """Delete a roster file for a specific user"""
    try:
        # Security check: prevent deletion from anonymous or invalid usernames
        if not username or username == 'anonymous' or len(username.strip()) == 0:
            print(f"WARNING: Blocked roster delete for invalid username: '{username}'")
            return False, "Access denied"
        
        user_dir = get_user_rosters_dir(username)
        
        # Additional security: verify the directory belongs to this user
        expected_hash = hashlib.md5(username.encode()).hexdigest()
        if expected_hash not in user_dir:
            print(f"WARNING: Directory hash mismatch during delete for user {username}")
            return False, "Access denied"
        
        filepath = os.path.join(user_dir, roster_filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, f"Roster {roster_filename} deleted successfully"
        else:
            return False, f"Roster file not found: {roster_filename}"
    except Exception as e:
        print(f"Error deleting roster data: {e}")
        return False, str(e)

def save_game_data(username, game_name, game_data):
    """Save game data to file"""
    try:
        user_dir = get_user_games_dir(username)
        # Create safe filename from game name
        safe_game_name = "".join(c for c in game_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_game_name = safe_game_name.replace(' ', '_')
        if not safe_game_name:
            safe_game_name = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filename = f"{safe_game_name}.json"
        filepath = os.path.join(user_dir, filename)
        
        # Add metadata
        save_data = {
            'game_info': game_data.get('game_info', {}),
            'plays': game_data.get('plays', []),
            'players': game_data.get('players', {}),
            'team_stats': game_data.get('team_stats', {}),
            'play_call_stats': game_data.get('play_call_stats', {}),
            'saved_at': datetime.now().isoformat(),
            'username': username
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return True, filepath
    except Exception as e:
        print(f"Error saving game data: {str(e)}")
        return False, str(e)

def load_game_data(username, game_filename):
    """Load game data from file"""
    try:
        user_dir = get_user_games_dir(username)
        filepath = os.path.join(user_dir, game_filename)
        
        if not os.path.exists(filepath):
            return None, "Game file not found"
        
        with open(filepath, 'r') as f:
            game_data = json.load(f)
        
        return game_data, None
    except Exception as e:
        print(f"Error loading game data: {str(e)}")
        return None, str(e)

def get_user_saved_games(username):
    """Get list of saved games for a user"""
    try:
        user_dir = get_user_games_dir(username)
        games = []
        
        for filename in os.listdir(user_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(user_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        game_data = json.load(f)
                    
                    games.append({
                        'filename': filename,
                        'game_name': game_data.get('game_info', {}).get('name', filename.replace('.json', '')),
                        'opponent': game_data.get('game_info', {}).get('opponent', ''),
                        'date': game_data.get('game_info', {}).get('date', ''),
                        'saved_at': game_data.get('saved_at', ''),
                        'total_plays': len(game_data.get('plays', [])),
                        'total_players': len(game_data.get('players', {}))
                    })
                except Exception as e:
                    print(f"Error reading game file {filename}: {str(e)}")
                    continue
        
        # Sort by saved_at descending (most recent first)
        games.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        return games
    except Exception as e:
        print(f"Error getting saved games: {str(e)}")
        return []

def update_play_call_analytics(box_stats, play_call, play_data, yards_gained, is_efficient, is_explosive, is_negative):
    """Update analytics tracking for a specific play call"""
    try:
        # Initialize play call stats if not exists
        if 'play_call_stats' not in box_stats:
            box_stats['play_call_stats'] = {}
        
        play_call_stats = box_stats['play_call_stats']
        
        # Initialize this play call's stats if first time seeing it
        if play_call not in play_call_stats:
            play_call_stats[play_call] = {
                'total_plays': 0,
                'total_yards': 0,
                'efficient_plays': 0,
                'explosive_plays': 0,
                'negative_plays': 0,
                'touchdowns': 0,
                'turnovers': 0,
                'first_downs': 0,
                'avg_yards_per_play': 0.0,
                'efficiency_rate': 0.0,
                'explosive_rate': 0.0,
                'negative_rate': 0.0,
                'nee_score': 0.0,
                'success_rate': 0.0,
                'play_type_breakdown': {},
                'down_breakdown': {1: 0, 2: 0, 3: 0, 4: 0},
                'distance_breakdown': {'short': 0, 'medium': 0, 'long': 0}
            }
        
        stats = play_call_stats[play_call]
        
        # Update basic stats
        stats['total_plays'] += 1
        stats['total_yards'] += yards_gained
        
        # Update advanced analytics
        if is_efficient:
            stats['efficient_plays'] += 1
        if is_explosive:
            stats['explosive_plays'] += 1
        if is_negative:
            stats['negative_plays'] += 1
        
        # Check for touchdowns and turnovers
        for player in play_data.get('players_involved', []):
            if player.get('touchdown', False):
                stats['touchdowns'] += 1
            if player.get('fumble', False) or player.get('interception', False):
                stats['turnovers'] += 1
        
        # Check for first downs (simplified logic)
        result = play_data.get('result', '').lower()
        if 'first_down' in result or 'touchdown' in result:
            stats['first_downs'] += 1
        
        # Update play type breakdown
        play_type = play_data.get('play_type', 'unknown')
        if play_type not in stats['play_type_breakdown']:
            stats['play_type_breakdown'][play_type] = 0
        stats['play_type_breakdown'][play_type] += 1
        
        # Update down breakdown
        down = play_data.get('down', 1)
        if down in stats['down_breakdown']:
            stats['down_breakdown'][down] += 1
        
        # Update distance breakdown
        distance = play_data.get('distance', 10)
        if distance <= 3:
            stats['distance_breakdown']['short'] += 1
        elif distance <= 7:
            stats['distance_breakdown']['medium'] += 1
        else:
            stats['distance_breakdown']['long'] += 1
        
        # Calculate rates
        total_plays = stats['total_plays']
        if total_plays > 0:
            stats['avg_yards_per_play'] = round(stats['total_yards'] / total_plays, 1)
            stats['efficiency_rate'] = round((stats['efficient_plays'] / total_plays) * 100, 1)
            stats['explosive_rate'] = round((stats['explosive_plays'] / total_plays) * 100, 1)
            stats['negative_rate'] = round((stats['negative_plays'] / total_plays) * 100, 1)
            stats['nee_score'] = round(stats['efficiency_rate'] + stats['explosive_rate'] - stats['negative_rate'], 1)
            
            # Success rate: plays that result in first downs, touchdowns, or are efficient/explosive
            successful_plays = stats['first_downs'] + stats['touchdowns'] + max(0, stats['efficient_plays'] - stats['first_downs'] - stats['touchdowns'])
            stats['success_rate'] = round(min(100, (successful_plays / total_plays) * 100), 1)
        
        print(f"DEBUG: Updated play call analytics for '{play_call}' - Total: {stats['total_plays']}, Avg Yards: {stats['avg_yards_per_play']}, Success Rate: {stats['success_rate']}%")
        
    except Exception as e:
        print(f"Error updating play call analytics: {str(e)}")

def calculate_penalty_situation(current_play, all_plays):
    """Calculate next down, distance, and field position for penalty plays"""
    try:
        current_down = int(current_play.get('down', 1))
        current_distance = int(current_play.get('distance', 10))
        current_field_position = current_play.get('field_position', 'OWN 25')
        penalty_yards = int(current_play.get('penalty_yards', 0))
        penalty_on = current_play.get('penalty_on', 'offense')
        
        print(f"DEBUG PENALTY: Input - down: {current_down}, distance: {current_distance}, field_position: {current_field_position}, penalty_yards: {penalty_yards}, penalty_on: {penalty_on}")
        
        # Parse current field position
        field_parts = current_field_position.strip().split()
        if len(field_parts) >= 2:
            side = field_parts[0]
            try:
                yard_line = int(field_parts[1])
            except (ValueError, IndexError):
                yard_line = 25
        else:
            side = "OWN"
            yard_line = 25
        
        # Calculate field position change based on penalty
        if penalty_on == 'offense':
            # Offensive penalty - move ball back (negative yards for offense)
            effective_yards = -penalty_yards
        else:
            # Defensive penalty - move ball forward (positive yards for offense)
            effective_yards = penalty_yards
        
        print(f"DEBUG PENALTY: Effective yards for field position: {effective_yards}")
        
        # Calculate new field position using penalty yards
        if side == "OWN":
            new_yard_line = int(yard_line) + effective_yards
            if new_yard_line >= 50:
                new_side = "OPP"
                new_yard_line = 100 - new_yard_line
                new_yard_line = max(1, new_yard_line)
            elif new_yard_line <= 0:
                # Safety or backed up to own endzone
                new_side = "OWN"
                new_yard_line = max(1, new_yard_line)
            else:
                new_side = "OWN"
        else:  # OPP side
            new_yard_line = int(yard_line) - effective_yards
            if new_yard_line <= 0:
                # Touchdown due to penalty
                return {
                    'down': 1,
                    'distance': 10,
                    'field_position': 'OWN 25',
                    'auto_calculated': True,
                    'reason': 'Penalty resulted in touchdown - Reset for next drive'
                }
            elif new_yard_line > 50:
                new_side = "OWN"
                new_yard_line = 100 - new_yard_line
            else:
                new_side = "OPP"
                new_yard_line = max(1, new_yard_line)
        
        # Ensure final yard line is valid
        final_yard_line = max(1, abs(int(new_yard_line)))
        new_field_position = f"{new_side} {final_yard_line}"
        
        # Penalty down/distance logic
        if penalty_on == 'defense':
            # Defensive penalty - automatic first down
            new_down = 1
            new_distance = 10
            reason = f"Defensive penalty: Automatic first down at {new_field_position}"
        else:
            # Offensive penalty - repeat down with increased distance
            new_down = current_down
            new_distance = current_distance + penalty_yards
            reason = f"Offensive penalty: Repeat {current_down} down with {penalty_yards} yard penalty"
        
        print(f"DEBUG PENALTY: Result - down: {new_down}, distance: {new_distance}, field_position: {new_field_position}")
        
        return {
            'down': new_down,
            'distance': new_distance,
            'field_position': new_field_position,
            'auto_calculated': True,
            'reason': reason
        }
        
    except Exception as e:
        print(f"ERROR in calculate_penalty_situation: {str(e)}")
        return {
            'down': 1,
            'distance': 10,
            'field_position': 'OWN 25',
            'auto_calculated': False,
            'reason': f'Error calculating penalty situation: {str(e)}'
        }

def calculate_next_situation(current_play, all_plays):
    """Calculate next down, distance, and field position based on current play"""
    try:
        current_down = int(current_play.get('down', 1))
        current_distance = int(current_play.get('distance', 10))
        current_field_position = current_play.get('field_position', 'OWN 25')
        yards_gained = int(current_play.get('yards_gained', 0))
        play_result = str(current_play.get('result', '')).lower()
        
        print(f"DEBUG: Input - down: {current_down}, distance: {current_distance}, field_position: {current_field_position}, yards_gained: {yards_gained}")
        
        # Parse current field position
        field_parts = current_field_position.strip().split()
        if len(field_parts) >= 2:
            side = field_parts[0]
            try:
                yard_line = int(field_parts[1])
            except (ValueError, IndexError):
                yard_line = 25
        else:
            side = "OWN"
            yard_line = 25
        
        # Calculate new field position
        print(f"DEBUG: Starting calculation - side: {side}, yard_line: {yard_line}, yards_gained: {yards_gained}")
        
        if side == "OWN":
            new_yard_line = int(yard_line) + int(yards_gained)
            if new_yard_line >= 50:
                new_side = "OPP"
                new_yard_line = 100 - new_yard_line
                new_yard_line = max(1, new_yard_line)
            else:
                new_side = "OWN"
        else:  # OPP side
            new_yard_line = int(yard_line) - int(yards_gained)
            if new_yard_line <= 0:
                # Touchdown!
                print("DEBUG: Touchdown detected")
                return {
                    'down': 1,
                    'distance': 10,
                    'field_position': 'OWN 25',
                    'auto_calculated': True,
                    'reason': 'Touchdown - Reset for next drive'
                }
            elif new_yard_line > 50:
                new_side = "OWN"
                new_yard_line = 100 - new_yard_line
            else:
                new_side = "OPP"
                new_yard_line = max(1, new_yard_line)
        
        print(f"DEBUG: After calculation - new_side: {new_side}, new_yard_line: {new_yard_line}")
        
        # Ensure final yard line is never 0
        final_yard_line = max(1, abs(int(new_yard_line)))
        new_field_position = f"{new_side} {final_yard_line}"
        
        # Determine next down and distance
        remaining_distance = int(current_distance) - int(yards_gained)
        print(f"DEBUG: Down calculation - current_down: {current_down}, remaining_distance: {remaining_distance}")
        
        # Check for first down
        if remaining_distance <= 0:
            next_down = 1
            next_distance = 10
            reason = "First down achieved"
        elif int(current_down) >= 4:
            next_down = 1
            next_distance = 10
            if new_side == "OWN":
                new_field_position = f"OPP {100 - abs(int(new_yard_line))}"
            else:
                new_field_position = f"OWN {100 - abs(int(new_yard_line))}"
            reason = "Turnover on downs"
        else:
            next_down = int(current_down) + 1
            next_distance = max(1, remaining_distance)
            reason = f"Next down: {next_down} & {next_distance}"
        
        # Handle special cases
        if any(keyword in play_result for keyword in ['touchdown', 'td', 'score']):
            return {
                'down': 1,
                'distance': 10,
                'field_position': 'OWN 25',
                'auto_calculated': True,
                'reason': 'Touchdown scored - Reset for next drive'
            }
        elif any(keyword in play_result for keyword in ['interception', 'int', 'fumble', 'turnover']):
            if new_side == "OWN":
                new_field_position = f"OPP {100 - abs(int(new_yard_line))}"
            else:
                new_field_position = f"OWN {100 - abs(int(new_yard_line))}"
            return {
                'down': 1,
                'distance': 10,
                'field_position': new_field_position,
                'auto_calculated': True,
                'reason': 'Turnover - Opponent takes possession'
            }
        
        return {
            'down': next_down,
            'distance': next_distance,
            'field_position': new_field_position,
            'auto_calculated': True,
            'reason': reason
        }
        
    except Exception as e:
        # Fallback to safe defaults
        return {
            'down': 1,
            'distance': 10,
            'field_position': 'OWN 25',
            'auto_calculated': False,
            'reason': f'Error calculating: {str(e)}'
        }

@app.route('/box_stats/get_stats', methods=['GET'])
@login_required
def get_box_stats():
    """Get current box stats data"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            # No session yet, return empty data
            box_stats = {
                'plays': [],
                'players': {},
                'game_info': {},
                'team_stats': {
                    'total_plays': 0,
                    'efficient_plays': 0,
                    'explosive_plays': 0,
                    'negative_plays': 0,
                    'total_yards': 0,
                    'touchdowns': 0,
                    'turnovers': 0,
                    'interceptions': 0,
                    'efficiency_rate': 0.0,
                    'explosive_rate': 0.0,
                    'negative_rate': 0.0,
                    'nee_score': 0.0,
                    'avg_yards_per_play': 0.0,
                    'success_rate': 0.0
                }
            }
        else:
            # Load from server-side storage
            box_stats_data = server_session.load_session_data(session_id)
            box_stats = box_stats_data.get('box_stats', {
                'plays': [],
                'players': {},
                'game_info': {},
                'team_stats': {
                    'total_plays': 0,
                    'efficient_plays': 0,
                    'explosive_plays': 0,
                    'negative_plays': 0,
                    'total_yards': 0,
                    'touchdowns': 0,
                    'turnovers': 0,
                    'interceptions': 0,
                    'efficiency_rate': 0.0,
                    'explosive_rate': 0.0,
                    'negative_rate': 0.0,
                    'nee_score': 0.0,
                    'avg_yards_per_play': 0.0,
                    'success_rate': 0.0
                }
            })
        
        # Use the stored team stats from session (which include advanced analytics)
        # instead of recalculating basic stats
        team_stats = box_stats.get('team_stats', {
            'total_plays': 0,
            'efficient_plays': 0,
            'explosive_plays': 0,
            'negative_plays': 0,
            'total_yards': 0,
            'touchdowns': 0,
            'turnovers': 0,
            'interceptions': 0,
            'efficiency_rate': 0.0,
            'explosive_rate': 0.0,
            'negative_rate': 0.0,
            'nee_score': 0.0,
            'avg_yards_per_play': 0.0,
            'success_rate': 0.0
        })
        
        # Add basic play type counts for compatibility
        team_stats['rushing_plays'] = len([p for p in box_stats['plays'] if p.get('play_type') == 'rush'])
        team_stats['passing_plays'] = len([p for p in box_stats['plays'] if p.get('play_type') == 'pass'])
        
        print(f"DEBUG GET_STATS: Returning team stats: {team_stats}")
        print(f"DEBUG GET_STATS: Team efficiency rate: {team_stats.get('efficiency_rate', 'NOT_FOUND')}")
        print(f"DEBUG GET_STATS: Team explosive rate: {team_stats.get('explosive_rate', 'NOT_FOUND')}")
        print(f"DEBUG GET_STATS: Team NEE score: {team_stats.get('nee_score', 'NOT_FOUND')}")
        
        return jsonify({
            'success': True,
            'box_stats': box_stats,
            'team_stats': team_stats,
            'next_situation': box_stats.get('next_situation', {
                'down': 1,
                'distance': 10,
                'field_position': 'OWN 25',
                'auto_calculated': False,
                'reason': 'Starting position'
            })
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting stats: {str(e)}'}), 500

@app.route('/box_stats/reset', methods=['POST'])
@login_required
def reset_box_stats():
    """Reset all box stats data"""
    try:
        session['box_stats'] = {
            'plays': [],
            'players': {},
            'game_info': {}
        }
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Box stats reset successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error resetting stats: {str(e)}'}), 500

# Player Roster Management Routes
@app.route('/box_stats/save_roster', methods=['POST'])
@login_required
def save_player_roster():
    """Save current player profiles as a named roster (supports editing)"""
    try:
        data = request.get_json()
        roster_name = data.get('roster_name', '').strip()
        player_profiles = data.get('player_profiles', {})
        is_edit = data.get('is_edit', False)
        original_name = data.get('original_name', '')
        
        print(f"DEBUG: Save roster request - name: {roster_name}, is_edit: {is_edit}, original: {original_name}")
        print(f"DEBUG: Player profiles count: {len(player_profiles)}")
        
        if not roster_name:
            return jsonify({'error': 'Roster name is required'}), 400
            
        if not player_profiles:
            return jsonify({'error': 'No player profiles to save'}), 400
        
        # Get username from session
        username = session.get('username', 'anonymous')
        
        # Handle roster editing (rename scenario)
        if is_edit and original_name and original_name != roster_name:
            # Delete old roster file if name changed (use consistent filename logic)
            old_filename = create_safe_roster_filename(original_name)
            delete_success, delete_msg = delete_roster_data(username, old_filename)
            if delete_success:
                print(f"DEBUG: Removed old roster '{original_name}' due to rename")
        
        # Prepare roster data
        roster_data = {
            'players': player_profiles,
            'created_at': datetime.now().isoformat()
        }
        
        # Save roster to file
        success, result = save_roster_data(username, roster_name, roster_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Roster "{roster_name}" saved successfully with {len(player_profiles)} players'
            })
        else:
            return jsonify({'error': f'Failed to save roster: {result}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error saving roster: {str(e)}'}), 500

@app.route('/box_stats/load_roster', methods=['POST'])
@login_required
def load_player_roster():
    """Load a saved player roster with optimization for large rosters"""
    try:
        data = request.get_json()
        roster_name = data.get('roster_name', '').strip()
        
        if not roster_name:
            return jsonify({'error': 'Roster name is required'}), 400
        
        # Get username from session
        username = session.get('username', 'anonymous')
        
        # Create filename using consistent helper function
        filename = create_safe_roster_filename(roster_name)
        
        # Load roster from file
        roster_data, error = load_roster_data(username, filename)
        
        if error or not roster_data:
            return jsonify({'error': f'Roster "{roster_name}" not found'}), 404
        
        player_count = len(roster_data.get('players', {}))
        
        # Add performance warning for very large rosters
        if player_count > 200:
            print(f"WARNING: Loading large roster '{roster_name}' with {player_count} players")
        
        # Optimize response for large rosters
        response_data = {
            'success': True,
            'roster': roster_data,
            'player_count': player_count,
            'message': f'Roster "{roster_name}" loaded successfully'
        }
        
        # Add performance hints for frontend
        if player_count > 50:
            response_data['performance_hint'] = 'large_roster'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR loading roster: {str(e)}")
        return jsonify({'error': f'Error loading roster: {str(e)}'}), 500

@app.route('/box_stats/get_rosters', methods=['GET'])
@login_required
def get_saved_rosters():
    """Get all saved rosters for the current user"""
    try:
        # Get username from session
        username = session.get('username', 'anonymous')
        
        # Get rosters from file storage
        rosters_list = get_user_saved_rosters(username)
        
        # Add players data to each roster for frontend compatibility
        for roster in rosters_list:
            roster_data, error = load_roster_data(username, roster['filename'])
            if roster_data and not error:
                roster['players'] = roster_data.get('players', {})
            else:
                roster['players'] = {}
        
        return jsonify({
            'success': True,
            'rosters': rosters_list
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting rosters: {str(e)}'}), 500

@app.route('/box_stats/delete_roster', methods=['POST'])
@login_required
def delete_box_stats_roster():
    """Delete a saved roster"""
    try:
        data = request.get_json()
        roster_name = data.get('roster_name')
        
        if not roster_name:
            return jsonify({'success': False, 'error': 'Roster name is required'})
        
        # Get current rosters
        rosters = session.get('saved_rosters', [])
        
        # Remove the specified roster
        rosters = [r for r in rosters if r['name'] != roster_name]
        session['saved_rosters'] = rosters
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': f'Roster "{roster_name}" deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error deleting roster: {str(e)}'}), 500

@app.route('/box_stats/set_game_info', methods=['POST'])
@login_required
def set_box_stats_game_info():
    """Set game information for the current session"""
    try:
        data = request.get_json()
        
        game_info = {
            'name': data.get('name', ''),
            'opponent': data.get('opponent', ''),
            'date': data.get('date', ''),
            'location': data.get('location', ''),
            'created_at': data.get('created_at', datetime.now().isoformat())
        }
        
        # Get or create server-side session
        session_id = session.get('server_session_id')
        if not session_id:
            session_id = server_session.create_session()
            session['server_session_id'] = session_id
        
        # Load existing session data
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {
            'plays': [],
            'players': {},
            'game_info': {},
            'team_stats': {
                'total_plays': 0,
                'efficient_plays': 0,
                'explosive_plays': 0,
                'negative_plays': 0,
                'efficiency_rate': 0.0,
                'explosive_rate': 0.0,
                'avg_yards_per_play': 0.0,
                'success_rate': 0.0
            }
        })
        
        # Update game info
        box_stats['game_info'] = game_info
        
        # Save back to server-side session
        box_stats_data['box_stats'] = box_stats
        server_session.save_session_data(session_id, box_stats_data)
        
        return jsonify({
            'success': True,
            'message': 'Game information saved successfully',
            'game_info': game_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error saving game info: {str(e)}'}), 500

@app.route('/box_stats/get_game_info', methods=['GET'])
@login_required
def get_box_stats_game_info():
    """Get current game information"""
    try:
        game_info = session.get('box_stats', {}).get('game_info', {})
        
        return jsonify({
            'success': True,
            'game_info': game_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error getting game info: {str(e)}'}), 500

@app.route('/box_stats/clear_game_info', methods=['POST'])
@login_required
def clear_box_stats_game_info():
    """Clear game information for the current session"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if session_id:
            # Load existing session data
            box_stats_data = server_session.load_session_data(session_id)
            box_stats = box_stats_data.get('box_stats', {})
            
            # Clear game info
            box_stats['game_info'] = {}
            
            # Save back to server-side session
            box_stats_data['box_stats'] = box_stats
            server_session.save_session_data(session_id, box_stats_data)
        
        return jsonify({
            'success': True,
            'message': 'Game information cleared'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error clearing game info: {str(e)}'}), 500

@app.route('/box_stats/export', methods=['GET'])
@login_required
def export_box_stats():
    """Export comprehensive box stats to Excel file with multiple organized sheets"""
    try:
        import io
        from flask import send_file
        
        box_stats = session.get('box_stats', {})
        
        # Debug: Print session data structure
        print("DEBUG: Session box_stats keys:", list(box_stats.keys()))
        print("DEBUG: Plays count:", len(box_stats.get('plays', [])))
        print("DEBUG: Players count:", len(box_stats.get('players', {})))
        print("DEBUG: Team stats keys:", list(box_stats.get('team_stats', {}).keys()))
        
        if not box_stats.get('plays'):
            return jsonify({'error': 'No box stats data to export'}), 400
        
        # Get game info
        game_info = box_stats.get('game_info', {})
        plays = box_stats.get('plays', [])
        players = box_stats.get('players', {})
        team_stats = box_stats.get('team_stats', {})
        
        print("DEBUG: Sample play data:", plays[0] if plays else "No plays")
        print("DEBUG: Sample player data:", list(players.values())[0] if players else "No players")
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Sheet 1: Game Summary
            game_summary_data = {
                'Game Information': ['Date', 'Opponent', 'Location', 'Weather', 'Total Plays', 'Game Duration'],
                'Details': [
                    game_info.get('date', 'N/A'),
                    game_info.get('opponent', 'N/A'), 
                    game_info.get('location', 'N/A'),
                    game_info.get('weather', 'N/A'),
                    len(plays),
                    f"{len(plays)} plays recorded"
                ]
            }
            game_summary_df = pd.DataFrame(game_summary_data)
            game_summary_df.to_excel(writer, sheet_name='Game Summary', index=False)
            
            # Sheet 2: Play-by-Play with Player Details
            play_by_play_data = []
            for i, play in enumerate(plays, 1):
                # Get players involved in this play
                players_involved = play.get('players_involved', [])
                player_names = []
                player_stats = []
                
                print(f"DEBUG: Processing play {i}, players_involved: {players_involved}")
                
                for player in players_involved:
                    name = f"#{player.get('number', 'N/A')} {player.get('name', 'Unknown')}"
                    player_names.append(name)
                    
                    # Collect player stats for this play
                    stats = []
                    if player.get('touchdown'): stats.append('TD')
                    if player.get('fumble'): stats.append('FUM')
                    if player.get('interception'): stats.append('INT')
                    if player.get('completion'): stats.append('COMP')
                    if player.get('reception'): stats.append('REC')
                    if player.get('tackle'): stats.append('TACKLE')
                    if player.get('sack'): stats.append('SACK')
                    if player.get('interception_def'): stats.append('INT-DEF')
                    if player.get('fumble_recovery'): stats.append('FR')
                    if player.get('forced_fumble'): stats.append('FF')
                    if player.get('tackle_for_loss'): stats.append('TFL')
                    if player.get('pass_breakup'): stats.append('PBU')
                    if player.get('defensive_td'): stats.append('DEF-TD')
                    if player.get('return_yards', 0) > 0: stats.append(f"RET:{player.get('return_yards')}yds")
                    if player.get('field_goal_made'): stats.append('FG')
                    if player.get('extra_point_made'): stats.append('XP')
                    if player.get('punt_return'): stats.append('PR')
                    if player.get('kickoff_return'): stats.append('KR')
                    if player.get('coverage_tackle'): stats.append('COV')
                    if player.get('blocked_kick'): stats.append('BLK')
                    if player.get('special_teams_td'): stats.append('ST-TD')
                    
                    player_stats.append(', '.join(stats) if stats else 'N/A')
                
                play_data = {
                    'Play #': play.get('play_number', i),
                    'Phase': play.get('phase', 'N/A'),
                    'Down': play.get('down', 'N/A'),
                    'Distance': play.get('distance', 'N/A'),
                    'Field Position': play.get('field_position', 'N/A'),
                    'Play Type': play.get('play_type', 'N/A'),
                    'Play Call': play.get('play_call', 'N/A'),
                    'Result': play.get('result', 'N/A'),
                    'Yards Gained': play.get('yards_gained', 0),
                    'Players Involved': ' | '.join(player_names) if player_names else 'N/A',
                    'Player Stats': ' | '.join(player_stats) if player_stats else 'N/A',
                    'Penalty Type': play.get('penalty_type', 'N/A') if play.get('play_type') == 'penalty' else 'N/A',
                    'Penalty Yards': play.get('penalty_yards', 0) if play.get('play_type') == 'penalty' else 'N/A',
                    'Timestamp': play.get('timestamp', 'N/A')
                }
                play_by_play_data.append(play_data)
                
            print(f"DEBUG: Created {len(play_by_play_data)} play-by-play entries")
            
            if play_by_play_data:
                play_by_play_df = pd.DataFrame(play_by_play_data)
                play_by_play_df.to_excel(writer, sheet_name='Play-by-Play', index=False)
            else:
                # Create empty sheet with headers
                empty_df = pd.DataFrame(columns=['Play #', 'Phase', 'Down', 'Distance', 'Field Position', 'Play Type', 'Play Call', 'Result', 'Yards Gained', 'Players Involved', 'Player Stats', 'Penalty Type', 'Penalty Yards', 'Timestamp'])
                empty_df.to_excel(writer, sheet_name='Play-by-Play', index=False)
            
            # Sheet 3: Team Stats by Phase
            team_stats_data = []
            phases = ['offense', 'defense', 'special_teams', 'overall']
            
            for phase in phases:
                if phase in team_stats:
                    stats = team_stats[phase]
                    team_stats_data.append({
                        'Phase': phase.replace('_', ' ').title(),
                        'Total Plays': stats.get('total_plays', 0),
                        'Total Yards': stats.get('total_yards', 0),
                        'Avg Yards/Play': round(stats.get('avg_yards_per_play', 0), 1),
                        'Efficient Plays': stats.get('efficient_plays', 0),
                        'Efficiency Rate': f"{stats.get('efficiency_rate', 0)}%",
                        'Explosive Plays': stats.get('explosive_plays', 0),
                        'Explosive Rate': f"{stats.get('explosive_rate', 0)}%",
                        'Negative Plays': stats.get('negative_plays', 0),
                        'Negative Rate': f"{stats.get('negative_rate', 0)}%",
                        'NEE Score': stats.get('nee_score', 0),
                        'Touchdowns': stats.get('touchdowns', 0),
                        'Turnovers': stats.get('turnovers', 0),
                        'Interceptions': stats.get('interceptions', 0)
                    })
            
            if team_stats_data:
                team_stats_df = pd.DataFrame(team_stats_data)
                team_stats_df.to_excel(writer, sheet_name='Team Stats by Phase', index=False)
            else:
                # Create empty sheet with headers
                empty_team_df = pd.DataFrame(columns=['Phase', 'Total Plays', 'Total Yards', 'Avg Yards/Play', 'Efficient Plays', 'Efficiency Rate', 'Explosive Plays', 'Explosive Rate', 'Negative Plays', 'Negative Rate', 'NEE Score', 'Touchdowns', 'Turnovers', 'Interceptions'])
                empty_team_df.to_excel(writer, sheet_name='Team Stats by Phase', index=False)
            
            # Sheet 4: Individual Player Box Stats
            player_box_stats = []
            for player_id, player_data in players.items():
                player_stats = {
                    'Player': f"#{player_data.get('number', 'N/A')} {player_data.get('name', 'Unknown')}",
                    'Position': player_data.get('position', 'N/A'),
                    
                    # Offensive Stats
                    'Rush Att': player_data.get('rushing_attempts', 0),
                    'Rush Yds': player_data.get('rushing_yards', 0),
                    'Receptions': player_data.get('receptions', 0),
                    'Rec Yds': player_data.get('receiving_yards', 0),
                    'Pass Att': player_data.get('passing_attempts', 0),
                    'Pass Comp': player_data.get('passing_completions', 0),
                    'Pass Yds': player_data.get('passing_yards', 0),
                    'Touchdowns': player_data.get('touchdowns', 0),
                    'Fumbles': player_data.get('fumbles', 0),
                    'Interceptions': player_data.get('interceptions', 0),
                    
                    # Defensive Stats
                    'Tackles': player_data.get('tackles_total', 0),
                    'Solo Tackles': player_data.get('tackles_solo', 0),
                    'Sacks': player_data.get('sacks', 0),
                    'INT (Def)': player_data.get('interceptions_def', 0),
                    'Pass Breakups': player_data.get('pass_breakups', 0),
                    'Fumble Recoveries': player_data.get('fumble_recoveries', 0),
                    'Forced Fumbles': player_data.get('forced_fumbles', 0),
                    'TFL': player_data.get('tackles_for_loss', 0),
                    'Def TDs': player_data.get('defensive_tds', 0),
                    'Return Yards': player_data.get('return_yards', 0),
                    
                    # Special Teams Stats
                    'FG Made': player_data.get('field_goals_made', 0),
                    'FG Att': player_data.get('field_goals_attempted', 0),
                    'XP Made': player_data.get('extra_points_made', 0),
                    'XP Att': player_data.get('extra_points_attempted', 0),
                    'Punts': player_data.get('punts', 0),
                    'Punt Yds': player_data.get('punt_yards', 0),
                    'KR': player_data.get('kickoff_returns', 0),
                    'KR Yds': player_data.get('kickoff_return_yards', 0),
                    'PR': player_data.get('punt_returns', 0),
                    'PR Yds': player_data.get('punt_return_yards', 0),
                    'Coverage Tackles': player_data.get('coverage_tackles', 0),
                    'Blocked Kicks': player_data.get('blocked_kicks', 0),
                    
                    # Advanced Analytics (only for offensive players)
                    'Total Plays': player_data.get('total_plays', 0),
                    'Efficiency Rate': f"{player_data.get('efficiency_rate', 0)}%" if player_data.get('total_plays', 0) > 0 else 'N/A',
                    'Explosive Rate': f"{player_data.get('explosive_rate', 0)}%" if player_data.get('total_plays', 0) > 0 else 'N/A',
                    'Negative Rate': f"{player_data.get('negative_rate', 0)}%" if player_data.get('total_plays', 0) > 0 else 'N/A',
                    'NEE Score': player_data.get('nee_score', 0) if player_data.get('total_plays', 0) > 0 else 'N/A'
                }
                player_box_stats.append(player_stats)
            
            if player_box_stats:
                player_box_stats_df = pd.DataFrame(player_box_stats)
                player_box_stats_df.to_excel(writer, sheet_name='Player Box Stats', index=False)
                print(f"DEBUG: Created Player Box Stats sheet with {len(player_box_stats)} players")
            else:
                # Create empty sheet with headers
                empty_player_df = pd.DataFrame(columns=['Player', 'Position', 'Rush Att', 'Rush Yds', 'Receptions', 'Rec Yds', 'Pass Att', 'Pass Comp', 'Pass Yds', 'Touchdowns', 'Fumbles', 'Interceptions', 'Tackles', 'Solo Tackles', 'Sacks', 'INT (Def)', 'Pass Breakups', 'Fumble Recoveries', 'Forced Fumbles', 'TFL', 'Def TDs', 'Return Yards'])
                empty_player_df.to_excel(writer, sheet_name='Player Box Stats', index=False)
                print("DEBUG: Created empty Player Box Stats sheet")
            
            # Sheet 5: Offensive Players Only (Detailed)
            offensive_players = []
            for player_id, player_data in players.items():
                if (player_data.get('rushing_attempts', 0) > 0 or 
                    player_data.get('receptions', 0) > 0 or 
                    player_data.get('passing_attempts', 0) > 0):
                    
                    offensive_stats = {
                        'Player': f"#{player_data.get('number', 'N/A')} {player_data.get('name', 'Unknown')}",
                        'Position': player_data.get('position', 'N/A'),
                        'Rush Att': player_data.get('rushing_attempts', 0),
                        'Rush Yds': player_data.get('rushing_yards', 0),
                        'Rush Avg': round(player_data.get('rushing_yards', 0) / max(player_data.get('rushing_attempts', 1), 1), 1),
                        'Receptions': player_data.get('receptions', 0),
                        'Rec Yds': player_data.get('receiving_yards', 0),
                        'Rec Avg': round(player_data.get('receiving_yards', 0) / max(player_data.get('receptions', 1), 1), 1),
                        'Pass Comp': player_data.get('passing_completions', 0),
                        'Pass Att': player_data.get('passing_attempts', 0),
                        'Pass Yds': player_data.get('passing_yards', 0),
                        'Comp %': round((player_data.get('passing_completions', 0) / max(player_data.get('passing_attempts', 1), 1)) * 100, 1),
                        'Touchdowns': player_data.get('touchdowns', 0),
                        'Fumbles': player_data.get('fumbles', 0),
                        'Interceptions': player_data.get('interceptions', 0),
                        'Total Plays': player_data.get('total_plays', 0),
                        'Efficiency Rate': f"{player_data.get('efficiency_rate', 0)}%",
                        'Explosive Rate': f"{player_data.get('explosive_rate', 0)}%",
                        'NEE Score': player_data.get('nee_score', 0)
                    }
                    offensive_players.append(offensive_stats)
            
            if offensive_players:
                offensive_df = pd.DataFrame(offensive_players)
                offensive_df.to_excel(writer, sheet_name='Offensive Players', index=False)
            
            # Sheet 6: Defensive Players Only (Detailed)
            defensive_players = []
            for player_id, player_data in players.items():
                if (player_data.get('tackles_total', 0) > 0 or 
                    player_data.get('sacks', 0) > 0 or 
                    player_data.get('interceptions_def', 0) > 0 or
                    player_data.get('pass_breakups', 0) > 0):
                    
                    defensive_stats = {
                        'Player': f"#{player_data.get('number', 'N/A')} {player_data.get('name', 'Unknown')}",
                        'Position': player_data.get('position', 'N/A'),
                        'Total Tackles': player_data.get('tackles_total', 0),
                        'Solo Tackles': player_data.get('tackles_solo', 0),
                        'Assisted Tackles': player_data.get('tackles_assisted', 0),
                        'Sacks': player_data.get('sacks', 0),
                        'TFL': player_data.get('tackles_for_loss', 0),
                        'QB Hits': player_data.get('qb_hits', 0),
                        'Interceptions': player_data.get('interceptions_def', 0),
                        'Pass Breakups': player_data.get('pass_breakups', 0),
                        'Fumble Recoveries': player_data.get('fumble_recoveries', 0),
                        'Forced Fumbles': player_data.get('forced_fumbles', 0),
                        'Defensive TDs': player_data.get('defensive_tds', 0),
                        'Return Yards': player_data.get('return_yards', 0),
                        'Coverage Tackles': player_data.get('coverage_tackles', 0)
                    }
                    defensive_players.append(defensive_stats)
            
            if defensive_players:
                defensive_df = pd.DataFrame(defensive_players)
                defensive_df.to_excel(writer, sheet_name='Defensive Players', index=False)
        
        output.seek(0)
        
        # Generate filename with game info
        opponent = game_info.get('opponent', 'Game')
        date = game_info.get('date', 'Unknown')
        filename = f"Box_Stats_{opponent}_{date}.xlsx".replace(' ', '_').replace('/', '-')
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': f'Error exporting stats: {str(e)}'}), 500

@app.route('/box_stats/update_player_stats', methods=['POST'])
@login_required
def update_player_stats():
    """Update player statistics with edited values"""
    try:
        data = request.get_json()
        updated_players = data.get('players', {})
        
        if not updated_players:
            return jsonify({'error': 'No player data provided'}), 400
        
        # Initialize box stats if not exists
        if 'box_stats' not in session:
            session['box_stats'] = {
                'plays': [],
                'players': {},
                'game_info': {},
                'team_stats': {
                    'total_plays': 0,
                    'efficient_plays': 0,
                    'explosive_plays': 0,
                    'total_yards': 0,
                    'efficiency_rate': 0.0,
                    'explosive_rate': 0.0,
                    'negative_plays': 0,
                    'negative_rate': 0.0,
                    'nee_score': 0.0,
                    'avg_yards_per_play': 0.0,
                    'success_rate': 0.0
                },
                'play_call_stats': {},  # Track analytics by play call
                'next_situation': {
                    'down': 1,
                    'distance': 10,
                    'field_position': 'OWN 25'
                }
            }
        
        # Update player statistics
        for player_number, stats in updated_players.items():
            # Ensure player exists in session
            if player_number not in session['box_stats']['players']:
                session['box_stats']['players'][player_number] = {}
            
            # Update all provided stats
            session['box_stats']['players'][player_number].update({
                'completions': int(stats.get('completions', 0)),
                'attempts': int(stats.get('attempts', 0)),
                'passing_yards': int(stats.get('passing_yards', 0)),
                'passing_tds': int(stats.get('passing_tds', 0)),
                'interceptions': int(stats.get('interceptions', 0)),
                'carries': int(stats.get('carries', 0)),
                'rushing_yards': int(stats.get('rushing_yards', 0)),
                'rushing_tds': int(stats.get('rushing_tds', 0)),
                'receptions': int(stats.get('receptions', 0)),
                'receiving_yards': int(stats.get('receiving_yards', 0)),
                'receiving_tds': int(stats.get('receiving_tds', 0)),
                'fumbles': int(stats.get('fumbles', 0)),
                'touchdowns': int(stats.get('touchdowns', 0))
            })
            
            # Calculate derived stats
            player_stats = session['box_stats']['players'][player_number]
            
            # Calculate total yards
            total_yards = (player_stats.get('passing_yards', 0) + 
                          player_stats.get('rushing_yards', 0) + 
                          player_stats.get('receiving_yards', 0))
            player_stats['total_yards'] = total_yards
            
            # Calculate completion percentage
            attempts = player_stats.get('attempts', 0)
            if attempts > 0:
                player_stats['completion_percentage'] = round((player_stats.get('completions', 0) / attempts) * 100, 1)
            else:
                player_stats['completion_percentage'] = 0.0
            
            # Calculate yards per carry
            carries = player_stats.get('carries', 0)
            if carries > 0:
                player_stats['yards_per_carry'] = round(player_stats.get('rushing_yards', 0) / carries, 1)
            else:
                player_stats['yards_per_carry'] = 0.0
            
            # Calculate yards per reception
            receptions = player_stats.get('receptions', 0)
            if receptions > 0:
                player_stats['yards_per_reception'] = round(player_stats.get('receiving_yards', 0) / receptions, 1)
            else:
                player_stats['yards_per_reception'] = 0.0
        
        session.modified = True
        
        print(f"DEBUG: Updated player stats for {len(updated_players)} players")
        
        return jsonify({
            'success': True,
            'message': f'Updated statistics for {len(updated_players)} players',
            'updated_players': list(updated_players.keys())
        })
        
    except Exception as e:
        print(f"ERROR: Failed to update player stats: {str(e)}")
        return jsonify({'error': f'Error updating player statistics: {str(e)}'}), 500

@app.route('/box_stats/save_game', methods=['POST'])
@login_required
def save_current_game():
    """Save the current game data to file"""
    try:
        data = request.get_json()
        game_name = data.get('game_name', '').strip()
        
        if not game_name:
            return jsonify({'error': 'Game name is required'}), 400
        
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session found'}), 400
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        
        if not box_stats.get('plays'):
            return jsonify({'error': 'No game data to save'}), 400
        
        # Get username from session
        username = session.get('username', 'anonymous')
        
        # Use existing game info if available, otherwise create basic info
        game_info = box_stats.get('game_info', {})
        if not game_info.get('name'):
            game_info['name'] = game_name
        if not game_info.get('created_at'):
            game_info['created_at'] = datetime.now().isoformat()
        
        # Update box_stats with the game info
        box_stats['game_info'] = game_info
        
        # Save game data
        success, result = save_game_data(username, game_name, box_stats)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Game "{game_name}" saved successfully',
                'filepath': result
            })
        else:
            return jsonify({'error': f'Failed to save game: {result}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error saving game: {str(e)}'}), 500

@app.route('/box_stats/saved_games', methods=['GET'])
@login_required
def get_saved_games():
    """Get list of saved games for the current user"""
    try:
        username = session.get('username', 'anonymous')
        games = get_user_saved_games(username)
        
        return jsonify({
            'success': True,
            'games': games
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting saved games: {str(e)}'}), 500

@app.route('/box_stats/load_game', methods=['POST'])
@login_required
def load_saved_game():
    """Load a saved game into the current session"""
    try:
        data = request.get_json()
        filename = data.get('filename', '').strip()
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        username = session.get('username', 'anonymous')
        
        # Load game data
        game_data, error = load_game_data(username, filename)
        
        if error:
            return jsonify({'error': f'Failed to load game: {error}'}), 500
        
        # Get or create server-side session
        session_id = session.get('server_session_id')
        if not session_id:
            session_id = server_session.create_session()
            session['server_session_id'] = session_id
        
        # Load data into server-side session storage
        box_stats_data = {
            'box_stats': {
                'plays': game_data.get('plays', []),
                'players': game_data.get('players', {}),
                'team_stats': game_data.get('team_stats', {}),
                'game_info': game_data.get('game_info', {}),
                'play_call_stats': game_data.get('play_call_stats', {}),
                'next_situation': {
                    'down': 1,
                    'distance': 10,
                    'field_position': 'OWN 25'
                }
            }
        }
        
        # Apply backward compatibility for loaded game data
        # Convert old team_stats format to new phase-specific format if needed
        if 'team_stats' in box_stats_data['box_stats']:
            team_stats = box_stats_data['box_stats']['team_stats']
            
            # Check if this is old format (has direct stats) vs new format (has phases)
            if 'total_plays' in team_stats and 'offense' not in team_stats:
                # Old format - convert to new phase-specific format
                old_stats = dict(team_stats)  # Copy old stats
                box_stats_data['box_stats']['team_stats'] = {
                    'offense': old_stats,
                    'defense': {
                        'total_plays': 0, 'efficient_plays': 0, 'explosive_plays': 0, 'negative_plays': 0,
                        'total_yards': 0, 'touchdowns': 0, 'turnovers': 0, 'interceptions': 0,
                        'efficiency_rate': 0.0, 'explosive_rate': 0.0, 'negative_rate': 0.0,
                        'nee_score': 0.0, 'avg_yards_per_play': 0.0, 'success_rate': 0.0,
                        'nee_progression': [], 'efficiency_progression': [], 'explosive_progression': []
                    },
                    'special_teams': {
                        'total_plays': 0, 'efficient_plays': 0, 'explosive_plays': 0, 'negative_plays': 0,
                        'total_yards': 0, 'touchdowns': 0, 'turnovers': 0, 'interceptions': 0,
                        'efficiency_rate': 0.0, 'explosive_rate': 0.0, 'negative_rate': 0.0,
                        'nee_score': 0.0, 'avg_yards_per_play': 0.0, 'success_rate': 0.0,
                        'nee_progression': [], 'efficiency_progression': [], 'explosive_progression': []
                    },
                    'overall': old_stats
                }
            
            # Ensure all advanced analytics fields exist in all phases
            required_team_fields = {
                'negative_plays': 0, 'efficiency_rate': 0.0, 'explosive_rate': 0.0, 'negative_rate': 0.0,
                'nee_score': 0.0, 'avg_yards_per_play': 0.0, 'success_rate': 0.0,
                'nee_progression': [], 'efficiency_progression': [], 'avg_yards_progression': []
            }
            
            all_phases = ['offense', 'defense', 'special_teams', 'overall']
            for phase in all_phases:
                if phase in box_stats_data['box_stats']['team_stats']:
                    for field, default_value in required_team_fields.items():
                        if field not in box_stats_data['box_stats']['team_stats'][phase]:
                            box_stats_data['box_stats']['team_stats'][phase][field] = default_value
        
        # Ensure all advanced analytics fields exist in loaded player stats
        if 'players' in box_stats_data['box_stats']:
            required_player_fields = {
                'negative_plays': 0,
                'efficiency_rate': 0.0,
                'explosive_rate': 0.0,
                'negative_rate': 0.0,
                'nee_score': 0.0,
                'nee_progression': [],
                'efficiency_progression': [],
                'explosive_progression': []
            }
            
            for player_key, player_data in box_stats_data['box_stats']['players'].items():
                for field, default_value in required_player_fields.items():
                    if field not in player_data:
                        player_data[field] = default_value
        
        # Save the loaded game data to server-side session
        server_session.save_session_data(session_id, box_stats_data)
        
        return jsonify({
            'success': True,
            'message': f'Game loaded successfully',
            'game_data': {
                'game_info': game_data.get('game_info', {}),
                'total_plays': len(game_data.get('plays', [])),
                'total_players': len(game_data.get('players', {})),
                'team_stats': game_data.get('team_stats', {})
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error loading game: {str(e)}'}), 500

@app.route('/box_stats/delete_game', methods=['POST'])
@login_required
def delete_saved_game():
    """Delete a saved game"""
    try:
        data = request.get_json()
        filename = data.get('filename', '').strip()
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        username = session.get('username', 'anonymous')
        user_dir = get_user_games_dir(username)
        filepath = os.path.join(user_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Game file not found'}), 404
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Game deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error deleting game: {str(e)}'}), 500

@app.route('/box_stats/nee_progression/<player_number>', methods=['GET'])
@login_required
def get_player_nee_progression(player_number):
    """Get NEE progression data for a specific player"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        players = box_stats.get('players', {})
        
        player_key = str(player_number)
        if player_key not in players:
            return jsonify({'error': f'Player #{player_number} not found'}), 404
        
        player_data = players[player_key]
        nee_progression = player_data.get('nee_progression', [])
        
        return jsonify({
            'success': True,
            'player_number': player_number,
            'player_name': player_data.get('name', f'Player #{player_number}'),
            'player_position': player_data.get('position', ''),
            'nee_progression': nee_progression,
            'current_nee': player_data.get('nee_score', 0.0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting player NEE progression: {str(e)}'}), 500

@app.route('/box_stats/team_nee_progression', methods=['GET'])
@login_required
def get_team_nee_progression():
    """Get NEE progression data for the team"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Use overall team stats for progression (combines all phases)
        overall_stats = team_stats.get('overall', {})
        nee_progression = overall_stats.get('nee_progression', [])
        
        print(f"DEBUG TEAM NEE ENDPOINT: Found {len(nee_progression)} NEE progression entries")
        print(f"DEBUG TEAM NEE ENDPOINT: Overall stats keys: {list(overall_stats.keys())}")
        print(f"DEBUG TEAM NEE ENDPOINT: Current NEE: {overall_stats.get('nee_score', 'NOT_FOUND')}")
        
        return jsonify({
            'success': True,
            'nee_progression': nee_progression,
            'current_nee': overall_stats.get('nee_score', 0.0),
            'total_plays': overall_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting team NEE progression: {str(e)}'}), 500

@app.route('/box_stats/efficiency_progression/<player_number>', methods=['GET'])
@login_required
def get_player_efficiency_progression(player_number):
    """Get efficiency progression data for a specific player"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        players = box_stats.get('players', {})
        
        player_key = str(player_number)
        if player_key not in players:
            return jsonify({'error': f'Player #{player_number} not found'}), 404
        
        player_data = players[player_key]
        efficiency_progression = player_data.get('efficiency_progression', [])
        
        return jsonify({
            'success': True,
            'player_number': player_number,
            'player_name': player_data.get('name', f'Player #{player_number}'),
            'player_position': player_data.get('position', ''),
            'efficiency_progression': efficiency_progression,
            'current_efficiency': player_data.get('efficiency_rate', 0.0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting player efficiency progression: {str(e)}'}), 500

@app.route('/box_stats/team_efficiency_progression', methods=['GET'])
@login_required
def get_team_efficiency_progression():
    """Get efficiency progression data for the team"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Use overall team stats for progression (combines all phases)
        overall_stats = team_stats.get('overall', {})
        efficiency_progression = overall_stats.get('efficiency_progression', [])
        
        return jsonify({
            'success': True,
            'efficiency_progression': efficiency_progression,
            'current_efficiency': overall_stats.get('efficiency_rate', 0.0),
            'total_plays': overall_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting team efficiency progression: {str(e)}'}), 500

@app.route('/box_stats/team_explosive_progression', methods=['GET'])
@login_required
def get_team_explosive_progression():
    """Get explosive rate progression data for the team"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Use overall team stats for progression (combines all phases)
        overall_stats = team_stats.get('overall', {})
        explosive_progression = overall_stats.get('explosive_progression', [])
        
        return jsonify({
            'success': True,
            'explosive_progression': explosive_progression,
            'current_explosive_rate': overall_stats.get('explosive_rate', 0.0),
            'total_plays': overall_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting team explosive progression: {str(e)}'}), 500

@app.route('/box_stats/phase_nee_progression/<phase>', methods=['GET'])
@login_required
def get_phase_nee_progression(phase):
    """Get NEE progression data for a specific phase"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Get phase-specific stats
        phase_stats = team_stats.get(phase, {})
        nee_progression = phase_stats.get('nee_progression', [])
        
        return jsonify({
            'success': True,
            'nee_progression': nee_progression,
            'current_nee': phase_stats.get('nee_score', 0.0),
            'total_plays': phase_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting {phase} NEE progression: {str(e)}'}), 500

@app.route('/box_stats/phase_efficiency_progression/<phase>', methods=['GET'])
@login_required
def get_phase_efficiency_progression(phase):
    """Get efficiency progression data for a specific phase"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Get phase-specific stats
        phase_stats = team_stats.get(phase, {})
        efficiency_progression = phase_stats.get('efficiency_progression', [])
        
        return jsonify({
            'success': True,
            'efficiency_progression': efficiency_progression,
            'current_efficiency': phase_stats.get('efficiency_rate', 0.0),
            'total_plays': phase_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting {phase} efficiency progression: {str(e)}'}), 500

@app.route('/box_stats/phase_explosive_progression/<phase>', methods=['GET'])
@login_required
def get_phase_explosive_progression(phase):
    """Get explosive rate progression data for a specific phase"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Get phase-specific stats
        phase_stats = team_stats.get(phase, {})
        explosive_progression = phase_stats.get('explosive_progression', [])
        
        return jsonify({
            'success': True,
            'explosive_progression': explosive_progression,
            'current_explosive_rate': phase_stats.get('explosive_rate', 0.0),
            'total_plays': phase_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting {phase} explosive progression: {str(e)}'}), 500

@app.route('/box_stats/explosive_progression/<player_number>', methods=['GET'])
@login_required
def get_player_explosive_progression(player_number):
    """Get explosive progression data for a specific player"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        players = box_stats.get('players', {})
        
        player_key = str(player_number)
        if player_key not in players:
            return jsonify({'error': f'Player #{player_number} not found'}), 404
        
        player_data = players[player_key]
        explosive_progression = player_data.get('explosive_progression', [])
        
        return jsonify({
            'success': True,
            'player_number': player_number,
            'player_name': player_data.get('name', f'Player #{player_number}'),
            'player_position': player_data.get('position', ''),
            'explosive_progression': explosive_progression,
            'current_explosive_rate': player_data.get('explosive_rate', 0.0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting player explosive progression: {str(e)}'}), 500

@app.route('/box_stats/team_avg_yards_progression', methods=['GET'])
@login_required
def get_team_avg_yards_progression():
    """Get average yards progression data for the team"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        # Use overall team stats for progression (combines all phases)
        overall_stats = team_stats.get('overall', {})
        avg_yards_progression = overall_stats.get('avg_yards_progression', [])
        
        return jsonify({
            'success': True,
            'avg_yards_progression': avg_yards_progression,
            'current_avg_yards': overall_stats.get('avg_yards_per_play', 0.0),
            'total_plays': overall_stats.get('total_plays', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting team avg yards progression: {str(e)}'}), 500

@app.route('/box_stats/debug_team_data', methods=['GET'])
@login_required
def debug_team_data():
    """Debug endpoint to check team progression data structure"""
    try:
        session_id = session.get('server_session_id')
        if not session_id:
            return jsonify({'error': 'No active session'}), 404
        
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        team_stats = box_stats.get('team_stats', {})
        
        debug_info = {
            'session_id': session_id,
            'team_stats_keys': list(team_stats.keys()),
            'overall_keys': list(team_stats.get('overall', {}).keys()),
            'overall_nee_progression_length': len(team_stats.get('overall', {}).get('nee_progression', [])),
            'overall_explosive_progression_length': len(team_stats.get('overall', {}).get('explosive_progression', [])),
            'overall_efficiency_progression_length': len(team_stats.get('overall', {}).get('efficiency_progression', [])),
            'total_plays': len(box_stats.get('plays', [])),
            'sample_nee_data': team_stats.get('overall', {}).get('nee_progression', [])[:3],
            'sample_explosive_data': team_stats.get('overall', {}).get('explosive_progression', [])[:3]
        }
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({'error': f'Debug error: {str(e)}'}), 500

@app.route('/box_stats/play_call_analytics', methods=['GET'])
@login_required
def get_play_call_analytics():
    """Get analytics for all play calls in the current session"""
    try:
        # Get server-side session ID
        session_id = session.get('server_session_id')
        if not session_id:
            # No session yet, return empty data
            return jsonify({
                'success': True,
                'play_call_analytics': [],
                'total_play_calls': 0
            })
        
        # Load session data from server-side storage
        box_stats_data = server_session.load_session_data(session_id)
        box_stats = box_stats_data.get('box_stats', {})
        play_call_stats = box_stats.get('play_call_stats', {})
        
        print(f"DEBUG: Getting play call analytics - found {len(play_call_stats)} play calls")
        print(f"DEBUG: Play call stats keys: {list(play_call_stats.keys())}")
        
        # Sort play calls by total plays (most used first)
        sorted_play_calls = []
        for play_call, stats in play_call_stats.items():
            sorted_play_calls.append({
                'play_call': play_call,
                **stats
            })
        
        # Sort by total plays descending
        sorted_play_calls.sort(key=lambda x: x['total_plays'], reverse=True)
        
        print(f"DEBUG: Returning {len(sorted_play_calls)} sorted play calls")
        
        return jsonify({
            'success': True,
            'play_call_analytics': sorted_play_calls,
            'total_play_calls': len(sorted_play_calls)
        })
        
    except Exception as e:
        print(f"ERROR: Failed to get play call analytics: {str(e)}")
        return jsonify({'error': f'Error getting play call analytics: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5008))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    if debug:
        print(f"Starting Flask app on port {port}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
