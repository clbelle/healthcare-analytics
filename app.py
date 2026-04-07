from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
from scipy.sparse import csr_matrix, hstack

app = Flask(__name__)

# Load model artifacts
print("Loading model artifacts...")
xgb_model = joblib.load('xgb_triage_model.joblib')
tfidf_vectorizer = joblib.load('tfidf_vectorizer.joblib')
metadata = joblib.load('model_metadata.joblib')
structured_feature_names = metadata['structured_feature_names']
medians = metadata['medians']
print("Artifacts loaded successfully.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from JSON
        data = request.json
        
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
