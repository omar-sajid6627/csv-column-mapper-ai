import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { getCodeAndSuggestions, mapCode, updateSuggestions } from './Apis';

vi.mock('./Apis', async (importOriginal) => ({
  ...(await importOriginal()),
  getCodeAndSuggestions: vi.fn(),
  updateSuggestions: vi.fn(),
  mapCode: vi.fn(),
}));

const SUGGESTION = 'Mapped Columns:\n1. Name -> EmployeeName';
const CODE = "mapped_df = input_df.rename(columns={'Name': 'EmployeeName'})";

const csv = (name, text) => new File([text], name, { type: 'text/csv' });

async function uploadBoth() {
  await userEvent.upload(screen.getByLabelText(/input file/i), csv('input.csv', 'Name\nAda\n'));
  await userEvent.upload(screen.getByLabelText(/template file/i), csv('template.csv', 'EmployeeName\nJo\n'));
  await userEvent.click(screen.getByRole('button', { name: /upload files/i }));
  await waitFor(() => expect(screen.getByLabelText(/mapping script/i)).toHaveValue(CODE));
}

beforeEach(() => {
  vi.resetAllMocks();
  getCodeAndSuggestions.mockResolvedValue({ data: { suggestion: SUGGESTION, code: CODE } });
});

test('upload stays disabled until both files are chosen', async () => {
  render(<App />);
  const upload = screen.getByRole('button', { name: /upload files/i });
  expect(upload).toBeDisabled();
  await userEvent.upload(screen.getByLabelText(/input file/i), csv('input.csv', 'Name\n'));
  expect(upload).toBeDisabled();
  await userEvent.upload(screen.getByLabelText(/template file/i), csv('template.csv', 'EmployeeName\n'));
  expect(upload).toBeEnabled();
});

test('shows the suggestion and script as plain text', async () => {
  render(<App />);
  await uploadBoth();
  expect(screen.getByLabelText(/suggested column mapping/i)).toHaveValue(SUGGESTION);
  const sent = getCodeAndSuggestions.mock.calls[0][0];
  expect(sent.get('input_table').name).toBe('input.csv');
  expect(sent.get('template_table').name).toBe('template.csv');
});

test('sends the edited suggestion as raw text', async () => {
  updateSuggestions.mockResolvedValue({ data: { suggestion: 'revised', code: 'mapped_df = input_df' } });
  render(<App />);
  await uploadBoth();
  await userEvent.click(screen.getByRole('button', { name: /update suggestions/i }));
  await waitFor(() => expect(screen.getByLabelText(/mapping script/i)).toHaveValue('mapped_df = input_df'));
  expect(updateSuggestions.mock.calls[0][0].get('suggestion')).toBe(SUGGESTION);
});

test('reports an API error from the suggestion request', async () => {
  getCodeAndSuggestions.mockRejectedValue({ response: { status: 413, data: { detail: 'input.csv: file is larger than 2048 KB' } } });
  render(<App />);
  await userEvent.upload(screen.getByLabelText(/input file/i), csv('input.csv', 'Name\n'));
  await userEvent.upload(screen.getByLabelText(/template file/i), csv('template.csv', 'EmployeeName\n'));
  await userEvent.click(screen.getByRole('button', { name: /upload files/i }));
  expect(await screen.findByText('input.csv: file is larger than 2048 KB')).toBeInTheDocument();
});

test('renders mapped rows and script errors with their line', async () => {
  mapCode.mockResolvedValueOnce({ data: [{ EmployeeName: 'Ada' }] });
  render(<App />);
  expect(screen.getByText(/run the mapping script/i)).toBeInTheDocument();
  await uploadBoth();
  await userEvent.click(screen.getByRole('button', { name: /^map$/i }));
  expect(await screen.findByRole('cell', { name: 'Ada' })).toBeInTheDocument();

  mapCode.mockRejectedValueOnce({ response: { status: 422, data: { detail: "KeyError: 'Name'", line: 2 } } });
  await userEvent.click(screen.getByRole('button', { name: /^map$/i }));
  expect(await screen.findByText("Line 2: KeyError: 'Name'")).toBeInTheDocument();
  expect(screen.queryByRole('cell', { name: 'Ada' })).not.toBeInTheDocument();
});
