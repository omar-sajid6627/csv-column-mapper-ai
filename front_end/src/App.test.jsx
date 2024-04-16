import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { getCodeAndSuggestions, getHealth, mapCode, updateSuggestions } from './Apis';

vi.mock('./Apis', async (importOriginal) => ({
  ...(await importOriginal()),
  getHealth: vi.fn(),
  getCodeAndSuggestions: vi.fn(),
  updateSuggestions: vi.fn(),
  mapCode: vi.fn(),
}));

const SUGGESTION = 'Mapped Columns:\n1. Name -> EmployeeName';
const CODE = "mapped_df = input_df.rename(columns={'Name': 'EmployeeName'})";

const csv = (name, text) => new File([text], name, { type: 'text/csv' });

async function chooseFiles() {
  await userEvent.upload(screen.getByLabelText(/input file/i), csv('input.csv', 'Name\nAda\n'));
  await userEvent.upload(screen.getByLabelText(/template file/i), csv('template.csv', 'EmployeeName\nJo\n'));
}

async function suggest() {
  await chooseFiles();
  await userEvent.click(screen.getByRole('button', { name: /suggest mapping/i }));
  await waitFor(() => expect(screen.getByLabelText(/mapping script/i)).toHaveValue(CODE));
}

beforeEach(() => {
  vi.resetAllMocks();
  getHealth.mockResolvedValue({ data: { status: 'ok', llm_mode: 'demo' } });
  getCodeAndSuggestions.mockResolvedValue({ data: { suggestion: SUGGESTION, code: CODE } });
});

test('shows which matcher answers', async () => {
  render(<App />);
  expect(await screen.findByText(/offline demo matcher/i)).toBeInTheDocument();
});

test('says so when the API is down', async () => {
  getHealth.mockRejectedValue(new Error('network'));
  render(<App />);
  expect(await screen.findByText(/api offline/i)).toBeInTheDocument();
});

test('suggest stays disabled until both files are chosen', async () => {
  render(<App />);
  const button = screen.getByRole('button', { name: /suggest mapping/i });
  expect(button).toBeDisabled();
  await userEvent.upload(screen.getByLabelText(/input file/i), csv('input.csv', 'Name\n'));
  expect(button).toBeDisabled();
  expect(screen.getByText(/input\.csv · 5 B/)).toBeInTheDocument();
  await userEvent.upload(screen.getByLabelText(/template file/i), csv('template.csv', 'EmployeeName\n'));
  expect(button).toBeEnabled();
});

test('shows the suggestion and script as plain text', async () => {
  render(<App />);
  await suggest();
  expect(screen.getByLabelText(/suggested column mapping/i)).toHaveValue(SUGGESTION);
  const sent = getCodeAndSuggestions.mock.calls[0][0];
  expect(sent.get('input_table').name).toBe('input.csv');
  expect(sent.get('template_table').name).toBe('template.csv');
});

test('sends the edited mapping as raw text', async () => {
  updateSuggestions.mockResolvedValue({ data: { suggestion: 'revised', code: 'mapped_df = input_df' } });
  render(<App />);
  await suggest();
  await userEvent.click(screen.getByRole('button', { name: /rewrite script/i }));
  await waitFor(() => expect(screen.getByLabelText(/mapping script/i)).toHaveValue('mapped_df = input_df'));
  expect(updateSuggestions.mock.calls[0][0].get('suggestion')).toBe(SUGGESTION);
  expect(screen.getByLabelText(/suggested column mapping/i)).toHaveValue('revised');
});

test('reports an upload error from the API', async () => {
  getCodeAndSuggestions.mockRejectedValue({
    response: { status: 413, data: { detail: 'input.csv: file is larger than 2048 KB' } },
  });
  render(<App />);
  await chooseFiles();
  await userEvent.click(screen.getByRole('button', { name: /suggest mapping/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('input.csv: file is larger than 2048 KB');
});

test('renders mapped rows, then a script error with its line', async () => {
  mapCode.mockResolvedValueOnce({ data: [{ EmployeeName: 'Ada', Age: null }] });
  render(<App />);
  expect(screen.getByText(/run the script in step 3/i)).toBeInTheDocument();
  await suggest();
  await userEvent.click(screen.getByRole('button', { name: /run script/i }));
  expect(await screen.findByRole('cell', { name: 'Ada' })).toBeInTheDocument();
  expect(screen.getByText(/1 row · 2 columns/)).toBeInTheDocument();

  mapCode.mockRejectedValueOnce({ response: { status: 422, data: { detail: "KeyError: 'Name'", line: 2 } } });
  await userEvent.click(screen.getByRole('button', { name: /run script/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent("Line 2: KeyError: 'Name'");
  expect(screen.queryByRole('cell', { name: 'Ada' })).not.toBeInTheDocument();
});

test('choosing a new file clears stale output', async () => {
  mapCode.mockResolvedValueOnce({ data: [{ EmployeeName: 'Ada' }] });
  render(<App />);
  await suggest();
  await userEvent.click(screen.getByRole('button', { name: /run script/i }));
  await screen.findByRole('cell', { name: 'Ada' });
  await userEvent.upload(screen.getByLabelText(/input file/i), csv('other.csv', 'Name\nBo\n'));
  expect(screen.queryByRole('cell', { name: 'Ada' })).not.toBeInTheDocument();
});
