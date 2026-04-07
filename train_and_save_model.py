import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix, hstack
from xgboost import XGBClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Loading dataset...")
df = pd.read_excel("all02072026_belle02152026.xlsx")
print(f"Dataset loaded. Shape: {df.shape}")

print("Processing numerical and categorical columns...")
numeric_cols = ['Age_Year', 'Patient Weight_NUM']
X_num = df[numeric_cols].copy()
medians = {}
for c in numeric_cols:
    X_num[c] = pd.to_numeric(X_num[c], errors='coerce')
    medians[c] = X_num[c].median()
    X_num[c] = X_num[c].fillna(medians[c])

cat_cols = ['Sex', 'Case Priority']
X_cat = df[cat_cols].copy()
X_cat = pd.get_dummies(X_cat, drop_first=True).astype(float)
X_cat = X_cat.fillna(0)

X_structured = pd.concat([X_num, X_cat], axis=1)
X_structured_sparse = csr_matrix(X_structured.values)
structured_feature_names = X_structured.columns.tolist()

print("Processing text features with TF-IDF...")
df['Reactions'] = df['Reactions'].fillna('')
tfidf_reactions = TfidfVectorizer(max_features=500)
X_text_reac = tfidf_reactions.fit_transform(df['Reactions'])

X = hstack([X_structured_sparse, X_text_reac])
y = df['Serious'].astype('category').cat.codes

print("Training XGBoost model...")
xgb_model = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
xgb_model.fit(X, y) # Training on full dataset since it's going into production

print("Saving artifacts...")
# Save the model
joblib.dump(xgb_model, 'xgb_triage_model.joblib')

# Save the vectorizer
joblib.dump(tfidf_reactions, 'tfidf_vectorizer.joblib')

# Save the expected structured columns and medians for deployment
metadata = {
    'structured_feature_names': structured_feature_names,
    'medians': medians,
}
joblib.dump(metadata, 'model_metadata.joblib')

print("Successfully saved all model artifacts!")
