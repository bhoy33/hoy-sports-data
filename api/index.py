from app_stable import app

# Vercel serverless function handler
def handler(request, context):
    return app

# For direct import
application = app
