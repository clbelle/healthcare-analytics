from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
from scipy.sparse import csr_matrix, hstack

import os
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
log_file = os.path.join(BASE_DIR, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(handler)

app = Flask(__name__)

# Initialize model artifacts
xgb_model = None
tfidf_vectorizer = None
metadata = None
structured_feature_names = []
medians = {}

print("Loading model artifacts...")
try:
    xgb_model = joblib.load(os.path.join(BASE_DIR, 'xgb_triage_model.joblib'))
    tfidf_vectorizer = joblib.load(os.path.join(BASE_DIR, 'tfidf_vectorizer.joblib'))
    metadata = joblib.load(os.path.join(BASE_DIR, 'model_metadata.joblib'))
    structured_feature_names = metadata['structured_feature_names']
    medians = metadata['medians']
    logger.info("Artifacts loaded successfully.")
    print("Artifacts loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model artifacts: {str(e)}")
    print(f"Error loading artifacts: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    # If the user submits via a standard POST (non-AJAX fallback)
    if request.method == 'POST':
        # This will be handled by the AJAX logic usually, 
        # but we can implement a basic version here if needed.
        pass
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint to verify app and model status."""
    status = {
        'status': 'healthy',
        'model_loaded': xgb_model is not None,
        'vectorizer_loaded': tfidf_vectorizer is not None,
        'metadata_loaded': metadata is not None
    }
    if not all(status.values()):
        status['status'] = 'unhealthy'
        return jsonify(status), 500
    return jsonify(status), 200

@app.route('/predict', methods=['POST'])
def predict():
    if xgb_model is None or tfidf_vectorizer is None:
        logger.error("Model artifacts not loaded.")
        return jsonify({
            'status': 'error',
            'message': "Prediction service is currently unavailable (model not loaded)."
        }), 503

    try:
        # Get data from JSON or Fallback to Form
        if request.is_json:
            data = request.json
        else:
            data = request.form
        
        # Extract inputs with defaults
        age = float(data.get('age', medians.get('Age_Year', 50)))
        weight = float(data.get('weight', medians.get('Patient Weight_NUM', 70)))
        sex = data.get('sex', '')
        priority = data.get('priority', '')
        reactions = data.get('reactions', '')
        
        # Build structured features row matching training structure exactly
        input_dict = {col: 0.0 for col in structured_feature_names}
        
        if 'Age_Year' in input_dict:
            input_dict['Age_Year'] = age
        if 'Patient Weight_NUM' in input_dict:
            input_dict['Patient Weight_NUM'] = weight
            
        sex_col = f'Sex_{sex}'
        if sex_col in input_dict:
            input_dict[sex_col] = 1.0
            
        priority_col = f'Case Priority_{priority}'
        if priority_col in input_dict:
            input_dict[priority_col] = 1.0
            
        # Convert to sparse matrix
        X_num = pd.DataFrame([input_dict])[structured_feature_names]
        X_structured_sparse = csr_matrix(X_num.values)
        
        # Process text features
        X_text_reac = tfidf_vectorizer.transform([reactions])
        
        # Combine
        X = hstack([X_structured_sparse, X_text_reac])
        
        # Predict probability of 'Serious' (class 1)
        prob = xgb_model.predict_proba(X)[0][1].item()
        
        return jsonify({
            'status': 'success',
            'risk_score': prob,
            'risk_percentage': round(prob * 100, 2)
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"An internal error occurred: {str(e)}"
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
