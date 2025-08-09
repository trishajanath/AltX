from fastapi import APIRouter, UploadFile, File, HTTPException,Form
import os
import base64
import io
import json
import numpy as np
from PIL import Image
from mainmodel1 import predict_subtype_with_heatmap
from pydantic import BaseModel
from model2 import predict_stage, predict_treatment

router = APIRouter()


    
# Configure directories
UPLOAD_DIR = "uploads"
REPORTS_FILE = "reports.json"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Ensure reports.json exists
if not os.path.exists(REPORTS_FILE):
    with open(REPORTS_FILE, "w") as f:
        json.dump({"reports": []}, f)  # Initialize empty reports list


    
@router.post("/upload")
async def upload_and_predict(
    file: UploadFile = File(...),
    patientName: str = Form(...),
    sn: str = Form(...),
    gender: str = Form(...),
    year: int = Form(...),
    age: int = Form(...),
    tumorSize: float = Form(...),
    invNodes: float = Form(...),
    breastCancerCell: int = Form(...),
    menopause: int = Form(...),
    metastasis: int = Form(...),
    breastQuadrant: int = Form(...),
    history: int = Form(...)
):
    try:
        # Save the uploaded file
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Get prediction and heatmap
        predicted_subtype, confidence, heatmap = predict_subtype_with_heatmap(file_path)

        # Predict cancer stage
        predicted_stage = predict_stage(sn, year, age, tumorSize, invNodes, breastCancerCell, menopause, metastasis, breastQuadrant, history)

        # Predict treatment
        treatment = predict_treatment(predicted_stage)

        # Encode original image
        with open(file_path, "rb") as image_file:
            original_image_str = base64.b64encode(image_file.read()).decode()

        # Normalize heatmap and convert to base64
        heatmap = np.uint8(255 * heatmap)
        heatmap = Image.fromarray(heatmap)
        buffered = io.BytesIO()
        heatmap.save(buffered, format="PNG")
        heatmap_str = base64.b64encode(buffered.getvalue()).decode()

        # Create report data with patient details
        report_data = {
            "filename": file.filename,
            "patientName": patientName,
            "sn": sn,
            "gender": gender,
            "year": year,
            "age": age,
            "tumor_size": tumorSize,
            "inv_nodes": invNodes,
            "breast_cancer_cell": breastCancerCell,
            "menopause": menopause,
            "metastasis": metastasis,
            "breast_quadrant": breastQuadrant,
            "history": history,
            "predicted_stage": predicted_stage,
            "recommended_treatment": treatment,
            "predicted_subtype": predicted_subtype,
            "confidence": f"{confidence:.2f}%",
            "heatmap": f"data:image/png;base64,{heatmap_str}",
            "original_image": f"data:image/png;base64,{original_image_str}"
        }

        # Append to reports.json
        if not os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, "w") as report_file:
                json.dump({"reports": []}, report_file)

        with open(REPORTS_FILE, "r+") as report_file:
            data = json.load(report_file)
            data["reports"].append(report_data)
            report_file.seek(0)  # Move to beginning of file
            json.dump(data, report_file, indent=4)

        return report_data

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports")
async def get_reports():
    try:
        with open(REPORTS_FILE, "r") as report_file:
            data = json.load(report_file)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/reports/{filename}")
async def delete_report(filename: str):
    try:
        # Read existing reports
        with open(REPORTS_FILE, "r") as report_file:
            data = json.load(report_file)

        # Filter out the report to delete
        new_reports = [report for report in data["reports"] if report["filename"] != filename]

        # Update the reports file
        with open(REPORTS_FILE, "w") as report_file:
            json.dump({"reports": new_reports}, report_file, indent=4)

        # Delete uploaded image file
        image_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(image_path):
            os.remove(image_path)

        return {"message": "Report deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
