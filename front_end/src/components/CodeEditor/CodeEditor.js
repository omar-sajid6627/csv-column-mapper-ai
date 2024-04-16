import React, { useState, useEffect } from 'react';
import { Alert, TextField } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import { errorMessage, mapCode } from '../../Apis';
import './CodeEditor.css';

function CodeEditor({ file, code, setOutputData }) {
  const [editedCode, setEditedCode] = useState(code);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setEditedCode(code);
  }, [code]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('input_table', file);
    formData.append('code', editedCode);
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
        value={editedCode}
        onChange={(e) => setEditedCode(e.target.value)}
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
        disabled={!file || !editedCode}
        onClick={handleSubmit}
      >
        Map
      </LoadingButton>
      {error && <Alert severity="error">{error}</Alert>}
    </div>
  );
}

export default CodeEditor;
