import React, { useState, useEffect } from 'react';
import './App.css';

const T = {
  en: {
    title: 'Bridgemakers GmbH',
    runBtn: { on: 'Run New Interview', busy: 'Running Interview…' },
    recent: 'Recent Interviews',
    noInterviews: 'No interviews yet. Click "Run New Interview" to start.',
    table: {
      time: 'Time',
      agent: 'Agent',
      question: 'Question',
      answer: 'Answer',
    },
    footer: '© 2025 Bridgemakers GmbH',
    provider: {
      label: 'AI Provider',
      openai: 'OpenAI',
      ollama: 'Ollama'
    }
  },
  de: {
    title: 'Bridgemakers GmbH',
    runBtn: { on: 'Neues Interview starten', busy: 'Interview läuft…' },
    recent: 'Letzte Interviews',
    noInterviews: 'Noch keine Interviews. Klicken Sie auf „Neues Interview starten“.',
    table: {
      time: 'Zeit',
      agent: 'Agent',
      question: 'Frage',
      answer: 'Antwort',
    },
    provider: {
      label: 'KI-Anbieter',
      openai: 'OpenAI',
      ollama: 'Ollama'
    },
    footer: '© 2025 Bridgemakers GmbH',
  },
};

const LanguageIcon = ({ lang }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    {lang === 'de' ? (
      <>
        <rect width="24" height="24" fill="#000000" />
        <rect y="8" width="24" height="8" fill="#DD0000" />
        <rect y="16" width="24" height="8" fill="#FFCE00" />
      </>
    ) : (
      <>
        <rect width="24" height="24" fill="#012169" />
        <rect width="24" height="2.4" fill="#FFFFFF" />
        <rect y="4.8" width="24" height="2.4" fill="#FFFFFF" />
        <rect y="9.6" width="24" height="2.4" fill="#FFFFFF" />
        <rect y="14.4" width="24" height="2.4" fill="#FFFFFF" />
        <rect y="19.2" width="24" height="2.4" fill="#FFFFFF" />
        <rect width="2.4" height="24" fill="#FFFFFF" />
        <rect x="4.8" width="2.4" height="24" fill="#FFFFFF" />
        <rect x="9.6" width="2.4" height="24" fill="#FFFFFF" />
        <rect x="14.4" width="2.4" height="24" fill="#FFFFFF" />
        <rect x="19.2" width="2.4" height="24" fill="#FFFFFF" />
        <rect width="14.4" height="14.4" fill="#C8102E" />
        <rect x="9.6" width="2.4" height="24" fill="#C8102E" />
        <rect width="2.4" height="24" fill="#C8102E" />
      </>
    )}
  </svg>
);

function App() {
  const [lang, setLang] = useState('de');
  const [provider, setProvider] = useState('openai');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const tr = T[lang];

  useEffect(() => {
    fetch('/interview-results')
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(data => setResults(data))
      .catch(console.error);
  }, []);

  const runInterview = async () => {
    setLoading(true);
    try {
      const qRes = await fetch('/questions');
      const questions = await qRes.json();

      const interviewRes = await fetch('/run-interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questions,provider }),
      });
      if (!interviewRes.ok) throw new Error(interviewRes.statusText);

      const updated = await fetch('/interview-results').then(r => r.json());
      setResults(updated);
    } catch (err) {
      console.error(err);
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (

<div className="app-container">
  <header className="app-header">
    <h1>{tr.title}</h1>
    <div className="header-actions">
      {/* Model Selector - New Dropdown */}
      <div className="model-selector">
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          disabled={loading}
          className="model-dropdown"
        >
          <option value="openai">OpenAI</option>
          <option value="ollama">Llama 3</option>
        </select>
      </div>

      {/* Existing Language Toggle */}
      <button
        className="lang-toggle"
        onClick={() => setLang(lang === 'en' ? 'de' : 'en')}
        aria-label={lang === 'en' ? 'Switch to German' : 'Switch to English'}
        title={lang === 'en' ? 'Deutsch' : 'English'}
      >
        <LanguageIcon lang={lang} />
        <span className="lang-label">
          {lang === 'en' ? 'DE' : 'EN'}
        </span>
      </button>

      {/* Existing Run Button */}
      <button
        className="primary-btn"
        onClick={runInterview}
        disabled={loading}
      >
        {loading ? tr.runBtn.busy : tr.runBtn.on}
      </button>
    </div>
  </header>

      <main className="content-area">
        <h2>{tr.recent}</h2>
        {results.length === 0 ? (
          <p className="empty-state">{tr.noInterviews}</p>
        ) : (
          <table className="results-table">
            <thead>
              <tr>
                <th>{tr.table.time}</th>
                <th>{tr.table.agent}</th>
                <th>{tr.table.question}</th>
                <th>{tr.table.answer}</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row, i) => (
                <tr key={row.id || i}>
                  <td>{new Date(row.timestamp).toLocaleString(lang)}</td>
                  <td>{row.agent}</td>
                                    <td>
                    {row[`question_${lang}`] ?? row.question_en}
                  </td>
                  <td className="answer-cell"
                    style={{
                      whiteSpace: 'pre-wrap',
                      wordBreak:   'break-word',
                    }}
                  >
                    {row[`answer_${lang}`]   ?? row.answer_en}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>

      <footer className="app-footer">
        {tr.footer}
      </footer>
    </div>
  );
}

export default App;