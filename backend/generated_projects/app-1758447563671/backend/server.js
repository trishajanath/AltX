const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8001;

// Middleware
app.use(helmet());
app.use(cors({
    origin: ['http://localhost:3000', 'http://localhost:3001'],
    credentials: true
}));
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
    res.json({
        message: 'Welcome to app-1758447563671 API',
        description: 'build a college timetable manage website
',
        version: '1.0.0'
    });
});

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        message: 'API is running successfully',
        timestamp: new Date().toISOString()
    });
});

// API Routes
app.get('/api/items', (req, res) => {
    // Mock data - replace with database queries
    res.json([
        {
            id: 1,
            name: 'Sample Item',
            description: 'This is a sample item',
            createdAt: new Date().toISOString()
        }
    ]);
});

app.post('/api/items', (req, res) => {
    const { name, description } = req.body;
    
    // Mock creation - replace with database insert
    res.status(201).json({
        id: Date.now(),
        name,
        description,
        createdAt: new Date().toISOString()
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        error: 'Something went wrong!',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Route not found'
    });
});

app.listen(PORT, () => {
    console.log(`🚀 app-1758447563671 API running on port ${PORT}`);
});