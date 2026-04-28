import sys
import os

# Add parent directory to path so that we can import src module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from src.pipeline import BISRAGPipeline

app = Flask(__name__)
CORS(app)

# Initialize pipeline with caching in mind (loaded once when serverless function warms up)
pipeline = BISRAGPipeline(use_llm=True, top_k=5)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400
    
    question = data['query']
    
    try:
        result = pipeline.query(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "BIS Recommendation Engine API is running.",
        "endpoints": {
            "POST /api/recommend": "Send a JSON payload with {'query': 'your text here'}"
        }
    })

# Local testing
if __name__ == '__main__':
    app.run(debug=True, port=5003)
