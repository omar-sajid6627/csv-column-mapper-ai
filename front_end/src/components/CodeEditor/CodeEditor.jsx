import { useState } from 'react';
import { Alert, TextField } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import { errorMessage, mapCode } from '../../Apis';
import './CodeEditor.css';

function CodeEditor({ file, code, setCode, setOutputData }) {
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
      .then((res) => setOutputData(res.data))
      .catch((err) => {
        setOutputData([]);
        setError(errorMessage(err));
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="code-editor-container">
      <TextField
        value={code}
        onChange={(e) => setCode(e.target.value)}
        inputProps={{ 'aria-label': 'Mapping script' }}
        multiline
        rows={10}
        variant="outlined"
        fullWidth
      />
      <LoadingButton
        loading={loading}
        loadingPosition="center"
        variant="contained"
        disabled={!file || !code}
        onClick={handleSubmit}
      >
        Map
      </LoadingButton>
      {error && <Alert severity="error">{error}</Alert>}
    </div>
  );
}

export default CodeEditor;
