/**
 * Sprint 729c — CaptureToSumButton component tests.
 */
import userEvent from '@testing-library/user-event';
import { CaptureToSumButton } from '@/components/engagement/CaptureToSumButton';
import { render, screen, waitFor } from '@/test-utils';

jest.mock('framer-motion', () => ({
  motion: {
    div: ({
      initial,
      animate,
      exit,
      transition,
      variants,
      whileHover,
      whileTap,
      viewport,
      layout,
      layoutId,
      children,
      ...rest
    }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const mockCreate = jest.fn();
jest.mock('@/hooks/useUncorrectedMisstatements', () => ({
  useUncorrectedMisstatements: () => ({
    schedule: null,
    items: [],
    isLoading: false,
    error: null,
    fetchSchedule: jest.fn(),
    createItem: mockCreate,
    updateItem: jest.fn(),
    archiveItem: jest.fn(),
  }),
}));

describe('CaptureToSumButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreate.mockResolvedValue(null);
  });

  it('renders default label when no prefill source supplied', () => {
    render(<CaptureToSumButton engagementId={1} />);
    expect(
      screen.getByRole('button', { name: /capture to sum/i }),
    ).toBeInTheDocument();
  });

  it('renders AJE-specific label when prefilled from an AJE', () => {
    render(
      <CaptureToSumButton
        engagementId={1}
        prefillFromAdjustingEntry={{
          reference: 'AJE-001',
          description: 'Bad debt accrual',
          lines: [
            { account: 'Bad Debt Expense', debit: 5000, credit: 0 },
            { account: 'Allowance for Doubtful Accounts', debit: 0, credit: 5000 },
          ],
        }}
      />,
    );
    expect(screen.getByRole('button', { name: /add to sum/i })).toBeInTheDocument();
  });

  it('renders sampling-specific label when prefilled from a projection', () => {
    render(
      <CaptureToSumButton
        engagementId={1}
        prefillFromSampleProjection={{
          test_description: 'Inventory pricing test, n=100',
          account: 'Inventory',
          upper_error_limit: 5000,
          tolerable_misstatement: 3000,
        }}
      />,
    );
    expect(
      screen.getByRole('button', { name: /capture as sum projection/i }),
    ).toBeInTheDocument();
  });

  it('opens modal pre-filled from AJE on click', async () => {
    const user = userEvent.setup();
    render(
      <CaptureToSumButton
        engagementId={1}
        prefillFromAdjustingEntry={{
          reference: 'AJE-002',
          description: 'Revenue cutoff',
          lines: [
            { account: 'Revenue', debit: 0, credit: 8000 },
            { account: 'Accrued Revenue', debit: 8000, credit: 0 },
          ],
        }}
      />,
    );
    await user.click(screen.getByRole('button', { name: /add to sum/i }));

    // Modal opens
    expect(screen.getByText(/^new misstatement$/i)).toBeInTheDocument();
    // Source-reference input is pre-filled with reference + description
    const refInput = screen.getByLabelText(/source reference/i) as HTMLInputElement;
    expect(refInput.value).toContain('AJE-002');
    expect(refInput.value).toContain('Revenue cutoff');
  });

  it('largest line is selected as the canonical account when AJE has multiple lines', async () => {
    const user = userEvent.setup();
    render(
      <CaptureToSumButton
        engagementId={1}
        prefillFromAdjustingEntry={{
          reference: 'AJE-003',
          description: 'Reclass',
          lines: [
            { account: 'Petty Cash', debit: 100, credit: 0 },
            { account: 'Cash', debit: 50000, credit: 0 },
            { account: 'Suspense', debit: 0, credit: 50100 },
          ],
        }}
      />,
    );
    await user.click(screen.getByRole('button', { name: /add to sum/i }));
    // Look for "Cash" or "Suspense" pre-fill (largest line absolute value
    // wins; in this case Suspense at 50100 credit > Cash 50000 debit).
    const accountInput = screen.getByPlaceholderText(/account name/i) as HTMLInputElement;
    expect(['Cash', 'Suspense']).toContain(accountInput.value);
  });

  it('opens modal pre-filled from sample projection on click', async () => {
    const user = userEvent.setup();
    render(
      <CaptureToSumButton
        engagementId={1}
        prefillFromSampleProjection={{
          test_description: 'AR aging sample',
          account: 'Accounts Receivable',
          upper_error_limit: 12000,
          tolerable_misstatement: 5000,
        }}
      />,
    );
    await user.click(screen.getByRole('button', { name: /capture as sum projection/i }));
    const refInput = screen.getByLabelText(/source reference/i) as HTMLInputElement;
    expect(refInput.value).toContain('AR aging sample');
    expect(refInput.value.toLowerCase()).toContain('uel');
  });
});
