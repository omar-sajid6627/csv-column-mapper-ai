import './UploadCSV.css';

function UploadCSV({ setFile, label, id }) {
  return (
    <div>
      <label htmlFor={id}>{label}: </label>
      <input type="file" id={id} accept=".csv,text/csv" onChange={(e) => setFile(e.target.files[0] || null)} />
    </div>
  );
}

export default UploadCSV;
