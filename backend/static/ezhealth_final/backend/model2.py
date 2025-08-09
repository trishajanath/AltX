from pydantic import BaseModel
import joblib
import pandas as pd

model_filename = '/Users/trishajanath/PredictModel/breast_cancer_rf_model.pkl'
model = joblib.load(model_filename)
# Define input data model using Pydantic
class PatientInput(BaseModel):
    sn: str
    year: int
    age: int
    tumor_size: float
    inv_nodes: float
    breast_cancer_cell: int
    menopause: int
    metastasis: int
    breast_quadrant: int
    history: int



# Function to predict cancer stage
def predict_stage(sn, year, age, tumor_size, inv_nodes, breast_cancer_cell, menopause, metastasis, breast_quadrant, history):
    input_data = pd.DataFrame({
        'S/N': [sn],
        'Year': [year],
        'Age': [age],
        'Tumor Size (cm)': [tumor_size],
        'Inv-Nodes': [inv_nodes],
        'Breast': [breast_cancer_cell],
        'Menopause': [menopause],
        'Metastasis': [metastasis],
        'Breast Quadrant': [breast_quadrant],
        'History': [history]
    })
    
    expected_columns = model.feature_names_in_
    input_data = input_data.reindex(columns=expected_columns)

    # Predict the stage
    predicted_stage = model.predict(input_data)[0]
    
    # Convert numpy int64 to native Python int
    return int(predicted_stage)

# Function to recommend treatment based on predicted stage
def predict_treatment(predicted_stage):
    treatments = {
        0: "Observation or Hormone Therapy",
        1: "Surgery + Radiation Therapy",
        2: "Surgery + Chemotherapy + Radiation",
        3: "Targeted Therapy + Immunotherapy",
        4: "Palliative Care + Clinical Trials"
    }
    return treatments.get(predicted_stage, "No treatment available for this stage")