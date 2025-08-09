# EzHealth

## Project Description

EzHealth is a specialized healthcare application designed to assist oncologists and radiologists in detecting and analyzing breast cancer through advanced medical imaging. The platform leverages machine learning algorithms to provide precise image segmentation, cancer subtype classification, and staging analysis.

## Problem Addressed

Breast cancer remains one of the most common cancers worldwide, with early detection being crucial for successful treatment outcomes. Traditional diagnostic processes can be time-consuming and subject to human interpretation variability. EzHealth addresses these challenges by providing clinicians with powerful AI-assisted tools for analyzing cells with greater speed, consistency, and accuracy.

## Solution

EzHealth provides a comprehensive platform where healthcare professionals can upload breast imaging scans and receive detailed AI-powered analysis, including:

- Precise segmentation of suspicious tissue regions
- Classification of cancer subtypes based on imaging characteristics
- Staging recommendations based on detected features
- Integration with patient health records for contextual diagnosis
- Secure storage and retrieval of historical imaging data

The application employs advanced deep learning models specifically trained on diverse breast cancer imaging datasets to ensure high accuracy across different patient demographics and imaging equipment.

## Impact

EzHealth aims to transform breast cancer diagnosis and treatment planning through:

- **Enhanced Detection Precision**: The AI-powered image analysis can identify subtle patterns and anomalies that might be overlooked in standard screening, potentially increasing early detection rates by 15-25%.

- **Critical Image Segmentation**: The platform's segmentation capabilities are invaluable for treatment planning, enabling clinicians to precisely map tumor boundaries, and distinguish between tissue types. This precision allows for optimized surgical procedures and effective treatment protocols.

- **Accelerated Diagnostic Timeline**: By automating initial image analysis, EzHealth can reduce the time between screening and diagnosis, enabling faster clinical decision-making and treatment initiation when time is critical.

- **Standardized Assessment**: The AI system provides consistent analysis parameters regardless of operator, time of day, or facility location, helping standardize care quality across different healthcare settings.

- **Reduced False Positives/Negatives**: Machine learning algorithms continually improve through feedback, potentially reducing unnecessary biopsies and missed diagnoses.


Through these capabilities, EzHealth aims to contribute to improved survival rates, reduced treatment costs, enhanced quality of life for patients, and more efficient utilization of healthcare resources.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js and npm
- MongoDB Atlas account

### Backend Setup

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/DrNeel11/ezhealth_final.git
   cd ezhealth_final/backend
   ```

2. **Create a Virtual Environment and Install Dependencies**:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file and add the required configurations, such as database connection strings.

4. **Run the Backend Server**:
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to the Frontend Directory**:
   ```sh
   cd ../frontend
   ```

2. **Install Dependencies**:
   ```sh
   npm install
   ```

3. **Start the Development Server**:
   ```sh
   npm start
   ```

## Features

- **Secure Authentication**: Role-based access for healthcare professionals.
- **Medical Image Upload**: Support for DICOM, JPEG, PNG, and other medical imaging formats.
- **Advanced Image Segmentation**: AI-powered delineation of tumor boundaries and tissue types.
- **Cancer Classification Model**: Deep learning algorithms to identify breast cancer subtypes.
- **Patient Records Management**: Comprehensive tracking of imaging history and diagnostic reports.


## Technologies Used

### Backend:
- FastAPI
- MongoDB
- Python
- TensorFlow/PyTorch
- OpenCV for image processing

### Frontend:
- React.js
- Tailwind CSS


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 EzHealth Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
