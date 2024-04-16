import { Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { CSVLink } from 'react-csv';
import './OutputTable.css';

function OutputTable({ rows }) {
  if (!rows.length) {
    return <p className="output-empty">Run the mapping script to see the mapped rows here.</p>;
  }
  const headers = Object.keys(rows[0]);
  return (
    <div className="output-table-container">
      <Table>
        <TableHead>
          <TableRow>
            {headers.map((header) => (
              <TableCell key={header}>{header}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={rowIndex}>
              {headers.map((header) => (
                <TableCell key={header}>{row[header] === null ? '' : String(row[header])}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <CSVLink data={rows} filename="mapped.csv" className="download-button">
        Download Results
      </CSVLink>
    </div>
  );
}

export default OutputTable;
