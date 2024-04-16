import { useEffect, useState } from 'react';
import CodeEditor from './components/CodeEditor/CodeEditor';
import OutputTable from './components/OutputTable/OutputTable';
import Suggestions from './components/Suggestions/Suggestions';
import UploadCSV from './components/UploadCSV/UploadCSV';
import { errorMessage, getCodeAndSuggestions, getHealth } from './Apis';
import './App.css';

const MODE_LABELS = { openai: 'OpenAI model', demo: 'Offline demo matcher' };

function App() {
  const [file, setFile] = useState(null);
  const [template, setTemplate] = useState(null);
  const [suggestion, setSuggestion] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState([]);
  const [mode, setMode] = useState(null);

  useEffect(() => {
    getHealth()
      .then((res) => setMode(MODE_LABELS[res.data.llm_mode] || res.data.llm_mode))
      .catch(() => setMode('API offline'));
  }, []);

  const pickFile = (setter) => (picked) => {
    setter(picked);
    setRows([]);
  };

  const handleSubmitFiles = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('input_table', file);
    formData.append('template_table', template);
    setLoading(true);
    setError('');
    getCodeAndSuggestions(formData)
      .then((res) => {
        setSuggestion(res.data.suggestion);
        setCode(res.data.code);
        setRows([]);
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  };

  return (
    <div className="page">
      <header className="masthead">
        <div>
          <h1>CSV Column Mapper</h1>
          <p className="tagline">Match an input CSV to a template, review the mapping, then run the script that reshapes it.</p>
        </div>
        {mode && (
          <p className="mode" aria-live="polite">
            <span className="mode-label">Suggestions by</span> {mode}
          </p>
        )}
      </header>

      <main>
        <section className="panel" aria-labelledby="step-files">
          <h2 id="step-files"><span className="step">1</span> Choose the two CSVs</h2>
          <form className="files" onSubmit={handleSubmitFiles}>
            <UploadCSV id="input-file" label="Input file" hint="The data you have" file={file} setFile={pickFile(setFile)} />
            <UploadCSV id="template-file" label="Template file" hint="The columns you want" file={template} setFile={pickFile(setTemplate)} />
            <button type="submit" className="primary" disabled={!file || !template || loading} aria-busy={loading}>
              {loading ? 'Asking for a mapping…' : 'Suggest mapping'}
            </button>
          </form>
          {error && <p role="alert" className="error">{error}</p>}
        </section>

        <div className="workbench">
          <section className="panel" aria-labelledby="step-mapping">
            <h2 id="step-mapping"><span className="step">2</span> Review the mapping</h2>
            <Suggestions
              suggestion={suggestion}
              setSuggestion={setSuggestion}
              setCode={setCode}
              inputFile={file}
              templateFile={template}
            />
          </section>
          <section className="panel" aria-labelledby="step-script">
            <h2 id="step-script"><span className="step">3</span> Edit and run the script</h2>
            <CodeEditor code={code} setCode={setCode} file={file} setRows={setRows} />
          </section>
        </div>

        <section className="panel" aria-labelledby="step-output">
          <h2 id="step-output"><span className="step">4</span> Mapped rows</h2>
          <OutputTable rows={rows} />
        </section>
      </main>
    </div>
  );
}

export default App;
