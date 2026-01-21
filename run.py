from app import create_app, init_db
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Initialize DB if it doesn't exist
    if not os.path.exists('leadscan.db'):
        init_db()
            
    app.run(debug=True, ssl_context='adhoc')
