from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import pandas as pd
import altair as alt
import json
import io
import base64
from werkzeug.utils import secure_filename
import os
from functools import wraps

# Configure Altair to use inline data for web serving
alt.data_transformers.disable_max_rows()
alt.data_transformers.enable('default')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'hoysportsdata_secret_key_2025'  # For session management

# Password protection configuration
SITE_PASSWORD = 'scots25'
ADMIN_PASSWORD = 'Jackets21!'

# Maintenance mode state (stored in memory for simplicity)
maintenance_mode = False

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
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
            return redirect(url_for('admin_dashboard'))
        
        # Check for regular user password
        elif password == SITE_PASSWORD:
            # Check if maintenance mode is active
            if maintenance_mode:
                return render_template('login.html', 
                    error='Our team is currently working on fixing bugs and/or adding features to make the app better for you! If you need immediate access contact your representative for Hoy Sports Data.',
                    maintenance_mode=True)
            session['authenticated'] = True
            session['is_admin'] = False
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
    """Defensive Self Scout Analysis (Hoy's Template) - Coming Soon"""
    return render_template('coming_soon.html', 
                         title='Defensive Self Scout Analysis (Hoy\'s Template)',
                         description='Defensive performance analysis using Hoy\'s specialized template.')

@app.route('/analytics/offensive-hudl')
@login_required
def offensive_hudl_analysis():
    """Offensive Self Scout Analysis (Hudl Excel Export) - Dynamic Column Recognition"""
    return render_template('hudl_analysis.html',
                         analysis_type='offensive',
                         title='Offensive Self Scout Analysis (Hudl Excel Export)',
                         description='Upload your Hudl Excel export and we\'ll automatically detect and analyze your offensive stats.')

@app.route('/analytics/defensive-hudl')
@login_required
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        combined_df = load_and_process_data(filepath, selected_sheets)
        
        # Get all data for preview (like Streamlit)
        preview_df = combined_df.copy()
        
        # Handle NaN values that can't be serialized to JSON
        preview_df = preview_df.fillna('')  # Replace NaN with empty string
        
        # Convert to format suitable for HTML table
        preview_data = {
            'columns': preview_df.columns.tolist(),
            'rows': preview_df.values.tolist()
        }
        
        return jsonify({
            'success': True,
            'data': preview_data,
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
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        combined_df = load_and_process_data(filepath, selected_sheets)
        
        # Create play identifiers (assuming there's a play number or we'll use row index)
        plays = []
        for idx, row in combined_df.iterrows():
            # Try to find a play identifier column, otherwise use row index
            play_id = None
            for col in ['Play', 'PlayNumber', 'Play_Number', 'play', 'play_number']:
                if col in combined_df.columns and pd.notna(row[col]):
                    play_id = str(row[col])
                    break
            
            if not play_id:
                play_id = f"Play {idx + 1}"
            
            # Create a description for the play
            description_parts = []
            for col in ['Down', 'Distance', 'Formation', 'PlayType', 'Result']:
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
    """Compare selected plays and return their data"""
    try:
        data = request.get_json()
        selected_plays = data.get('selected_plays', [])
        
        if not selected_plays:
            return jsonify({'error': 'No plays selected'}), 400
        
        # Get the uploaded file path from session
        filepath = session.get('uploaded_file_path')
        if not filepath:
            return jsonify({'error': 'No file uploaded'}), 400
        
        # Load the Excel file
        xls = pd.ExcelFile(filepath)
        
        # Find plays across all sheets
        plays_data = []
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                df.columns = df.columns.str.strip().str.lower()
                
                # Add sheet info
                df['sheet_name'] = sheet_name
                df['sheet_order'] = list(xls.sheet_names).index(sheet_name)
                
                # Filter for selected plays
                if 'play' in df.columns:
                    matching_plays = df[df['play'].isin(selected_plays)]
                    if not matching_plays.empty:
                        plays_data.append(matching_plays)
                        
            except Exception as e:
                continue
        
        if not plays_data:
            return jsonify({'error': 'No matching plays found'}), 404
        
        # Combine all matching plays
        combined_plays = pd.concat(plays_data, ignore_index=True)
        
        # Convert to JSON-serializable format
        result_data = combined_plays.to_dict('records')
        
        return jsonify({
            'success': True,
            'plays_data': result_data,
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
@login_required
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
@login_required
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
@login_required
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(debug=True, host='0.0.0.0', port=port)
