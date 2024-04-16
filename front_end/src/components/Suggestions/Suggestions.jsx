import { useState } from 'react';
import { Alert, TextField } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import { errorMessage, updateSuggestions } from '../../Apis';
import './Suggestions.css';

function Suggestions({ setSuggestions, setCode, inputFile, templateFile, suggestions }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('input_table', inputFile);
    formData.append('template_table', templateFile);
    formData.append('suggestion', suggestions);
    setLoading(true);
    setError('');
    updateSuggestions(formData)
      .then((res) => {
        setSuggestions(res.data.suggestion);
        setCode(res.data.code);
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  };

  return (
    <div className="suggestions-container">
      <TextField
        value={suggestions}
        onChange={(e) => setSuggestions(e.target.value)}
        inputProps={{ 'aria-label': 'Suggested column mapping' }}
        multiline
        rows={10}
        variant="outlined"
        fullWidth
      />
      <LoadingButton
        loading={loading}
        loadingPosition="center"
        variant="contained"
        disabled={!inputFile || !templateFile || !suggestions}
        onClick={handleSubmit}
      >
        Update Suggestions
      </LoadingButton>
      {error && <Alert severity="error">{error}</Alert>}
    </div>
  );
}

export default Suggestions;
