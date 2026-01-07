import React, { useState } from "react";
import "./App.css";

/* ===============================
   Get secret key from URL
================================ */
function getSecretKey() {
  const params = new URLSearchParams(window.location.search);
  return params.get("key");
}

/* ===============================
   UI text
================================ */
const TEXT = {
  en: {
    title: "AI SQL Generator",
    appLanguage: "🌐 App Language",
    databaseType: "🗄️ Database Type",
    sqlMode: "✍ SQL Mode",
    readMode: "Read (SELECT)",
    writeMode: "Write (INSERT / UPDATE / DELETE / DDL)",
    schemaInput: "📄 Schema Input",
    criteriaInput: "🧠 Criteria Input",
    generate: "▶ Generate SQL",
    generating: "Generating...",
    clear: "🧹 Clear All",
    output: "📤 SQL Output",
    schemaPlaceholder:
`-- Paste CREATE TABLE statements here
-- Multiple tables supported`,
    criteriaPlaceholder: "Get all users",
    requiredAlert: "Schema and criteria are required",
    writeWarning: "⚠️ This SQL may modify or destroy data. Continue?"
  },
  ja: {
    title: "AI SQL ジェネレーター",
    appLanguage: "🌐 言語",
    databaseType: "🗄️ データベース種類",
    sqlMode: "✍ SQL モード",
    readMode: "読取 (SELECT)",
    writeMode: "書込 (INSERT / UPDATE / DELETE / DDL)",
    schemaInput: "📄 スキーマ入力",
    criteriaInput: "🧠 条件入力",
    generate: "▶ SQL 生成",
    generating: "生成中...",
    clear: "🧹 全てクリア",
    output: "📤 SQL 出力",
    schemaPlaceholder:
`-- CREATE TABLE 文を貼り付けてください
-- 複数テーブル対応`,
    criteriaPlaceholder: "すべてのユーザーを取得",
    requiredAlert: "スキーマと条件を入力してください",
    writeWarning: "⚠️ このSQLはデータを変更・削除する可能性があります。続行しますか？"
  }
};

function App() {
  /* ===============================
     Hooks (ALWAYS FIRST)
  ================================ */
  const apiKey = getSecretKey();

  const [appLang, setAppLang] = useState("en");
  const [dbType, setDbType] = useState("mysql");
  const [sqlMode, setSqlMode] = useState("read");
  const [schema, setSchema] = useState("");
  const [criteria, setCriteria] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  const t = TEXT[appLang];

  /* ===============================
     Access control (AFTER hooks)
  ================================ */
  if (!apiKey) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "red" }}>
        <h2>Access denied</h2>
        <p>Invalid or missing access key.</p>
      </div>
    );
  }

  const hasContent =
    schema.trim() !== "" ||
    criteria.trim() !== "" ||
    output.trim() !== "";

  const clearAll = () => {
    setSchema("");
    setCriteria("");
    setOutput("");
  };

  const generateSQL = async () => {
    if (!schema.trim() || !criteria.trim()) {
      alert(t.requiredAlert);
      return;
    }

    if (sqlMode === "write" && !window.confirm(t.writeWarning)) return;

    setLoading(true);
    setOutput("");

    try {
      const res = await fetch("https://ai-sql-generator-rh5f.onrender.com/generate-sql", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey
        },
        body: JSON.stringify({
          language: appLang,
          database: dbType,
          sqlMode,
          schema,
          criteria
        })
      });

      if (!res.ok) throw new Error();

      const data = await res.json();
      setOutput(data.sql || "");
    } catch {
      setOutput("Failed to connect to backend or access denied");
    }

    setLoading(false);
  };

  /* ===============================
     UI
  ================================ */
  return (
    <div style={{ padding: 20, maxWidth: 900, margin: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h2>{t.title}</h2>

        <div>
          <label>{t.appLanguage}</label><br />
          <select value={appLang} onChange={e => setAppLang(e.target.value)}>
            <option value="en">English</option>
            <option value="ja">日本語</option>
          </select>
        </div>
      </div>

      <hr />

      <label>{t.databaseType}</label><br />
      <select value={dbType} onChange={e => setDbType(e.target.value)}>
        <option value="mysql">MySQL</option>
        <option value="postgresql">PostgreSQL</option>
        <option value="sqlserver">SQL Server</option>
        <option value="sqlite">SQLite</option>
      </select>

      <hr />

      <label>{t.sqlMode}</label><br />
      <select value={sqlMode} onChange={e => setSqlMode(e.target.value)}>
        <option value="read">{t.readMode}</option>
        <option value="write">{t.writeMode}</option>
      </select>

      <hr />

      <label>{t.schemaInput}</label>
      <textarea
        rows={12}
        style={{ width: "100%" }}
        value={schema}
        onChange={e => setSchema(e.target.value)}
        placeholder={t.schemaPlaceholder}
      />

      <hr />

      <label>{t.criteriaInput}</label>
      <textarea
        rows={4}
        style={{ width: "100%" }}
        value={criteria}
        onChange={e => setCriteria(e.target.value)}
        placeholder={t.criteriaPlaceholder}
      />

      <br /><br />

      <button onClick={generateSQL} disabled={loading}>
        {loading ? t.generating : t.generate}
      </button>

      {hasContent && (
        <button onClick={clearAll} style={{ marginLeft: 10 }}>
          {t.clear}
        </button>
      )}

      <hr />

      <label>{t.output}</label>
      <textarea rows={10} style={{ width: "100%" }} value={output} readOnly />
    </div>
  );
}

export default App;