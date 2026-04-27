/**
 * Sprint 728b — AnalyticalExpectationsPanel component tests.
 */
import userEvent from '@testing-library/user-event';
import { AnalyticalExpectationsPanel } from '@/components/engagement/AnalyticalExpectationsPanel';
import type { AnalyticalExpectation } from '@/types/analytical-expectations';
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

const makeItem = (overrides: Partial<AnalyticalExpectation> = {}): AnalyticalExpectation => ({
  id: 1,
  engagement_id: 1,
  procedure_target_type: 'account',
  procedure_target_label: 'Revenue',
  expected_value: 1000,
  expected_range_low: null,
  expected_range_high: null,
  precision_threshold_amount: 50,
  precision_threshold_percent: null,
  corroboration_basis_text: 'Prior-period growth analysis',
  corroboration_tags: ['prior_period'],
  cpa_notes: null,
  result_actual_value: null,
  result_variance_amount: null,
  result_status: 'not_evaluated',
  created_by: 1,
  created_at: '2026-04-26T00:00:00Z',
  updated_by: null,
  updated_at: '2026-04-26T00:00:00Z',
  ...overrides,
});

const defaultProps = {
  engagementId: 1,
  items: [],
  isLoading: false,
  onCreate: jest.fn(),
  onUpdate: jest.fn(),
  onArchive: jest.fn(),
  onDownload: jest.fn(),
};

describe('AnalyticalExpectationsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    defaultProps.onCreate.mockResolvedValue(null);
    defaultProps.onUpdate.mockResolvedValue(null);
    defaultProps.onArchive.mockResolvedValue(true);
    defaultProps.onDownload.mockResolvedValue(undefined);
  });

  it('renders empty state when no items', () => {
    render(<AnalyticalExpectationsPanel {...defaultProps} />);
    expect(
      screen.getByText(/no analytical expectations recorded yet/i),
    ).toBeInTheDocument();
  });

  it('disables Download workpaper when there are no items', () => {
    render(<AnalyticalExpectationsPanel {...defaultProps} />);
    const btn = screen.getByRole('button', { name: /download workpaper/i });
    expect(btn).toBeDisabled();
  });

  it('renders item rows with status badges', () => {
    const items = [
      makeItem({ id: 1, procedure_target_label: 'Revenue', result_status: 'not_evaluated' }),
      makeItem({
        id: 2,
        procedure_target_label: 'Cash',
        procedure_target_type: 'balance',
        result_status: 'within_threshold',
        result_actual_value: 1010,
        result_variance_amount: 10,
      }),
      makeItem({
        id: 3,
        procedure_target_label: 'Current Ratio',
        procedure_target_type: 'ratio',
        result_status: 'exceeds_threshold',
        result_actual_value: 3.5,
        result_variance_amount: 1.5,
        precision_threshold_amount: null,
        precision_threshold_percent: 5,
      }),
    ];
    render(<AnalyticalExpectationsPanel {...defaultProps} items={items} />);
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('Cash')).toBeInTheDocument();
    expect(screen.getByText('Current Ratio')).toBeInTheDocument();
    // Status labels appear in both the summary cards and in row badges; assert presence rather than uniqueness
    expect(screen.getAllByText(/not evaluated/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/within threshold/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/exceeds threshold/i).length).toBeGreaterThan(0);
  });

  it('counts items by status correctly', () => {
    const items = [
      makeItem({ id: 1, result_status: 'not_evaluated' }),
      makeItem({ id: 2, result_status: 'within_threshold' }),
      makeItem({ id: 3, result_status: 'within_threshold' }),
      makeItem({ id: 4, result_status: 'exceeds_threshold' }),
    ];
    render(<AnalyticalExpectationsPanel {...defaultProps} items={items} />);
    // Total label
    expect(screen.getByText('Total')).toBeInTheDocument();
    // The count "4" should appear next to the Total label
    const totalCard = screen.getByText('Total').parentElement;
    expect(totalCard).toHaveTextContent('4');
  });

  it('captures actual value and calls onUpdate with result_actual_value', async () => {
    const user = userEvent.setup();
    const items = [makeItem({ id: 1, result_status: 'not_evaluated' })];
    render(<AnalyticalExpectationsPanel {...defaultProps} items={items} />);

    const input = screen.getByLabelText(/actual:/i);
    await user.type(input, '1100');
    await user.click(screen.getByRole('button', { name: /capture/i }));

    await waitFor(() => {
      expect(defaultProps.onUpdate).toHaveBeenCalledWith(1, { result_actual_value: 1100 });
    });
  });

  it('clears result via Re-evaluate button', async () => {
    const user = userEvent.setup();
    const items = [
      makeItem({
        id: 1,
        result_status: 'within_threshold',
        result_actual_value: 1010,
        result_variance_amount: 10,
      }),
    ];
    render(<AnalyticalExpectationsPanel {...defaultProps} items={items} />);

    await user.click(screen.getByRole('button', { name: /re-evaluate/i }));
    await waitFor(() => {
      expect(defaultProps.onUpdate).toHaveBeenCalledWith(1, { clear_result: true });
    });
  });

  it('archives an item via Archive button', async () => {
    const user = userEvent.setup();
    const items = [makeItem({ id: 7, procedure_target_label: 'Inventory' })];
    render(<AnalyticalExpectationsPanel {...defaultProps} items={items} />);

    await user.click(screen.getByLabelText(/archive expectation inventory/i));
    await waitFor(() => {
      expect(defaultProps.onArchive).toHaveBeenCalledWith(7);
    });
  });

  it('opens create modal when + Add Expectation is clicked', async () => {
    const user = userEvent.setup();
    render(<AnalyticalExpectationsPanel {...defaultProps} />);
    await user.click(screen.getByRole('button', { name: /\+ add expectation/i }));
    expect(screen.getByText(/new analytical expectation/i)).toBeInTheDocument();
  });
});
