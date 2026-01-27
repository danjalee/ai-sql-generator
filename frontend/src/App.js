import React, { useState } from "react";

function App() {
  const [language, setLanguage] = useState("en");
  const [database, setDatabase] = useState("mysql");
  const [sqlMode, setSqlMode] = useState("read");
  const [schema, setSchema] = useState("");
  const [criteria, setCriteria] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateSQL = async () => {
    setLoading(true);
    setError("");
    setResult("");

    try {
      const response = await fetch(
        "https://ai-sql-generator-backend.onrender.com/generate-sql",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": process.env.REACT_APP_SECRET_KEY
          },
          body: JSON.stringify({
            language,
            database,
            sqlMode,
            schema_ddl: schema,
            criteria
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to generate SQL");
      }

      setResult(data.sql);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>AI SQL Generator</h2>

      <select value={language} onChange={e => setLanguage(e.target.value)}>
        <option value="en">English</option>
        <option value="ja">Japanese</option>
      </select>

      <select value={database} onChange={e => setDatabase(e.target.value)}>
        <option value="mysql">MySQL</option>
        <option value="postgresql">PostgreSQL</option>
        <option value="sqlserver">SQL Server</option>
        <option value="sqlite">SQLite</option>
      </select>

      <select value={sqlMode} onChange={e => setSqlMode(e.target.value)}>
        <option value="read">SELECT (Read)</option>
        <option value="write">Write</option>
      </select>

      <textarea
        placeholder="Paste schema DDL here"
        value={schema}
        onChange={e => setSchema(e.target.value)}
        rows={6}
        style={{ width: "100%" }}
      />

      <textarea
        placeholder="Describe what you want"
        value={criteria}
        onChange={e => setCriteria(e.target.value)}
        rows={3}
        style={{ width: "100%" }}
      />

      <button onClick={generateSQL} disabled={loading}>
        {loading ? "Generating..." : "Generate SQL"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {result && <pre>{result}</pre>}
    </div>
  );
}

export default App;