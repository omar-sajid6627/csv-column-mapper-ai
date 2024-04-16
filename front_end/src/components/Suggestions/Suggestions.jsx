import { useState } from 'react';
import { errorMessage, updateSuggestions } from '../../Apis';

function Suggestions({ suggestion, setSuggestion, setCode, inputFile, templateFile }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('input_table', inputFile);
    formData.append('template_table', templateFile);
    formData.append('suggestion', suggestion);
    setLoading(true);
    setError('');
    updateSuggestions(formData)
      .then((res) => {
        setSuggestion(res.data.suggestion);
        setCode(res.data.code);
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  };

  return (
    <form className="editor" onSubmit={handleSubmit}>
      <label htmlFor="suggestion" className="visually-hidden">Suggested column mapping</label>
      <p className="hint" id="suggestion-hint">
        Edit the <code>source -&gt; target</code> lines, then ask for a script that follows them.
      </p>
      <textarea
        id="suggestion"
        value={suggestion}
        onChange={(e) => setSuggestion(e.target.value)}
        aria-describedby="suggestion-hint"
        placeholder="The suggested mapping appears here after step 1."
        rows={12}
        spellCheck={false}
      />
      <button type="submit" className="secondary" disabled={!inputFile || !templateFile || !suggestion || loading} aria-busy={loading}>
        {loading ? 'Rewriting script…' : 'Rewrite script from this mapping'}
      </button>
      {error && <p role="alert" className="error">{error}</p>}
    </form>
  );
}

export default Suggestions;
