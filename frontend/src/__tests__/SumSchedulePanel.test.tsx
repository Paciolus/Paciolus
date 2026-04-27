/**
 * Sprint 729b — SumSchedulePanel component tests.
 */
import userEvent from '@testing-library/user-event';
import { SumSchedulePanel } from '@/components/engagement/SumSchedulePanel';
import type {
  UncorrectedMisstatement,
  SumScheduleResponse,
} from '@/types/uncorrected-misstatements';
import { render, screen, waitFor, within } from '@/test-utils';

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

const item = (overrides: Partial<UncorrectedMisstatement> = {}): UncorrectedMisstatement => ({
  id: 1,
  engagement_id: 1,
  source_type: 'known_error',
  source_reference: 'Cutoff at YE',
  description: 'Dec 31 revenue posted to January',
  accounts_affected: [{ account: 'Revenue', debit_credit: 'CR', amount: 10000 }],
  classification: 'factual',
  fs_impact_net_income: -10000,
  fs_impact_net_assets: -10000,
  cpa_disposition: 'not_yet_reviewed',
  cpa_notes: null,
  created_by: 1,
  created_at: '2026-04-26T00:00:00Z',
  updated_by: null,
  updated_at: '2026-04-26T00:00:00Z',
  ...overrides,
});

function makeSchedule(
  overrides: Partial<SumScheduleResponse> = {},
): SumScheduleResponse {
  return {
    engagement_id: 1,
    items: [],
    subtotals: {
      factual_judgmental_net_income: 0,
      factual_judgmental_net_assets: 0,
      projected_net_income: 0,
      projected_net_assets: 0,
    },
    aggregate: { net_income: 0, net_assets: 0, driver: 0 },
    materiality: { overall: 100000, performance: 75000, trivial: 5000 },
    bucket: 'clearly_trivial',
    unreviewed_count: 0,
    ...overrides,
  };
}

const defaultProps = {
  engagementId: 1,
  schedule: null as SumScheduleResponse | null,
  isLoading: false,
  onCreate: jest.fn(),
  onUpdate: jest.fn(),
  onArchive: jest.fn(),
  onDownload: jest.fn(),
};

describe('SumSchedulePanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    defaultProps.onCreate.mockResolvedValue(null);
    defaultProps.onUpdate.mockResolvedValue(null);
    defaultProps.onArchive.mockResolvedValue(true);
    defaultProps.onDownload.mockResolvedValue(undefined);
  });

  it('renders empty state when no schedule + no items', () => {
    render(<SumSchedulePanel {...defaultProps} />);
    expect(
      screen.getByText(/no uncorrected misstatements recorded yet/i),
    ).toBeInTheDocument();
  });

  it('renders bucket box with the correct bucket label', () => {
    const schedule = makeSchedule({ bucket: 'approaching_material' });
    render(<SumSchedulePanel {...defaultProps} schedule={schedule} />);
    const box = screen.getByTestId('sum-bucket-box');
    expect(within(box).getByText(/approaching material/i)).toBeInTheDocument();
  });

  it('shows MATERIAL warning when aggregate is in MATERIAL bucket', () => {
    const schedule = makeSchedule({
      bucket: 'material',
      aggregate: { net_income: -200000, net_assets: -200000, driver: 200000 },
    });
    render(<SumSchedulePanel {...defaultProps} schedule={schedule} />);
    expect(
      screen.getByText(/aggregate exceeds overall materiality/i),
    ).toBeInTheDocument();
  });

  it('renders item rows', () => {
    const schedule = makeSchedule({
      items: [
        item({ id: 1, classification: 'factual', description: 'Revenue cutoff' }),
        item({
          id: 2,
          classification: 'projected',
          source_type: 'sample_projection',
          description: 'Inventory pricing extrapolation',
        }),
      ],
    });
    render(<SumSchedulePanel {...defaultProps} schedule={schedule} />);
    expect(screen.getByText('Revenue cutoff')).toBeInTheDocument();
    expect(screen.getByText('Inventory pricing extrapolation')).toBeInTheDocument();
  });

  it('updates disposition when select changes', async () => {
    const user = userEvent.setup();
    const schedule = makeSchedule({ items: [item({ id: 5 })] });
    render(<SumSchedulePanel {...defaultProps} schedule={schedule} />);

    const select = screen.getByLabelText(/disposition:/i);
    await user.selectOptions(select, 'auditor_accepts_as_immaterial');

    await waitFor(() => {
      expect(defaultProps.onUpdate).toHaveBeenCalledWith(5, {
        cpa_disposition: 'auditor_accepts_as_immaterial',
      });
    });
  });

  it('archives item via Archive button', async () => {
    const user = userEvent.setup();
    const schedule = makeSchedule({ items: [item({ id: 11 })] });
    render(<SumSchedulePanel {...defaultProps} schedule={schedule} />);

    await user.click(screen.getByLabelText(/archive misstatement 11/i));
    await waitFor(() => {
      expect(defaultProps.onArchive).toHaveBeenCalledWith(11);
    });
  });

  it('opens create modal', async () => {
    const user = userEvent.setup();
    render(<SumSchedulePanel {...defaultProps} />);
    await user.click(screen.getByRole('button', { name: /\+ add misstatement/i }));
    expect(screen.getByText(/^new misstatement$/i)).toBeInTheDocument();
  });

  it('disables Download workpaper when no items', () => {
    render(<SumSchedulePanel {...defaultProps} />);
    expect(screen.getByRole('button', { name: /download workpaper/i })).toBeDisabled();
  });
});
