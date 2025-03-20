import pandas as pd
import pickle
import sys, os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb


def train_model(cleaned_data, model_output):
    
    df = pd.read_csv(cleaned_data)
    df = df.dropna(subset=['decision_date', 'date_received'])

    df['Date of Final Decision'] = pd.to_datetime(df['decision_date'])
    df['date_received'] = pd.to_datetime(df['date_received'])
    df['days_to_decision'] = (df['Date of Final Decision'] - df['date_received']).dt.days
    
    df[['Panel (lead)', 'Primary Product Code', 'state', 'decision_code']].fillna('Unknown', inplace=True)

    features = ['Panel (lead)', 'Primary Product Code', 'state', 'decision_code']
    X = df[features]
    y = df['days_to_decision']
    print([X,y])

    encoder = OneHotEncoder(handle_unknown='ignore', sparse=False)
    X_encoded = encoder.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)
    
    param_grid = {
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7],
    'subsample': [0.8, 1.0],
    'colsample_bytree': [0.8, 1.0]
    }

    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)

    # Set up GridSearchCV
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        scoring='neg_mean_squared_error', 
        cv=5,
        n_jobs=-1 
    )

    # Perform grid search
    grid_search.fit(X_train, y_train)

    # Print the best parameters and best score
    print("Best Parameters:", grid_search.best_params_)
    print("Best Score (Negative MSE):", grid_search.best_score_)

    # Use the best model for predictions
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)

    # Evaluate the best model
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Mean Absolute Error (MAE): {mae}")
    print(f"Mean Squared Error (MSE): {mse}")
    print(f"R-squared (R²): {r2}")

if __name__ == "__main__":
    
    train_model('data/output/aiml_info.csv', 'models/trained_model.pkl')
