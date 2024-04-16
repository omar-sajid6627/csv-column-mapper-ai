import { downloadCsv } from '../../csv';

const show = (value) => (value === null || value === undefined ? '' : String(value));

function OutputTable({ rows }) {
  if (!rows.length) {
    return <p className="empty">Run the script in step 3 to see the mapped rows here.</p>;
  }
  const headers = Object.keys(rows[0]);
  return (
    <>
      <div className="table-scroll" role="region" aria-labelledby="step-output" tabIndex={0}>
        <table>
          <caption className="visually-hidden">{rows.length} mapped rows</caption>
          <thead>
            <tr>
              {headers.map((header) => (
                <th key={header} scope="col">{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {headers.map((header) => (
                  <td key={header}>{show(row[header])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">
        <span>{rows.length} {rows.length === 1 ? 'row' : 'rows'} · {headers.length} columns</span>
        <button type="button" className="secondary" onClick={() => downloadCsv(rows, 'mapped.csv')}>
          Download CSV
        </button>
      </div>
    </>
  );
}

export default OutputTable;
