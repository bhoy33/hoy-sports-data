#!/usr/bin/env python3
"""
Minimal test app to diagnose Railway deployment issues
"""
import os
import sys
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Test deployment successful',
        'python_version': sys.version,
        'env_vars': {
            'PORT': os.environ.get('PORT', 'not set'),
            'SUPABASE_URL': 'set' if os.environ.get('SUPABASE_URL') else 'not set',
            'SUPABASE_ANON_KEY': 'set' if os.environ.get('SUPABASE_ANON_KEY') else 'not set',
            'SECRET_KEY': 'set' if os.environ.get('SECRET_KEY') else 'not set'
        }
    })

@app.route('/test-imports')
def test_imports():
    import_results = {}
    
    # Test critical imports
    try:
        import flask
        import_results['flask'] = f'✅ {flask.__version__}'
    except Exception as e:
        import_results['flask'] = f'❌ {str(e)}'
    
    try:
        import pandas
        import_results['pandas'] = f'✅ {pandas.__version__}'
    except Exception as e:
        import_results['pandas'] = f'❌ {str(e)}'
    
    try:
        import supabase
        import_results['supabase'] = '✅ imported'
    except Exception as e:
        import_results['supabase'] = f'❌ {str(e)}'
    
    try:
        import altair
        import_results['altair'] = f'✅ {altair.__version__}'
    except Exception as e:
        import_results['altair'] = f'❌ {str(e)}'
    
    return jsonify({
        'status': 'import_test_complete',
        'imports': import_results
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting test app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
