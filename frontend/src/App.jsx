import React, { useState } from 'react';

function App() {
  const [url, setUrl] = useState('');
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');

  const scan = async () => {
    setReport(null);
    setError('');
    try {
      const res = await fetch('http://127.0.0.1:8000/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (data.error) setError(data.error);
      else setReport(data);
    } catch (e) {
      setError('Could not connect to server.');
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Security Header Scanner</h1>
      <input
        type="text"
        placeholder="https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: '300px', marginRight: '10px' }}
      />
      <button onClick={scan}>Scan</button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {report && (
        <div style={{ marginTop: '1rem' }}>
          <h3>Scan Result</h3>
          <p><strong>HTTPS:</strong> {report.https ? '✅ Yes' : '❌ No'}</p>
          <h4>Headers</h4>
          <ul>
            {Object.entries(report.headers).map(([key, value]) => (
              <li key={key}>
                <strong>{key}:</strong> {value}
              </li>
            ))}
          </ul>
          <h4>Suggestions</h4>
          <ul>
            {report.suggestions.map((msg, i) => (
              <li key={i}>⚠ {msg}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
