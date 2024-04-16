import { toCsv } from './csv';

test('quotes commas, quotes and newlines and blanks nulls', () => {
  const rows = [
    { name: 'Ada, Example', note: 'said "hi"', empty: null },
    { name: 'Line\nbreak', note: 'plain', empty: 0 },
  ];
  expect(toCsv(rows)).toBe('name,note,empty\r\n"Ada, Example","said ""hi""",\r\n"Line\nbreak",plain,0\r\n');
});

test('returns an empty string for no rows', () => {
  expect(toCsv([])).toBe('');
});
