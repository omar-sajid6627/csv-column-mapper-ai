const formatSize = (bytes) => (bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB`);

function UploadCSV({ id, label, hint, file, setFile }) {
  return (
    <div className="upload">
      <label htmlFor={id}>{label}</label>
      <span className="hint" id={`${id}-hint`}>{hint} · .csv up to 2 MB</span>
      <input
        type="file"
        id={id}
        accept=".csv,text/csv"
        aria-describedby={`${id}-hint`}
        onChange={(e) => setFile(e.target.files[0] || null)}
      />
      {file && <span className="chosen">{file.name} · {formatSize(file.size)}</span>}
    </div>
  );
}

export default UploadCSV;
