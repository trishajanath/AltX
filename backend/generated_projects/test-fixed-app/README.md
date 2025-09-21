# test-fixed-app

build a simple todo app with add, delete, and mark complete features

## Tech Stack

React, FastAPI, Vite, TailwindCSS

## Getting Started

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend, if using FastAPI)
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd test-fixed-app
```

2. Install frontend dependencies
```bash
cd frontend
npm install
```

3. Install backend dependencies
```bash
cd ../backend
pip install -r requirements.txt
```

### Running the Application

1. Start the backend server
```bash
cd backend
python main.py
```

2. Start the frontend development server
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

## Project Structure

```
test-fixed-app/
├── frontend/          # React frontend application
├── backend/           # FastAPI backend API
├── README.md
└── .gitignore
```

## Features

- Modern responsive design
- RESTful API
- Real-time updates
- Error handling
- Development tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
