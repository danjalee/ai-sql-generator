import React, { useState, useRef } from "react";
import "./App.css";

function getSecretKey() {
  const params = new URLSearchParams(window.location.search);
  return params.get("key");
}

const TEXT = {
  en: {
    title: "AI SQL Generator",
    appLanguage: "🌐 Language",
    databaseType: "🗄️ Database Type",
    schemaInput: "📄 Schema Input",
    criteriaInput: "🧠 Criteria Input",
    generate: "▶ Generate SQL",
    generating: "Generating...",
    clear: "🧹 Clear All",
    output: "📤 SQL Output",
    copy: "📋 Copy",
    copied: "Copied!",
    stop: "🛑 Stop",
    schemaPlaceholder:
`-- Paste CREATE TABLE statements here
-- Multiple tables supported`,
    criteriaPlaceholder: "Describe what you want to do",
    requiredAlert: "Schema and criteria are required"
  },
  ja: {
    title: "AI SQL ジェネレーター",
    appLanguage: "🌐 言語",
    databaseType: "🗄️ データベース種類",
    schemaInput: "📄 スキーマ入力",
    criteriaInput: "🧠 条件入力",
    generate: "▶ SQL 生成",
    generating: "生成中...",
    clear: "🧹 全てクリア",
    output: "📤 SQL 出力",
    copy: "📋 コピー",
    copied: "コピー済み",
    stop: "🛑 停止",
    schemaPlaceholder:
`-- CREATE TABLE 文を貼り付けてください
-- 複数テーブル対応`,
    criteriaPlaceholder: "やりたいことを自然言語で入力",
    requiredAlert: "スキーマと条件を入力してください"
  }
};

function App() {
  const apiKey = getSecretKey();
  const [appLang, setAppLang] = useState("en");
  const [dbType, setDbType] = useState("mysql");
  const [schema, setSchema] = useState("");
  const [criteria, setCriteria] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const controllerRef = useRef(null);
  const t = TEXT[appLang];

  if (!apiKey) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "red" }}>
        <h2>Access denied</h2>
        <p>Invalid or missing access key.</p>
      </div>
    );
  }

  const clearAll = () => {
    setSchema("");
    setCriteria("");
    setOutput("");
  };

  const stopGenerating = () => {
    controllerRef.current?.abort();
    setLoading(false);
  };

  const copyOutput = () => {
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const generateSQL = async () => {
    if (!schema.trim() || !criteria.trim()) {
      alert(t.requiredAlert);
      return;
    }

    controllerRef.current = new AbortController();
    setLoading(true);
    setOutput("");

    try {
      const res = await fetch("http://localhost:8000/generate-sql", {
        method: "POST",
        signal: controllerRef.current.signal,
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey
        },
        body: JSON.stringify({
          language: appLang,
          database: dbType,
          schema,
          criteria
        })
      });

      if (!res.ok) {
        try {
          const errBody = await res.text();
          let msg = "Failed to generate SQL";
          try {
            const parsed = JSON.parse(errBody);
            msg = parsed.detail || msg;
          } catch (_) {
            msg = errBody || msg;
          }
          setOutput(msg);
        } catch {
          setOutput("Failed to generate SQL");
        }
      } else {
        const data = await res.json();
        setOutput(data.sql || "");
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setOutput("Failed to generate SQL");
      }
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: 20, maxWidth: 900, margin: "auto" }}>
      <h2>{t.title}</h2>

      <label>{t.appLanguage}</label><br />
      <select value={appLang} onChange={e => setAppLang(e.target.value)}>
        <option value="en">English</option>
        <option value="ja">日本語</option>
      </select>

      <hr />

      <label>{t.databaseType}</label><br />
      <select value={dbType} onChange={e => setDbType(e.target.value)}>
        <option value="mysql">MySQL</option>
        <option value="postgresql">PostgreSQL</option>
        <option value="sqlserver">SQL Server</option>
        <option value="sqlite">SQLite</option>
      </select>

      <hr />

      <label>{t.schemaInput}</label>
      <textarea rows={12} style={{ width: "100%" }}
        value={schema}
        onChange={e => setSchema(e.target.value)}
        placeholder={t.schemaPlaceholder}
      />

      <hr />

      <label>{t.criteriaInput}</label>
      <textarea rows={4} style={{ width: "100%" }}
        value={criteria}
        onChange={e => setCriteria(e.target.value)}
        placeholder={t.criteriaPlaceholder}
      />

      <br /><br />

      <button onClick={generateSQL} disabled={loading}>
        {loading ? t.generating : t.generate}
      </button>

      {loading && <button onClick={stopGenerating}>{t.stop}</button>}
      {output && <button onClick={copyOutput}>{copied ? t.copied : t.copy}</button>}
      {(schema || criteria || output) && <button onClick={clearAll}>{t.clear}</button>}

      <hr />

      <label>{t.output}</label>
      <textarea rows={10} style={{ width: "100%" }} value={output} readOnly />
    </div>
  );
}

export default App;
