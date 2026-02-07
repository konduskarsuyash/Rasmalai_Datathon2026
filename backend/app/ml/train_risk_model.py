"""
ML Model Training Script
Trains XGBoost classifier on collected simulation data to predict default risk
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from typing import Optional, Tuple, Dict
import json

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        classification_report, confusion_matrix, roc_auc_score,
        precision_recall_curve, roc_curve
    )
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn and xgboost not installed")
    print("Install with: pip install scikit-learn xgboost")


class RiskModelTrainer:
    """
    Trains ML models for credit risk prediction
    """
    
    def __init__(self, data_path: str):
        """
        Initialize trainer with training data
        
        Args:
            data_path: Path to CSV file with training data
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn and xgboost required for training")
        
        self.data_path = Path(data_path)
        self.df = None
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.metrics = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load training data from CSV"""
        print(f"📊 Loading data from {self.data_path}")
        
        self.df = pd.read_csv(self.data_path)
        
        print(f"✓ Loaded {len(self.df)} decision points")
        print(f"  Columns: {len(self.df.columns)}")
        print(f"  Memory: {self.df.memory_usage().sum() / 1024**2:.2f} MB")
        
        # Show class distribution
        if 'borrower_defaulted_t10' in self.df.columns:
            defaults = self.df['borrower_defaulted_t10'].sum()
            print(f"  Defaults (t+10): {defaults} ({defaults/len(self.df)*100:.1f}%)")
        
        return self.df
    
    def prepare_features(self, target_column: str = 'borrower_defaulted_t10') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare feature matrix and target vector
        
        Args:
            target_column: Column to use as target (borrower_defaulted_t5 or borrower_defaulted_t10)
            
        Returns:
            (X, y) feature matrix and target vector
        """
        if self.df is None:
            self.load_data()
        
        # Filter rows with valid target
        df_clean = self.df[self.df[target_column].notna()].copy()
        print(f"✓ Using {len(df_clean)} rows with valid target")
        
        # Select feature columns
        feature_cols = [
            # Borrower financial (8 features)
            'borrower_capital_ratio',
            'borrower_leverage',
            'borrower_liquidity_ratio',
            'borrower_equity',
            'borrower_cash',
            'borrower_market_exposure',
            'borrower_past_defaults',
            'borrower_risk_appetite',
            
            # Network position (5 features)
            'borrower_centrality',
            'borrower_degree',
            'borrower_upstream_exposure',
            'borrower_downstream_exposure',
            'borrower_clustering',
            
            # Market conditions (3 features)
            'market_stress',
            'market_volatility',
            'market_liquidity',
            
            # Lender context (3 features)
            'lender_capital_ratio',
            'lender_equity',
            'exposure_ratio',
        ]
        
        # Filter to available columns
        available_cols = [col for col in feature_cols if col in df_clean.columns]
        self.feature_names = available_cols
        
        print(f"✓ Using {len(available_cols)} features")
        
        # Extract features and target
        X = df_clean[available_cols].values
        y = df_clean[target_column].values.astype(int)
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"✓ Target distribution: {np.bincount(y)}")
        
        return X, y
    
    def train_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> xgb.XGBClassifier:
        """
        Train XGBoost classifier
        
        Args:
            X: Feature matrix
            y: Target vector
            test_size: Fraction of data for testing
            random_state: Random seed
            
        Returns:
            Trained model
        """
        print("\n🤖 Training XGBoost model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"  Train set: {len(X_train)} samples")
        print(f"  Test set: {len(X_test)} samples")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model with class balancing
        scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
        
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            eval_metric='logloss'
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        print("✓ Model trained")
        
        # Evaluate
        self._evaluate_model(X_train_scaled, X_test_scaled, y_train, y_test)
        
        return self.model
    
    def _evaluate_model(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray
    ):
        """Evaluate model performance"""
        print("\n📊 Model Evaluation:")
        
        # Predictions
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)
        
        y_train_proba = self.model.predict_proba(X_train)[:, 1]
        y_test_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Accuracy
        train_acc = (y_train_pred == y_train).mean()
        test_acc = (y_test_pred == y_test).mean()
        
        print(f"  Train Accuracy: {train_acc:.3f}")
        print(f"  Test Accuracy:  {test_acc:.3f}")
        
        # AUC-ROC
        if len(np.unique(y_train)) == 2:
            train_auc = roc_auc_score(y_train, y_train_proba)
            test_auc = roc_auc_score(y_test, y_test_proba)
            
            print(f"  Train AUC-ROC: {train_auc:.3f}")
            print(f"  Test AUC-ROC:  {test_auc:.3f}")
            
            self.metrics['test_auc'] = test_auc
        
        # Classification report
        print("\n  Test Set Classification Report:")
        print(classification_report(y_test, y_test_pred, target_names=['No Default', 'Default']))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_test_pred)
        print("\n  Confusion Matrix:")
        print(f"    TN: {cm[0,0]}  FP: {cm[0,1]}")
        print(f"    FN: {cm[1,0]}  TP: {cm[1,1]}")
        
        # Feature importance
        print("\n  Top 10 Important Features:")
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]
        
        for i, idx in enumerate(indices):
            print(f"    {i+1}. {self.feature_names[idx]}: {importances[idx]:.4f}")
        
        # Store metrics
        self.metrics.update({
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'confusion_matrix': cm.tolist(),
            'feature_importances': dict(zip(self.feature_names, importances.tolist()))
        })
    
    def save_model(self, output_path: str = "models/risk_model.pkl"):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'metrics': self.metrics
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n✓ Model saved to {output_path}")
        
        # Save metrics as JSON
        metrics_path = output_path.parent / f"{output_path.stem}_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"✓ Metrics saved to {metrics_path}")
        
        return output_path
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict:
        """Perform cross-validation"""
        print(f"\n🔁 Performing {cv}-fold cross-validation...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Cross-validate
        scores = cross_val_score(self.model, X_scaled, y, cv=cv, scoring='roc_auc')
        
        print(f"  AUC-ROC scores: {scores}")
        print(f"  Mean: {scores.mean():.3f} (+/- {scores.std() * 2:.3f})")
        
        return {
            'scores': scores.tolist(),
            'mean': scores.mean(),
            'std': scores.std()
        }


def train_from_csv(
    data_path: str,
    output_model_path: str = "models/risk_model.pkl",
    target_column: str = 'borrower_defaulted_t10',
    test_size: float = 0.2
) -> Path:
    """
    Complete training pipeline from CSV to saved model
    
    Args:
        data_path: Path to training data CSV
        output_model_path: Path to save trained model
        target_column: Target column to predict
        test_size: Test set fraction
        
    Returns:
        Path to saved model
    """
    if not SKLEARN_AVAILABLE:
        print("❌ Cannot train: scikit-learn and xgboost not installed")
        print("Install with: pip install scikit-learn xgboost")
        return None
    
    print("=" * 60)
    print("🎯 CREDIT RISK MODEL TRAINING")
    print("=" * 60)
    
    # Initialize trainer
    trainer = RiskModelTrainer(data_path)
    
    # Load and prepare data
    trainer.load_data()
    X, y = trainer.prepare_features(target_column=target_column)
    
    # Train model
    trainer.train_model(X, y, test_size=test_size)
    
    # Save model
    model_path = trainer.save_model(output_model_path)
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE")
    print("=" * 60)
    print(f"Model ready at: {model_path}")
    print(f"Test AUC-ROC: {trainer.metrics.get('test_auc', 'N/A'):.3f}")
    print("\nTo use in simulation:")
    print("  from app.ml.risk_models import MLRiskPredictor")
    print(f"  predictor = MLRiskPredictor('{model_path}')")
    
    return model_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python train_risk_model.py <data_csv_path> [output_model_path]")
        print("\nExample:")
        print("  python train_risk_model.py training_data/training_data_20260208.csv")
        sys.exit(1)
    
    data_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "models/risk_model.pkl"
    
    train_from_csv(data_path, output_path)
