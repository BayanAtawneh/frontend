import React, { useState } from 'react';
import axios from 'axios';

const SQLQueryGenerator = () => {
  const [question, setQuestion] = useState('');
  const [sqlQuery, setSqlQuery] = useState('');
  const [resultTable, setResultTable] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
  };

  const handleGenerateSQL = async () => {
    if (!question) {
      alert('Please enter a question!');
      return;
    }

    setLoading(true);
    setError('');
    setSqlQuery('');
    setResultTable([]);
    setColumns([]);

    try {
      const response = await axios.post('http://localhost:8000/generate-sql', {
        question,
      });

      if (response.data.error) {
        setError(response.data.error);
      } else {
        setSqlQuery(response.data.sql || '');

        if (response.data.columns && response.data.rows) {
          setColumns(response.data.columns);
          setResultTable(response.data.rows);
        }
      }
    } catch (err) {
      setError('An error occurred while generating or executing the SQL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sql-query-generator">
      <h1>SQL Query Generator</h1>
      <div>
        <textarea
          rows="4"
          cols="60"
          placeholder="Enter your question..."
          value={question}
          onChange={handleQuestionChange}
        />
      </div>
      <div>
        <button onClick={handleGenerateSQL} disabled={loading}>
          {loading ? 'Generating...' : 'Generate SQL'}
        </button>
      </div>

      {sqlQuery && (
        <div>
          <h2>Generated SQL Query:</h2>
          <pre style={{ background: '#f4f4f4', padding: '1em' }}>{sqlQuery}</pre>
        </div>
      )}

      {columns.length > 0 && resultTable.length > 0 && (
        <div>
          <h2>Query Result:</h2>
          <table border="1" cellPadding="5" cellSpacing="0">
            <thead>
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {resultTable.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {error && <div style={{ color: 'red', marginTop: '1em' }}>{error}</div>}
    </div>
  );
};

export default SQLQueryGenerator;
