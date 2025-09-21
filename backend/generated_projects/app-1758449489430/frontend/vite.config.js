import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // A mock API server for development
    proxy: {
      '/api': {
        target: 'http://localhost:3000', // This doesn't need to exist
        changeOrigin: true,
        configure: (proxy, options) => {
          // Mock API responses
          const mockEvents = [
            { id: 1, title: 'Engineering Career Fair', date: '2024-10-25T10:00:00', location: 'Grand Hall', department: 'College of Engineering', category: 'Academic', description: 'Meet top engineering firms and explore internship opportunities.' },
            { id: 2, title: 'Homecoming Football Game', date: '2024-10-26T14:00:00', location: 'University Stadium', department: 'Athletics', category: 'Sports', description: 'Cheer on the University Lions against their biggest rivals!' },
            { id: 3, title: 'Fall Semester Concert', date: '2024-11-05T19:30:00', location: 'Campus Green', department: 'Student Life', category: 'Social', description: 'Live music from student bands and local artists.' },
            { id: 4, title: 'AI & Machine Learning Workshop', date: '2024-11-12T13:00:00', location: 'CS Building, Room 301', department: 'Computer Science', category: 'Workshop', description: 'A hands-on workshop covering the fundamentals of AI.' },
            { id: 5, title: 'Art History Guest Lecture', date: '2024-11-18T16:00:00', location: 'Fine Arts Auditorium', department: 'Arts & Humanities', category: 'Academic', description: 'Guest lecture by Dr. Eleanor Vance on Renaissance art.' }
          ];
          let nextId = 6;

          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.method === 'GET' && req.url === '/api/data') {
              res.statusCode = 200;
              res.setHeader('Content-Type', 'application/json');
              setTimeout(() => { // Simulate network delay
                res.end(JSON.stringify(mockEvents));
              }, 800);
            }

            if (req.method === 'POST' && req.url === '/api/create') {
              let body = '';
              req.on('data', chunk => {
                body += chunk.toString();
              });
              req.on('end', () => {
                try {
                  const newEvent = JSON.parse(body);
                  if (!newEvent.title || !newEvent.date || !newEvent.location) {
                      res.statusCode = 400;
                      res.setHeader('Content-Type', 'application/json');
                      res.end(JSON.stringify({ message: 'Missing required fields.' }));
                      return;
                  }
                  newEvent.id = nextId++;
                  mockEvents.push(newEvent);

                  res.statusCode = 201;
                  res.setHeader('Content-Type', 'application/json');
                  setTimeout(() => { // Simulate network delay
                    res.end(JSON.stringify(newEvent));
                  }, 1200);

                } catch (e) {
                   res.statusCode = 500;
                   res.setHeader('Content-Type', 'application/json');
                   res.end(JSON.stringify({ message: 'Server error parsing request.' }));
                }
              });
            }
          });
        }
      }
    }
  }
})