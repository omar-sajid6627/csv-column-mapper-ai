import { useState } from 'react';
import { errorMessage, mapCode } from '../../Apis';

function CodeEditor({ code, setCode, file, setRows }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('input_table', file);
    formData.append('code', code);
    setLoading(true);
    setError('');
    mapCode(formData)
      .then((res) => setRows(res.data))
      .catch((err) => {
        setRows([]);
        setError(errorMessage(err));
      })
      .finally(() => setLoading(false));
  };

  return (
    <form className="editor" onSubmit={handleSubmit}>
      <label htmlFor="script" className="visually-hidden">Mapping script</label>
      <p className="hint" id="script-hint">
        Python with <code>pd</code>, <code>np</code> and <code>datetime</code>; assign the result to <code>mapped_df</code>.
      </p>
      <textarea
        id="script"
        className="code"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        aria-describedby="script-hint"
        placeholder="mapped_df = input_df"
        rows={12}
        spellCheck={false}
      />
      <button type="submit" className="primary" disabled={!file || !code || loading} aria-busy={loading}>
        {loading ? 'Running…' : 'Run script'}
      </button>
      {error && <p role="alert" className="error">{error}</p>}
    </form>
  );
}

export default CodeEditor;
