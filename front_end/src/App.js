import React, { useState } from 'react';
import { Alert, Grid } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import Suggestions from './components/Suggestions/Suggestions';
import CodeEditor from './components/CodeEditor/CodeEditor';
import OutputTable from './components/OutputTable/OutputTable';
import UploadCSV from './components/UploadCSV/UploadCSV';
import { errorMessage, getCodeAndSuggestions } from './Apis';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [template, setTemplate] = useState(null);
  const [suggestions, setSuggestions] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [outputData, setOutputData] = useState([]);

  const handleSubmitFiles = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('input_table', file);
    formData.append('template_table', template);
    setLoading(true);
    setError('');
    getCodeAndSuggestions(formData)
      .then((res) => {
        setCode(res.data.code);
        setSuggestions(res.data.suggestion);
        setOutputData([]);
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  };

  return (
    <div className="App">
      <Grid container spacing={4}>
        <Grid item xs={12}>
          <h1>CSV Column Mapper</h1>
        </Grid>
        <Grid className="form-input" container xs={12}>
          <Grid item xs={4}>
            <UploadCSV label="Input File" id="input-file" setFile={setFile} />
          </Grid>
          <Grid item xs={4}>
            <UploadCSV label="Template File" id="template-file" setFile={setTemplate} />
          </Grid>
          <Grid item xs={4}>
            <LoadingButton
              loading={loading}
              loadingPosition="center"
              variant="contained"
              disabled={!file || !template}
              onClick={handleSubmitFiles}
            >
              Upload Files
            </LoadingButton>
          </Grid>
          {error && <Alert severity="error">{error}</Alert>}
        </Grid>
        <Grid className="grid-input" container xs={12}>
          <Grid item xs={5}>
            <h2>Suggestions</h2>
            <Suggestions setSuggestions={setSuggestions} setCode={setCode} inputFile={file} templateFile={template} suggestions={suggestions} />
          </Grid>
          <Grid item xs={5}>
            <h2>Code Editor</h2>
            <CodeEditor setOutputData={setOutputData} file={file} code={code} />
          </Grid>
        </Grid>
        <Grid className="table-grid" item xs={12}>
          <h2>Output Data</h2>
          <OutputTable rows={outputData} />
        </Grid>
      </Grid>
    </div>
  );
}

export default App;
