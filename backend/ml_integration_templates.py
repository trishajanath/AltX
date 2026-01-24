"""
ML Model Integration Templates for Generated Applications
Provides templates for common ML models that can be integrated into applications
"""

import json
from typing import Dict, List, Any, Optional

# ============================================================================
# ML MODEL TEMPLATES - These get injected into generated applications
# ============================================================================

ML_MODEL_TEMPLATES = {
    "linear_regression": {
        "name": "Linear Regression",
        "description": "Predicts continuous values based on input features",
        "use_cases": ["price prediction", "population prediction", "sales forecasting", "demand prediction"],
        "backend_code": '''
# Linear Regression Model Implementation
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

# Pydantic models for requests/responses
class PredictionRequest(BaseModel):
    features: List[float]  # Input features for prediction
    
class PredictionResponse(BaseModel):
    prediction: float
    confidence: Optional[float] = None
    model_info: dict

class TrainingDataPoint(BaseModel):
    features: List[float]
    target: float

class TrainingRequest(BaseModel):
    data_points: List[TrainingDataPoint]
    
class ModelMetrics(BaseModel):
    r_squared: float
    mse: float
    mae: float
    coefficients: List[float]
    intercept: float

# Simple Linear Regression implementation (no sklearn dependency)
class SimpleLinearRegression:
    def __init__(self):
        self.coefficients = None
        self.intercept = None
        self.r_squared = 0.0
        self.mse = 0.0
        self.mae = 0.0
        self.is_trained = False
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train the model using normal equation"""
        # Add bias term (column of 1s)
        X_b = np.c_[np.ones((X.shape[0], 1)), X]
        
        # Normal equation: theta = (X^T * X)^(-1) * X^T * y
        try:
            theta = np.linalg.pinv(X_b.T @ X_b) @ X_b.T @ y
            self.intercept = theta[0]
            self.coefficients = theta[1:].tolist()
            
            # Calculate metrics
            predictions = self.predict(X)
            self.mse = np.mean((y - predictions) ** 2)
            self.mae = np.mean(np.abs(y - predictions))
            
            # R-squared
            ss_res = np.sum((y - predictions) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            self.r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
            
            self.is_trained = True
            return self
        except Exception as e:
            raise ValueError(f"Training failed: {str(e)}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        return X @ np.array(self.coefficients) + self.intercept
    
    def get_metrics(self) -> dict:
        return {
            "r_squared": float(self.r_squared),
            "mse": float(self.mse),
            "mae": float(self.mae),
            "coefficients": self.coefficients,
            "intercept": float(self.intercept) if self.intercept is not None else None
        }

# Global model instance
model = SimpleLinearRegression()

# Sample training data for demo (can be replaced with real data)
SAMPLE_DATA = {
    "population_prediction": {
        "features": [[2010], [2012], [2014], [2016], [2018], [2020], [2022]],
        "targets": [6.9, 7.0, 7.2, 7.4, 7.6, 7.8, 8.0]  # Billions
    },
    "price_prediction": {
        "features": [[1000], [1500], [2000], [2500], [3000], [3500], [4000]],  # sq ft
        "targets": [200000, 280000, 350000, 420000, 500000, 580000, 650000]  # price
    },
    "sales_forecasting": {
        "features": [[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]],  # months
        "targets": [120, 150, 180, 220, 250, 280, 320, 350, 300, 280, 250, 400]  # sales
    }
}

@router.post("/train", response_model=ModelMetrics)
async def train_model(request: TrainingRequest):
    """Train the linear regression model with provided data"""
    try:
        X = np.array([dp.features for dp in request.data_points])
        y = np.array([dp.target for dp in request.data_points])
        
        model.fit(X, y)
        return ModelMetrics(**model.get_metrics())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/train-demo/{use_case}")
async def train_demo_model(use_case: str):
    """Train with sample demo data for common use cases"""
    if use_case not in SAMPLE_DATA:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown use case. Available: {list(SAMPLE_DATA.keys())}"
        )
    
    data = SAMPLE_DATA[use_case]
    X = np.array(data["features"])
    y = np.array(data["targets"])
    
    model.fit(X, y)
    return {
        "message": f"Model trained for {use_case}",
        "metrics": model.get_metrics(),
        "sample_predictions": {
            "input_range": [float(X.min()), float(X.max())],
            "prediction_range": [float(y.min()), float(y.max())]
        }
    }

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make a prediction using the trained model"""
    if not model.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet. Call /train first.")
    
    try:
        X = np.array([request.features])
        prediction = model.predict(X)[0]
        
        return PredictionResponse(
            prediction=float(prediction),
            confidence=model.r_squared,
            model_info=model.get_metrics()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/metrics")
async def get_model_metrics():
    """Get current model metrics"""
    if not model.is_trained:
        return {"trained": False, "message": "Model not trained yet"}
    return {"trained": True, "metrics": model.get_metrics()}

@router.get("/sample-data/{use_case}")
async def get_sample_data(use_case: str):
    """Get sample training data for a use case"""
    if use_case not in SAMPLE_DATA:
        return {"available_use_cases": list(SAMPLE_DATA.keys())}
    return SAMPLE_DATA[use_case]
''',
        "frontend_code": '''
// ML Prediction Component - Linear Regression
const MLPredictionWidget = ({ title = "Prediction Model", useCase = "population_prediction" }) => {
  const [inputValue, setInputValue] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [modelTrained, setModelTrained] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [trainingData, setTrainingData] = useState([]);
  const [newDataPoint, setNewDataPoint] = useState({ feature: '', target: '' });
  
  const ML_API = 'http://localhost:8000/api/ml';
  
  // Train model with demo data
  const trainDemoModel = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${ML_API}/train-demo/${useCase}`, { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      setModelTrained(true);
      setMetrics(data.metrics);
      showNotification('Model trained successfully!');
    } catch (err) {
      setError(err.message);
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // Train with custom data
  const trainCustomModel = async () => {
    if (trainingData.length < 2) {
      setError('Need at least 2 data points to train');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${ML_API}/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_points: trainingData.map(d => ({
            features: [parseFloat(d.feature)],
            target: parseFloat(d.target)
          }))
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      setModelTrained(true);
      setMetrics(data);
      showNotification('Custom model trained!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Make prediction
  const makePrediction = async () => {
    if (!inputValue) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${ML_API}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ features: [parseFloat(inputValue)] })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      setPrediction(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Add training data point
  const addDataPoint = () => {
    if (newDataPoint.feature && newDataPoint.target) {
      setTrainingData([...trainingData, { ...newDataPoint }]);
      setNewDataPoint({ feature: '', target: '' });
    }
  };
  
  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <span className="text-2xl">🤖</span> {title}
      </h3>
      
      {/* Model Status */}
      <div className="mb-6">
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
          modelTrained ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
        }`}>
          <span className={`w-2 h-2 rounded-full ${modelTrained ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
          {modelTrained ? 'Model Trained' : 'Model Not Trained'}
        </div>
      </div>
      
      {/* Training Section */}
      {!modelTrained && (
        <div className="mb-6 space-y-4">
          <button
            onClick={trainDemoModel}
            disabled={loading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Training...' : `Train with Demo Data (${useCase.replace('_', ' ')})`}
          </button>
          
          <div className="border-t border-gray-700 pt-4">
            <p className="text-gray-400 text-sm mb-3">Or add custom training data:</p>
            <div className="flex gap-2 mb-2">
              <input
                type="number"
                placeholder="Feature (X)"
                value={newDataPoint.feature}
                onChange={(e) => setNewDataPoint({...newDataPoint, feature: e.target.value})}
                className="flex-1 px-3 py-2 bg-gray-800 rounded-lg text-white"
              />
              <input
                type="number"
                placeholder="Target (Y)"
                value={newDataPoint.target}
                onChange={(e) => setNewDataPoint({...newDataPoint, target: e.target.value})}
                className="flex-1 px-3 py-2 bg-gray-800 rounded-lg text-white"
              />
              <button onClick={addDataPoint} className="px-4 py-2 bg-gray-700 rounded-lg text-white hover:bg-gray-600">+</button>
            </div>
            {trainingData.length > 0 && (
              <div className="text-sm text-gray-400 mb-2">
                {trainingData.length} data points added
              </div>
            )}
            <button
              onClick={trainCustomModel}
              disabled={trainingData.length < 2 || loading}
              className="w-full py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              Train Custom Model
            </button>
          </div>
        </div>
      )}
      
      {/* Model Metrics */}
      {metrics && (
        <div className="mb-6 p-4 bg-gray-800 rounded-lg">
          <h4 className="text-white font-medium mb-2">Model Metrics</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-gray-400">R² Score:</span> <span className="text-green-400">{(metrics.r_squared * 100).toFixed(1)}%</span></div>
            <div><span className="text-gray-400">MSE:</span> <span className="text-white">{metrics.mse.toFixed(4)}</span></div>
            <div><span className="text-gray-400">MAE:</span> <span className="text-white">{metrics.mae.toFixed(4)}</span></div>
          </div>
        </div>
      )}
      
      {/* Prediction Section */}
      {modelTrained && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Enter value to predict"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="flex-1 px-4 py-3 bg-gray-800 rounded-lg text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
            />
            <button
              onClick={makePrediction}
              disabled={loading || !inputValue}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '...' : 'Predict'}
            </button>
          </div>
          
          {prediction && (
            <div className="p-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg border border-blue-500/30">
              <div className="text-gray-400 text-sm mb-1">Prediction Result</div>
              <div className="text-3xl font-bold text-white">{prediction.prediction.toLocaleString()}</div>
              <div className="text-gray-400 text-sm mt-1">
                Confidence: {(prediction.confidence * 100).toFixed(1)}%
              </div>
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};
'''
    },
    
    "classification": {
        "name": "Classification",
        "description": "Classifies data into categories",
        "use_cases": ["sentiment analysis", "spam detection", "category classification", "risk assessment"],
        "backend_code": '''
# Classification Model Implementation (K-Nearest Neighbors)
import numpy as np
from collections import Counter
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/ml/classify", tags=["Classification"])

class ClassificationRequest(BaseModel):
    features: List[float]
    k: int = 3  # Number of neighbors

class ClassificationResponse(BaseModel):
    prediction: str
    probabilities: Dict[str, float]
    confidence: float

class TrainingData(BaseModel):
    features: List[List[float]]
    labels: List[str]

# Simple KNN implementation
class SimpleKNN:
    def __init__(self, k=3):
        self.k = k
        self.X_train = None
        self.y_train = None
        self.classes = []
        
    def fit(self, X: np.ndarray, y: List[str]):
        self.X_train = X
        self.y_train = np.array(y)
        self.classes = list(set(y))
        return self
    
    def predict(self, X: np.ndarray) -> tuple:
        # Calculate distances to all training points
        distances = np.sqrt(np.sum((self.X_train - X) ** 2, axis=1))
        
        # Get k nearest neighbors
        k_indices = np.argsort(distances)[:self.k]
        k_labels = self.y_train[k_indices]
        
        # Vote for class
        vote_counts = Counter(k_labels)
        prediction = vote_counts.most_common(1)[0][0]
        
        # Calculate probabilities
        total = len(k_labels)
        probabilities = {cls: vote_counts.get(cls, 0) / total for cls in self.classes}
        confidence = max(probabilities.values())
        
        return prediction, probabilities, confidence

# Global classifier
classifier = SimpleKNN()

# Demo data for sentiment analysis
DEMO_DATA = {
    "sentiment": {
        "features": [[0.8, 0.9], [0.7, 0.8], [0.9, 0.85], [0.2, 0.1], [0.1, 0.2], [0.15, 0.15], [0.5, 0.5], [0.55, 0.45]],
        "labels": ["positive", "positive", "positive", "negative", "negative", "negative", "neutral", "neutral"]
    },
    "risk": {
        "features": [[0.9, 0.8, 0.7], [0.8, 0.85, 0.75], [0.3, 0.2, 0.4], [0.2, 0.3, 0.25], [0.5, 0.5, 0.5]],
        "labels": ["high_risk", "high_risk", "low_risk", "low_risk", "medium_risk"]
    }
}

@router.post("/train")
async def train_classifier(data: TrainingData):
    """Train the KNN classifier"""
    X = np.array(data.features)
    classifier.fit(X, data.labels)
    return {"message": "Classifier trained", "classes": classifier.classes, "samples": len(data.labels)}

@router.post("/train-demo/{use_case}")
async def train_demo(use_case: str):
    """Train with demo data"""
    if use_case not in DEMO_DATA:
        raise HTTPException(status_code=400, detail=f"Available: {list(DEMO_DATA.keys())}")
    
    data = DEMO_DATA[use_case]
    X = np.array(data["features"])
    classifier.fit(X, data["labels"])
    return {"message": f"Trained for {use_case}", "classes": classifier.classes}

@router.post("/predict", response_model=ClassificationResponse)
async def classify(request: ClassificationRequest):
    """Classify input features"""
    if classifier.X_train is None:
        raise HTTPException(status_code=400, detail="Classifier not trained")
    
    X = np.array([request.features])
    prediction, probabilities, confidence = classifier.predict(X)
    
    return ClassificationResponse(
        prediction=prediction,
        probabilities=probabilities,
        confidence=confidence
    )
''',
        "frontend_code": '''
// Classification Widget Component
const ClassificationWidget = ({ title = "AI Classifier", useCase = "sentiment" }) => {
  const [features, setFeatures] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [trained, setTrained] = useState(false);
  
  const trainModel = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/ml/classify/train-demo/${useCase}`, { method: 'POST' });
      if (res.ok) {
        setTrained(true);
        showNotification('Classifier ready!');
      }
    } catch (err) {
      showNotification('Training failed', 'error');
    }
    setLoading(false);
  };
  
  const classify = async () => {
    if (features.length === 0) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/ml/classify/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ features, k: 3 })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      showNotification('Classification failed', 'error');
    }
    setLoading(false);
  };
  
  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h3 className="text-xl font-bold text-white mb-4">🎯 {title}</h3>
      
      {!trained ? (
        <button onClick={trainModel} disabled={loading} className="w-full py-3 bg-purple-600 text-white rounded-lg">
          {loading ? 'Training...' : 'Initialize Classifier'}
        </button>
      ) : (
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Enter features (comma-separated)"
            onChange={(e) => setFeatures(e.target.value.split(',').map(Number).filter(n => !isNaN(n)))}
            className="w-full px-4 py-3 bg-gray-800 rounded-lg text-white"
          />
          <button onClick={classify} disabled={loading} className="w-full py-3 bg-purple-600 text-white rounded-lg">
            Classify
          </button>
          
          {result && (
            <div className="p-4 bg-purple-600/20 rounded-lg">
              <div className="text-2xl font-bold text-white">{result.prediction}</div>
              <div className="text-gray-400">Confidence: {(result.confidence * 100).toFixed(1)}%</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
'''
    },
    
    "time_series": {
        "name": "Time Series Forecasting",
        "description": "Predicts future values based on historical time series data",
        "use_cases": ["stock prediction", "weather forecast", "demand forecasting", "trend analysis"],
        "backend_code": '''
# Time Series Forecasting using Moving Averages and Exponential Smoothing
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/ml/timeseries", tags=["Time Series"])

class TimeSeriesData(BaseModel):
    values: List[float]
    timestamps: Optional[List[str]] = None

class ForecastRequest(BaseModel):
    values: List[float]
    steps: int = 5
    method: str = "exponential"  # "moving_average" or "exponential"
    alpha: float = 0.3  # Smoothing factor for exponential

class ForecastResponse(BaseModel):
    forecast: List[float]
    method: str
    trend: str  # "up", "down", or "stable"

def moving_average_forecast(values: List[float], steps: int, window: int = 3) -> List[float]:
    """Simple Moving Average forecast"""
    forecast = []
    data = list(values)
    
    for _ in range(steps):
        ma = np.mean(data[-window:])
        forecast.append(ma)
        data.append(ma)
    
    return forecast

def exponential_smoothing_forecast(values: List[float], steps: int, alpha: float = 0.3) -> List[float]:
    """Exponential Smoothing forecast"""
    forecast = []
    last_value = values[-1]
    last_smoothed = values[-1]
    
    # Calculate trend
    smoothed = [values[0]]
    for v in values[1:]:
        s = alpha * v + (1 - alpha) * smoothed[-1]
        smoothed.append(s)
    
    # Forecast
    for _ in range(steps):
        next_val = alpha * last_value + (1 - alpha) * last_smoothed
        forecast.append(next_val)
        last_smoothed = next_val
        last_value = next_val
    
    return forecast

def detect_trend(values: List[float]) -> str:
    """Simple trend detection"""
    if len(values) < 2:
        return "stable"
    
    first_half = np.mean(values[:len(values)//2])
    second_half = np.mean(values[len(values)//2:])
    
    diff_pct = (second_half - first_half) / first_half * 100 if first_half != 0 else 0
    
    if diff_pct > 5:
        return "up"
    elif diff_pct < -5:
        return "down"
    return "stable"

@router.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    """Generate time series forecast"""
    if len(request.values) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 data points")
    
    if request.method == "moving_average":
        predictions = moving_average_forecast(request.values, request.steps)
    else:
        predictions = exponential_smoothing_forecast(request.values, request.steps, request.alpha)
    
    trend = detect_trend(request.values)
    
    return ForecastResponse(
        forecast=[round(p, 2) for p in predictions],
        method=request.method,
        trend=trend
    )

@router.post("/analyze")
async def analyze_series(data: TimeSeriesData):
    """Analyze time series data"""
    values = data.values
    return {
        "count": len(values),
        "mean": round(np.mean(values), 2),
        "std": round(np.std(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "trend": detect_trend(values),
        "last_5": values[-5:] if len(values) >= 5 else values
    }
''',
        "frontend_code": '''
// Time Series Forecasting Widget
const TimeSeriesForecast = ({ title = "Forecast" }) => {
  const [values, setValues] = useState([100, 120, 115, 130, 125, 140, 135]);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const generateForecast = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/ml/timeseries/forecast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ values, steps: 5, method: 'exponential' })
      });
      const data = await res.json();
      setForecast(data);
    } catch (err) {
      showNotification('Forecast failed', 'error');
    }
    setLoading(false);
  };
  
  const allValues = forecast ? [...values, ...forecast.forecast] : values;
  const maxVal = Math.max(...allValues);
  
  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h3 className="text-xl font-bold text-white mb-4">📈 {title}</h3>
      
      {/* Simple Chart */}
      <div className="h-40 flex items-end gap-1 mb-4">
        {allValues.map((v, i) => (
          <div
            key={i}
            className={`flex-1 rounded-t ${i >= values.length ? 'bg-blue-500/50' : 'bg-green-500'}`}
            style={{ height: `${(v / maxVal) * 100}%` }}
            title={`${v.toFixed(1)}`}
          />
        ))}
      </div>
      
      <input
        type="text"
        placeholder="Enter values (comma-separated)"
        defaultValue={values.join(', ')}
        onChange={(e) => setValues(e.target.value.split(',').map(Number).filter(n => !isNaN(n)))}
        className="w-full px-4 py-2 bg-gray-800 rounded-lg text-white mb-4"
      />
      
      <button onClick={generateForecast} disabled={loading} className="w-full py-3 bg-green-600 text-white rounded-lg">
        {loading ? 'Forecasting...' : 'Generate Forecast'}
      </button>
      
      {forecast && (
        <div className="mt-4 p-4 bg-gray-800 rounded-lg">
          <div className="text-gray-400 text-sm">Forecast ({forecast.method})</div>
          <div className="text-white font-medium">{forecast.forecast.join(' → ')}</div>
          <div className={`text-sm mt-2 ${forecast.trend === 'up' ? 'text-green-400' : forecast.trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
            Trend: {forecast.trend === 'up' ? '📈 Upward' : forecast.trend === 'down' ? '📉 Downward' : '➡️ Stable'}
          </div>
        </div>
      )}
    </div>
  );
};
'''
    }
}


def detect_ml_requirements(idea: str, features: List[str]) -> Dict[str, Any]:
    """
    Analyze user's idea to detect ML model requirements
    
    Args:
        idea: User's project description
        features: List of requested features
        
    Returns:
        Dict with detected ML models and configurations
    """
    idea_lower = idea.lower()
    features_text = ' '.join(features).lower() if features else ''
    combined_text = f"{idea_lower} {features_text}"
    
    ml_requirements = {
        "needs_ml": False,
        "models": [],
        "use_cases": [],
        "recommendations": []
    }
    
    # Linear Regression detection
    linear_keywords = [
        "predict", "prediction", "forecast", "forecasting",
        "population", "price prediction", "sales forecast",
        "demand prediction", "regression", "trend", "estimate",
        "linear", "continuous value", "numerical prediction"
    ]
    
    if any(kw in combined_text for kw in linear_keywords):
        ml_requirements["needs_ml"] = True
        ml_requirements["models"].append("linear_regression")
        
        # Determine specific use case
        if "population" in combined_text:
            ml_requirements["use_cases"].append("population_prediction")
        elif "price" in combined_text or "cost" in combined_text:
            ml_requirements["use_cases"].append("price_prediction")
        elif "sales" in combined_text or "revenue" in combined_text:
            ml_requirements["use_cases"].append("sales_forecasting")
        else:
            ml_requirements["use_cases"].append("general_prediction")
    
    # Classification detection
    classification_keywords = [
        "classify", "classification", "categorize", "category",
        "sentiment", "spam", "risk assessment", "detect",
        "identify", "label", "positive", "negative"
    ]
    
    if any(kw in combined_text for kw in classification_keywords):
        ml_requirements["needs_ml"] = True
        ml_requirements["models"].append("classification")
        
        if "sentiment" in combined_text:
            ml_requirements["use_cases"].append("sentiment_analysis")
        elif "spam" in combined_text:
            ml_requirements["use_cases"].append("spam_detection")
        elif "risk" in combined_text:
            ml_requirements["use_cases"].append("risk_assessment")
    
    # Time Series detection
    timeseries_keywords = [
        "time series", "stock", "weather", "forecast future",
        "historical data", "trend analysis", "sequence",
        "temporal", "over time"
    ]
    
    if any(kw in combined_text for kw in timeseries_keywords):
        ml_requirements["needs_ml"] = True
        ml_requirements["models"].append("time_series")
    
    # Generate recommendations
    if ml_requirements["needs_ml"]:
        ml_requirements["recommendations"].append(
            "Your application can include built-in ML models for predictions"
        )
        if "linear_regression" in ml_requirements["models"]:
            ml_requirements["recommendations"].append(
                "Linear regression model will be included for numerical predictions"
            )
        if "classification" in ml_requirements["models"]:
            ml_requirements["recommendations"].append(
                "Classification model (KNN) will be included for categorization"
            )
        if "time_series" in ml_requirements["models"]:
            ml_requirements["recommendations"].append(
                "Time series forecasting will be included for trend analysis"
            )
    
    return ml_requirements


def detect_llm_requirements(idea: str, features: List[str]) -> Dict[str, Any]:
    """
    Detect if the user wants LLM integration and return guidance
    
    Args:
        idea: User's project description
        features: List of requested features
        
    Returns:
        Dict with LLM requirements and API key guidance
    """
    idea_lower = idea.lower()
    features_text = ' '.join(features).lower() if features else ''
    combined_text = f"{idea_lower} {features_text}"
    
    llm_requirements = {
        "needs_llm": False,
        "llm_type": None,
        "requires_api_key": True,
        "api_key_instructions": None,
        "providers": []
    }
    
    # OpenAI/GPT detection
    openai_keywords = [
        "chatgpt", "gpt", "openai", "chatbot", "ai chat",
        "ai assistant", "conversational ai", "natural language",
        "text generation", "ai response", "smart assistant"
    ]
    
    if any(kw in combined_text for kw in openai_keywords):
        llm_requirements["needs_llm"] = True
        llm_requirements["providers"].append({
            "name": "OpenAI (GPT)",
            "api_key_env": "OPENAI_API_KEY",
            "signup_url": "https://platform.openai.com/signup",
            "docs_url": "https://platform.openai.com/docs/api-reference",
            "instructions": """
To use OpenAI GPT in your application:
1. Sign up at https://platform.openai.com/signup
2. Go to https://platform.openai.com/api-keys
3. Click "Create new secret key"
4. Copy the key and add to your .env file:
   OPENAI_API_KEY=sk-your-key-here
5. The app will automatically use this key for AI responses
            """
        })
    
    # Google Gemini detection
    gemini_keywords = [
        "gemini", "google ai", "bard", "palm"
    ]
    
    if any(kw in combined_text for kw in gemini_keywords):
        llm_requirements["needs_llm"] = True
        llm_requirements["providers"].append({
            "name": "Google Gemini",
            "api_key_env": "GOOGLE_API_KEY",
            "signup_url": "https://makersuite.google.com/app/apikey",
            "docs_url": "https://ai.google.dev/docs",
            "instructions": """
To use Google Gemini in your application:
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add to your .env file:
   GOOGLE_API_KEY=your-key-here
5. The app will use Gemini for AI features
            """
        })
    
    # Anthropic Claude detection
    claude_keywords = [
        "claude", "anthropic"
    ]
    
    if any(kw in combined_text for kw in claude_keywords):
        llm_requirements["needs_llm"] = True
        llm_requirements["providers"].append({
            "name": "Anthropic Claude",
            "api_key_env": "ANTHROPIC_API_KEY",
            "signup_url": "https://console.anthropic.com/",
            "docs_url": "https://docs.anthropic.com/",
            "instructions": """
To use Anthropic Claude in your application:
1. Sign up at https://console.anthropic.com/
2. Navigate to API Keys section
3. Generate a new API key
4. Add to your .env file:
   ANTHROPIC_API_KEY=sk-ant-your-key-here
5. The app will use Claude for AI features
            """
        })
    
    # Generic AI detection (recommend OpenAI as default)
    generic_ai_keywords = [
        "ai", "artificial intelligence", "machine learning chat",
        "intelligent", "smart chat", "ai-powered"
    ]
    
    if any(kw in combined_text for kw in generic_ai_keywords) and not llm_requirements["needs_llm"]:
        llm_requirements["needs_llm"] = True
        llm_requirements["providers"].append({
            "name": "OpenAI (Recommended)",
            "api_key_env": "OPENAI_API_KEY",
            "signup_url": "https://platform.openai.com/signup",
            "docs_url": "https://platform.openai.com/docs/api-reference",
            "instructions": """
To add AI capabilities to your application:
1. Sign up at https://platform.openai.com/signup
2. Get your API key from https://platform.openai.com/api-keys
3. Add to your .env file:
   OPENAI_API_KEY=sk-your-key-here
4. Restart the application to enable AI features
            """
        })
    
    # Build combined instructions if LLM is needed
    if llm_requirements["needs_llm"]:
        instructions = ["🤖 LLM INTEGRATION REQUIRED", "=" * 50, ""]
        instructions.append("Your application requires an AI/LLM API key.")
        instructions.append("Please set up one of the following providers:\n")
        
        for provider in llm_requirements["providers"]:
            instructions.append(f"📌 {provider['name']}")
            instructions.append(provider["instructions"])
            instructions.append("")
        
        instructions.append("=" * 50)
        llm_requirements["api_key_instructions"] = "\n".join(instructions)
    
    return llm_requirements


def get_ml_backend_code(model_types: List[str]) -> str:
    """
    Generate combined backend code for requested ML models
    
    Args:
        model_types: List of model types to include
        
    Returns:
        Combined Python backend code
    """
    code_parts = [
        "# ============================================================",
        "# Machine Learning Models - Auto-generated",
        "# ============================================================",
        ""
    ]
    
    for model_type in model_types:
        if model_type in ML_MODEL_TEMPLATES:
            template = ML_MODEL_TEMPLATES[model_type]
            code_parts.append(f"# --- {template['name']} ---")
            code_parts.append(template["backend_code"])
            code_parts.append("")
    
    return "\n".join(code_parts)


def get_ml_frontend_code(model_types: List[str]) -> str:
    """
    Generate combined frontend component code for ML models
    
    Args:
        model_types: List of model types to include
        
    Returns:
        Combined React component code
    """
    code_parts = [
        "// ============================================================",
        "// Machine Learning Components - Auto-generated", 
        "// ============================================================",
        ""
    ]
    
    for model_type in model_types:
        if model_type in ML_MODEL_TEMPLATES:
            template = ML_MODEL_TEMPLATES[model_type]
            code_parts.append(f"// --- {template['name']} Component ---")
            code_parts.append(template["frontend_code"])
            code_parts.append("")
    
    return "\n".join(code_parts)


def generate_ml_integration_guide(ml_requirements: Dict, llm_requirements: Dict) -> str:
    """
    Generate a guide for the user about ML/LLM integration
    
    Args:
        ml_requirements: Output from detect_ml_requirements
        llm_requirements: Output from detect_llm_requirements
        
    Returns:
        Markdown formatted guide
    """
    guide = ["# AI/ML Integration Guide\n"]
    
    if ml_requirements.get("needs_ml"):
        guide.append("## 🤖 Machine Learning Models\n")
        guide.append("Your application includes the following ML capabilities:\n")
        
        for model in ml_requirements.get("models", []):
            if model in ML_MODEL_TEMPLATES:
                template = ML_MODEL_TEMPLATES[model]
                guide.append(f"### {template['name']}")
                guide.append(f"**Description:** {template['description']}")
                guide.append(f"**Use Cases:** {', '.join(template['use_cases'])}")
                guide.append("")
        
        guide.append("### API Endpoints")
        guide.append("```")
        guide.append("POST /api/ml/train          - Train the model")
        guide.append("POST /api/ml/train-demo/{type} - Train with demo data")
        guide.append("POST /api/ml/predict        - Make predictions")
        guide.append("GET  /api/ml/metrics        - Get model metrics")
        guide.append("```\n")
    
    if llm_requirements.get("needs_llm"):
        guide.append("## 🧠 LLM Integration\n")
        guide.append(llm_requirements.get("api_key_instructions", ""))
    
    return "\n".join(guide)
