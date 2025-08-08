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
    """Offensive Self Scout Analysis (Hudl Excel Export) - Coming Soon"""
    return render_template('coming_soon.html',
                         title='Offensive Self Scout Analysis (Hudl Excel Export)',
                         description='Offensive analysis optimized for Hudl Excel export format.')

@app.route('/analytics/defensive-hudl')
@login_required
def defensive_hudl_analysis():
    """Defensive Self Scout Analysis (Hudl Excel Export) - Coming Soon"""
    return render_template('coming_soon.html',
                         title='Defensive Self Scout Analysis (Hudl Excel Export)',
                         description='Defensive analysis designed for Hudl Excel export data.')

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
        filename = data.get('filename')
        selected_sheets = data.get('sheets', [])
        play_indices = data.get('play_indices', [])
        
        if not filename or not selected_sheets or not play_indices:
            return jsonify({'error': 'Missing filename, sheets, or play indices'}), 400
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        combined_df = load_and_process_data(filepath, selected_sheets)
        
        # Get the selected plays
        selected_plays = combined_df.iloc[play_indices].copy()
        
        # Handle NaN values
        selected_plays = selected_plays.fillna('')
        
        # Prepare data for comparison table
        comparison_data = {
            'columns': selected_plays.columns.tolist(),
            'plays': []
        }
        
        for idx, (_, row) in enumerate(selected_plays.iterrows()):
            play_data = {
                'play_number': idx + 1,
                'data': row.tolist()
            }
            comparison_data['plays'].append(play_data)
        
        return jsonify({
            'success': True,
            'comparison_data': comparison_data
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(debug=True, host='0.0.0.0', port=port)
