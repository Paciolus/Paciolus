# Phase III Implementation Guide: Advanced Diagnostic Signals
## For Backend & Frontend Engineers

**Date:** 2026-02-04
**Audience:** Backend Python engineers, Frontend TypeScript/React engineers
**Status:** Design finalized, ready for coding

---

## Part 1: Shared Data Structures

### TypeScript Types (to create in `frontend/src/types/`)

```typescript
// frontend/src/types/diagnostics.ts

/**
 * SUSPENSE ACCOUNT DETECTOR
 */
export interface SuspenseAccountAlert {
  account: string
  amount: number
  detected_type: AccountType
  confidence: number // 0-1, e.g., 0.95
  reason: string // e.g., "Account name contains 'suspense' or 'clearing'"
  is_dismissed?: boolean // Session-only flag
}

/**
 * BALANCE SHEET EQUATION VALIDATOR
 */
export interface BalanceSheetEquation {
  total_assets: number
  total_liabilities: number
  total_equity: number
  liabilities_plus_equity: number
  variance: number // Assets - (Liabilities + Equity)
  variance_percent: number // variance / total_assets * 100
  is_balanced: boolean // variance < tolerance (0.01%)
  tolerance: number // Default: 0.0001 (0.01%)
  likely_cause?: string // For significant errors
  severity: 'balanced' | 'rounding' | 'error' // Severity level
}

/**
 * CONCENTRATION RISK DETECTOR
 */
export interface ConcentrationRisk {
  category: AccountCategory // 'asset', 'liability', 'equity'
  category_total: number
  account: string
  amount: number
  percentage: number // 0-100, e.g., 44.8
  threshold_exceeded: boolean // percentage > 25
  threshold: number // Default: 25, configurable
}

export interface ConcentrationRiskSummary {
  concentration_risks: ConcentrationRisk[]
  risk_level: 'low' | 'medium' | 'high' // Based on count & severity
  total_at_risk: number // Count of accounts exceeding threshold
  has_risks: boolean // true if total_at_risk > 0
}

/**
 * ROUNDING ANOMALY SCANNER
 */
export interface RoundingAnomaly {
  account: string
  amount: number
  is_round: boolean // true if amount % 1 === 0 or very close
  confidence: number // 0-1, e.g., 0.95
  likely_cause: string // e.g., "Manual estimate", "Accrual", "Petty cash fund"
  category: AccountType
  is_flagged?: boolean // Session-only flag
  is_ignored?: boolean // Session-only flag
}

export interface RoundingAnomalySummary {
  rounding_anomalies: RoundingAnomaly[]
  threshold: number // Default: 0.90 (90% confidence)
  total_detected: number
}

/**
 * CONTRA-ACCOUNT VALIDATOR
 */
export interface ContraAccountRelationship {
  primary_account: string
  contra_account: string
  primary_amount: number
  contra_amount: number
  ratio: number // Decimal, e.g., 0.30 for 30%
  ratio_label: string // e.g., "Depreciation Ratio"
  health_status: 'normal' | 'unusual' | 'critical'
  typical_range: [number, number] // [min%, max%], e.g., [0.20, 0.40]
  recommendation: string // Explanation of health status
  industry_context?: string // Optional: manufacturing, retail, etc.
}

export interface ContraAccountValidationSummary {
  contra_account_relationships: ContraAccountRelationship[]
  total_validated: number
  total_normal: number
  total_unusual: number
  total_critical: number
}

/**
 * COMPLETE DIAGNOSTIC RESPONSE
 * (Extends existing AuditResult)
 */
export interface AuditResult {
  // ... existing fields ...
  anomalies: AbnormalBalanceExtended[]
  analytics: Analytics

  // NEW FIELDS (Phase III)
  suspense_accounts?: SuspenseAccountAlert[]
  balance_sheet_equation?: BalanceSheetEquation
  concentration_risks?: ConcentrationRiskSummary
  rounding_anomalies?: RoundingAnomalySummary
  contra_accounts?: ContraAccountValidationSummary
}
```

---

## Part 2: Backend Implementation Details

### Python Models (to create in `backend/models.py`)

```python
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class RiskSeverity(str, Enum):
    """New severity classification"""
    BALANCED = "balanced"
    ROUNDING = "rounding"
    UNUSUAL = "unusual"
    CRITICAL = "critical"
    ERROR = "error"

@dataclass
class SuspenseAccountAlert:
    """Sprint 40: Suspense Account Detection"""
    account: str
    amount: float
    detected_type: str
    confidence: float  # 0-1
    reason: str

    def to_dict(self):
        return {
            'account': self.account,
            'amount': self.amount,
            'detected_type': self.detected_type,
            'confidence': self.confidence,
            'reason': self.reason
        }

@dataclass
class BalanceSheetEquation:
    """Sprint 41: A = L + E Validator"""
    total_assets: float
    total_liabilities: float
    total_equity: float
    liabilities_plus_equity: float
    variance: float
    variance_percent: float
    is_balanced: bool
    tolerance: float = 0.0001  # 0.01% tolerance
    likely_cause: Optional[str] = None
    severity: str = "balanced"  # balanced|rounding|error

    def to_dict(self):
        return {
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'total_equity': self.total_equity,
            'liabilities_plus_equity': self.liabilities_plus_equity,
            'variance': self.variance,
            'variance_percent': self.variance_percent,
            'is_balanced': self.is_balanced,
            'severity': self.severity,
            'likely_cause': self.likely_cause
        }

@dataclass
class ConcentrationRisk:
    """Sprint 42: Asset/Liability Concentration Detection"""
    category: str  # asset|liability|equity|revenue
    category_total: float
    account: str
    amount: float
    percentage: float  # 0-100
    threshold_exceeded: bool
    threshold: float = 25.0  # Configurable, default 25%

    def to_dict(self):
        return {
            'category': self.category,
            'category_total': self.category_total,
            'account': self.account,
            'amount': self.amount,
            'percentage': self.percentage,
            'threshold_exceeded': self.threshold_exceeded
        }

@dataclass
class RoundingAnomaly:
    """Sprint 42: Rounding Anomaly Scanner"""
    account: str
    amount: float
    is_round: bool
    confidence: float  # 0-1, must be > 0.90 to flag
    likely_cause: str
    category: str

    def to_dict(self):
        return {
            'account': self.account,
            'amount': self.amount,
            'is_round': self.is_round,
            'confidence': self.confidence,
            'likely_cause': self.likely_cause,
            'category': self.category
        }

@dataclass
class ContraAccountRelationship:
    """Sprint 43: Contra-Account Validation"""
    primary_account: str
    contra_account: str
    primary_amount: float
    contra_amount: float
    ratio: float  # Decimal, e.g., 0.30
    ratio_label: str
    health_status: str  # normal|unusual|critical
    typical_range: tuple  # (min, max), e.g., (0.20, 0.40)
    recommendation: str
    industry_context: Optional[str] = None

    def to_dict(self):
        return {
            'primary_account': self.primary_account,
            'contra_account': self.contra_account,
            'primary_amount': self.primary_amount,
            'contra_amount': self.contra_amount,
            'ratio': self.ratio,
            'ratio_label': self.ratio_label,
            'health_status': self.health_status,
            'typical_range': self.typical_range,
            'recommendation': self.recommendation
        }
```

### Python Detection Algorithms (to create in `backend/advanced_detectors.py`)

```python
"""
advanced_detectors.py - Phase III diagnostic signal detectors

Each detector is Zero-Storage compliant:
- No financial data is stored
- Session-only analysis
- Results passed to frontend for user review
"""

from typing import List, Dict, Tuple, Optional
import re
from classification_rules import CLASSIFICATION_KEYWORDS
from models import (
    SuspenseAccountAlert, BalanceSheetEquation, ConcentrationRisk,
    RoundingAnomaly, ContraAccountRelationship
)

class SuspenseAccountDetector:
    """
    Sprint 40: Detect accounts intended to be temporary/clearing

    Rule: Account name contains keywords like "suspense", "clearing",
    "temporary", "holding", "contra" but has a non-zero balance
    """

    SUSPENSE_KEYWORDS = {
        'suspense', 'clearing', 'temporary', 'holding',
        'contra', 'pending', 'transit', 'standby',
        'placeholder', 'undefined'
    }

    @classmethod
    def detect(cls, trial_balance: List[Dict]) -> List[SuspenseAccountAlert]:
        """
        Scan trial balance for suspense accounts with balances.

        Args:
            trial_balance: List of {account_name, debit, credit, balance}

        Returns:
            List of SuspenseAccountAlert objects
        """
        alerts = []

        for row in trial_balance:
            account = row.get('account_name', '').lower()
            balance = row.get('balance', 0)

            # Skip zero-balance accounts (they're OK)
            if balance == 0:
                continue

            # Check if account name matches suspense keywords
            for keyword in cls.SUSPENSE_KEYWORDS:
                if keyword in account:
                    confidence = cls._calculate_confidence(account, keyword)

                    alerts.append(SuspenseAccountAlert(
                        account=row.get('account_name'),
                        amount=abs(balance),
                        detected_type='unknown',  # Will be enriched by classification
                        confidence=confidence,
                        reason=f"Account name contains '{keyword}' but carries balance"
                    ))
                    break  # Only one alert per account

        return alerts

    @classmethod
    def _calculate_confidence(cls, account_name: str, keyword: str) -> float:
        """Calculate confidence 0-1 based on keyword position and prevalence"""
        # Exact match: 0.99
        if account_name == keyword:
            return 0.99
        # Starts with keyword: 0.95
        if account_name.startswith(keyword):
            return 0.95
        # Contains keyword: 0.85
        if keyword in account_name:
            return 0.85
        return 0.70


class BalanceSheetEquationValidator:
    """
    Sprint 41: Validate Assets = Liabilities + Equity

    Tolerance: 0.01% variance (accounting for rounding)
    """

    TOLERANCE = 0.0001  # 0.01%

    @classmethod
    def validate(
        cls,
        trial_balance: List[Dict],
        category_totals: Dict[str, float]
    ) -> BalanceSheetEquation:
        """
        Validate balance sheet equation.

        Args:
            trial_balance: List of {account_name, category, balance}
            category_totals: {total_assets, total_liabilities, total_equity}

        Returns:
            BalanceSheetEquation with detailed variance analysis
        """
        total_assets = category_totals.get('total_assets', 0)
        total_liabilities = category_totals.get('total_liabilities', 0)
        total_equity = category_totals.get('total_equity', 0)

        liabilities_plus_equity = total_liabilities + total_equity
        variance = total_assets - liabilities_plus_equity

        # Calculate variance percentage
        if total_assets != 0:
            variance_percent = (variance / total_assets) * 100
        else:
            variance_percent = 0

        # Determine severity
        abs_variance_percent = abs(variance_percent)
        if abs_variance_percent < 0.01:  # Within tolerance
            severity = 'balanced'
            is_balanced = True
            likely_cause = None
        elif abs_variance_percent < 1.0:
            severity = 'rounding'
            is_balanced = True
            likely_cause = "Rounding variance within 1%"
        else:
            severity = 'error'
            is_balanced = False
            likely_cause = cls._diagnose_error(
                total_assets, total_liabilities, total_equity
            )

        return BalanceSheetEquation(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            liabilities_plus_equity=liabilities_plus_equity,
            variance=variance,
            variance_percent=variance_percent,
            is_balanced=is_balanced,
            severity=severity,
            likely_cause=likely_cause
        )

    @classmethod
    def _diagnose_error(cls, assets: float, liab: float, equity: float) -> str:
        """Generate diagnostic message for balance sheet errors"""
        if assets > (liab + equity):
            return "Assets exceed liabilities + equity: Missing liability or hidden obligation"
        else:
            return "Liabilities + equity exceed assets: Possible missing equity account or over-valued liability"


class ConcentrationRiskDetector:
    """
    Sprint 42: Detect account concentration risk (>25% of category)

    Warning: When a single account dominates category totals,
    indicating concentration risk (e.g., 45% of assets in AR)
    """

    DEFAULT_THRESHOLD = 0.25  # 25%

    @classmethod
    def detect(
        cls,
        trial_balance: List[Dict],
        category_totals: Dict[str, float]
    ) -> List[ConcentrationRisk]:
        """
        Scan for accounts exceeding concentration threshold.

        Args:
            trial_balance: List of {account_name, category, balance}
            category_totals: {total_assets, total_liabilities, etc}

        Returns:
            List of ConcentrationRisk objects
        """
        risks = []
        threshold = cls.DEFAULT_THRESHOLD

        # Group by category
        by_category = {}
        for row in trial_balance:
            category = row.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(row)

        # Check each category
        for category, accounts in by_category.items():
            category_total = category_totals.get(f'total_{category}', 0)

            if category_total == 0:
                continue

            for account in accounts:
                amount = abs(account.get('balance', 0))
                percentage = (amount / category_total) * 100

                if percentage > (threshold * 100):
                    risks.append(ConcentrationRisk(
                        category=category,
                        category_total=category_total,
                        account=account.get('account_name'),
                        amount=amount,
                        percentage=percentage,
                        threshold_exceeded=True,
                        threshold=threshold * 100
                    ))

        return risks


class RoundingAnomalyScanner:
    """
    Sprint 42: Detect suspiciously round figures (e.g., $5,000.00)

    Confidence scoring based on:
    1. Account type (accruals more likely to be round)
    2. Amount size ($1,000+)
    3. Percent of category total
    """

    MIN_AMOUNT_TO_FLAG = 1000  # Don't flag < $1,000
    CONFIDENCE_THRESHOLD = 0.90  # Only flag if 90%+ confidence

    # Account types where rounding is NORMAL (low confidence)
    TYPICALLY_ROUND_ACCOUNTS = {
        'petty_cash', 'sales_discounts', 'cash_short_over',
        'rounding_variance', 'miscellaneous_expense'
    }

    # Account types where rounding is SUSPICIOUS (high confidence)
    TYPICALLY_PRECISE_ACCOUNTS = {
        'accounts_receivable', 'inventory', 'equipment',
        'accounts_payable', 'expense'
    }

    @classmethod
    def scan(cls, trial_balance: List[Dict]) -> List[RoundingAnomaly]:
        """
        Scan for round-figure anomalies.

        Args:
            trial_balance: List of {account_name, category, balance}

        Returns:
            List of RoundingAnomaly objects (confidence >= threshold)
        """
        anomalies = []

        for row in trial_balance:
            account = row.get('account_name', '')
            amount = abs(row.get('balance', 0))
            category = row.get('category', 'unknown')

            # Skip small amounts
            if amount < cls.MIN_AMOUNT_TO_FLAG:
                continue

            # Check if amount is "round" (no cents, or very close)
            is_round = cls._is_round_number(amount)

            if not is_round:
                continue

            # Calculate confidence
            confidence = cls._calculate_confidence(account, category, amount)

            if confidence >= cls.CONFIDENCE_THRESHOLD:
                anomalies.append(RoundingAnomaly(
                    account=account,
                    amount=amount,
                    is_round=True,
                    confidence=confidence,
                    likely_cause=cls._get_cause(account, category),
                    category=category
                ))

        return anomalies

    @classmethod
    def _is_round_number(cls, amount: float, tolerance: float = 0.01) -> bool:
        """Check if amount is suspiciously round"""
        decimal_part = amount - int(amount)
        return decimal_part < tolerance or (1 - decimal_part) < tolerance

    @classmethod
    def _calculate_confidence(cls, account: str, category: str, amount: float) -> float:
        """Score confidence 0-1 based on account type and amount"""
        base_confidence = 0.80

        # Boost for typically-precise accounts
        if any(kw in account.lower() for kw in cls.TYPICALLY_PRECISE_ACCOUNTS):
            base_confidence = 0.95

        # Reduce for typically-round accounts
        if any(kw in account.lower() for kw in cls.TYPICALLY_ROUND_ACCOUNTS):
            base_confidence = 0.40

        # Boost for specific accrual patterns
        if 'accrual' in account.lower() or 'expense' in category.lower():
            base_confidence = min(0.98, base_confidence + 0.05)

        return min(0.99, base_confidence)

    @classmethod
    def _get_cause(cls, account: str, category: str) -> str:
        """Generate likely cause explanation"""
        account_lower = account.lower()

        if 'petty' in account_lower or 'cash' in account_lower:
            return "Petty cash fund or round cash balance"
        elif 'accrual' in account_lower or 'accrued' in account_lower:
            return "Manual accrual estimate (not system-calculated)"
        elif 'deferred' in account_lower or 'prepaid' in account_lower:
            return "Revenue/expense deferral, typically estimated"
        elif 'allowance' in account_lower or 'reserve' in account_lower:
            return "Valuation allowance or reserve estimate"
        else:
            return "Manual estimate or system rounding"


class ContraAccountValidator:
    """
    Sprint 43: Validate depreciation and allowance relationships

    Rules:
    - Equipment > Accumulated Depreciation (20-40% range)
    - Inventory > Allowance for Obsolescence (3-8% range)
    - Accounts Receivable > Allowance for Doubtful (2-5% range)
    """

    # Define known contra-account pairs and their typical ranges
    KNOWN_RELATIONSHIPS = {
        ('equipment', 'accumulated depreciation'): {
            'ratio_label': 'Depreciation Ratio',
            'typical_range': (0.20, 0.40),
            'formula': 'Accumulated Depreciation / Equipment'
        },
        ('fixed assets', 'accumulated depreciation'): {
            'ratio_label': 'Depreciation Ratio',
            'typical_range': (0.15, 0.35),
            'formula': 'Accumulated Depreciation / Fixed Assets'
        },
        ('inventory', 'allowance for obsolescence'): {
            'ratio_label': 'Obsolescence Reserve Ratio',
            'typical_range': (0.03, 0.08),
            'formula': 'Allowance for Obsolescence / Inventory'
        },
        ('accounts receivable', 'allowance for doubtful accounts'): {
            'ratio_label': 'AR Reserve Ratio',
            'typical_range': (0.02, 0.05),
            'formula': 'Allowance for Doubtful / AR'
        }
    }

    @classmethod
    def validate(cls, trial_balance: List[Dict]) -> List[ContraAccountRelationship]:
        """
        Validate contra-account relationships.

        Args:
            trial_balance: List of {account_name, balance}

        Returns:
            List of ContraAccountRelationship validations
        """
        relationships = []
        accounts_by_name = {
            r.get('account_name', '').lower(): r
            for r in trial_balance
        }

        for (primary_kw, contra_kw), config in cls.KNOWN_RELATIONSHIPS.items():
            # Try to find matching accounts
            primary = cls._find_account(accounts_by_name, primary_kw)
            contra = cls._find_account(accounts_by_name, contra_kw)

            if primary and contra:
                primary_amt = abs(primary.get('balance', 0))
                contra_amt = abs(contra.get('balance', 0))

                if primary_amt == 0:
                    continue  # Skip if no primary account balance

                ratio = contra_amt / primary_amt if primary_amt != 0 else 0
                min_ratio, max_ratio = config['typical_range']

                # Determine health
                if min_ratio <= ratio <= max_ratio:
                    health = 'normal'
                    recommendation = f"Within typical range ({min_ratio*100:.0f}-{max_ratio*100:.0f}%)"
                elif ratio < min_ratio:
                    health = 'unusual'
                    recommendation = f"Lower than typical ({ratio*100:.1f}% vs {min_ratio*100:.0f}-{max_ratio*100:.0f}% expected)"
                else:
                    health = 'critical'
                    recommendation = f"Higher than typical ({ratio*100:.1f}% vs {min_ratio*100:.0f}-{max_ratio*100:.0f}% expected)"

                relationships.append(ContraAccountRelationship(
                    primary_account=primary.get('account_name'),
                    contra_account=contra.get('account_name'),
                    primary_amount=primary_amt,
                    contra_amount=contra_amt,
                    ratio=ratio,
                    ratio_label=config['ratio_label'],
                    health_status=health,
                    typical_range=config['typical_range'],
                    recommendation=recommendation
                ))

        return relationships

    @classmethod
    def _find_account(cls, accounts_dict: Dict[str, Dict], keyword: str) -> Optional[Dict]:
        """Find account by keyword fuzzy match (case-insensitive)"""
        keyword_lower = keyword.lower()
        for account_name, row in accounts_dict.items():
            if keyword_lower in account_name:
                return row
        return None
```

### API Endpoint (to add in `backend/main.py`)

```python
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from advanced_detectors import (
    SuspenseAccountDetector, BalanceSheetEquationValidator,
    ConcentrationRiskDetector, RoundingAnomalyScanner,
    ContraAccountValidator
)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

@router.post("/advanced-signals")
async def run_advanced_diagnostics(
    file: UploadFile = File(...),
    materiality: float = 0,
    user_id: str = Depends(get_current_user)
) -> dict:
    """
    Sprint 40-43: Run all Phase III diagnostic signals

    Zero-Storage: Results computed in-memory, never stored.
    User can export to PDF/Excel for offline review.
    """

    try:
        # Parse file (CSV or Excel)
        trial_balance = await parse_trial_balance(file)
        category_totals = compute_category_totals(trial_balance)

        # Run all detectors
        suspense_alerts = SuspenseAccountDetector.detect(trial_balance)
        equation = BalanceSheetEquationValidator.validate(
            trial_balance, category_totals
        )
        concentration_risks = ConcentrationRiskDetector.detect(
            trial_balance, category_totals
        )
        rounding_anomalies = RoundingAnomalyScanner.scan(trial_balance)
        contra_accounts = ContraAccountValidator.validate(trial_balance)

        return {
            'status': 'success',
            'suspense_accounts': [a.to_dict() for a in suspense_alerts],
            'balance_sheet_equation': equation.to_dict(),
            'concentration_risks': {
                'risks': [r.to_dict() for r in concentration_risks],
                'total_at_risk': len([r for r in concentration_risks if r.threshold_exceeded]),
                'risk_level': cls._assess_risk_level(concentration_risks)
            },
            'rounding_anomalies': {
                'anomalies': [a.to_dict() for a in rounding_anomalies],
                'total_detected': len(rounding_anomalies)
            },
            'contra_accounts': {
                'relationships': [c.to_dict() for c in contra_accounts],
                'total_normal': len([c for c in contra_accounts if c.health_status == 'normal']),
                'total_unusual': len([c for c in contra_accounts if c.health_status == 'unusual']),
                'total_critical': len([c for c in contra_accounts if c.health_status == 'critical'])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Part 3: Frontend Component Implementation

### Suspense Account Alert Component

```tsx
// frontend/src/components/risk/SuspenseAccountAlert.tsx

'use client'

import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import type { SuspenseAccountAlert, AccountType } from '@/types/mapping'
import { AccountTypeDropdown } from '@/components/mapping'

interface SuspenseAccountAlertProps {
  alert: SuspenseAccountAlert
  disabled?: boolean
  onDismiss: (accountName: string) => void
  onReassign: (accountName: string, newType: AccountType) => void
}

export function SuspenseAccountAlert({
  alert,
  disabled = false,
  onDismiss,
  onReassign,
}: SuspenseAccountAlertProps) {
  const [archived, setArchived] = useState(false)

  const cardVariants = {
    hidden: { opacity: 0, x: -20, scale: 0.95 },
    visible: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 25,
        delay: 0.1,
      },
    },
  }

  if (archived) return null

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="rounded-lg overflow-hidden
                 bg-obsidian-800/40
                 border border-obsidian-600/50
                 border-l-4 border-l-clay-500"
    >
      <div className="p-4 relative">
        {/* Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-clay-400 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <h3 className="font-serif font-semibold text-oatmeal-200">
              Suspense Account Detected
            </h3>
          </div>
          <button
            onClick={() => onDismiss(alert.account)}
            className="text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Account Details */}
        <div className="space-y-2 text-sm font-sans text-oatmeal-400 mb-3">
          <div>
            Account:{' '}
            <span className="text-oatmeal-200 font-medium">{alert.account}</span>
          </div>
          <div>
            Amount:{' '}
            <span className="font-mono text-oatmeal-200">
              ${alert.amount.toLocaleString()}
            </span>
          </div>
          <div>
            Confidence:{' '}
            <span className="text-oatmeal-300">
              {Math.round(alert.confidence * 100)}%
            </span>
          </div>
        </div>

        {/* Issue Description */}
        <div className="bg-obsidian-700/30 rounded px-3 py-2 mb-3">
          <p className="text-xs text-oatmeal-500 font-sans">
            ⚠️ This account typically carries NO balance at period end. It should
            be cleared or reclassified before closing.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 flex-wrap">
          <AccountTypeDropdown
            accountName={alert.account}
            currentType="unknown"
            isManual={false}
            disabled={disabled}
            onChange={(newType) => onReassign(alert.account, newType)}
          />
          <button
            onClick={() => setArchived(true)}
            disabled={disabled}
            className="px-3 py-2 text-xs font-sans bg-obsidian-700
                       hover:bg-obsidian-600 border border-obsidian-600
                       text-oatmeal-400 hover:text-oatmeal-300
                       rounded transition-all disabled:opacity-50"
          >
            Archive
          </button>
          <button
            onClick={() => onDismiss(alert.account)}
            disabled={disabled}
            className="px-3 py-2 text-xs font-sans bg-obsidian-700
                       hover:bg-obsidian-600 border border-obsidian-600
                       text-oatmeal-400 hover:text-oatmeal-300
                       rounded transition-all disabled:opacity-50"
          >
            Ignore for Session
          </button>
        </div>
      </div>
    </motion.div>
  )
}
```

### Balance Sheet Equation Component

```tsx
// frontend/src/components/analytics/BalanceSheetEquation.tsx

'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import type { BalanceSheetEquation } from '@/types/diagnostics'

interface BalanceSheetEquationProps {
  equation: BalanceSheetEquation
}

export function BalanceSheetEquation({ equation }: BalanceSheetEquationProps) {
  const [showDetails, setShowDetails] = useState(equation.severity !== 'balanced')

  if (equation.severity === 'balanced') {
    // Success state: badge only
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="inline-flex items-center gap-2 px-3 py-1.5
                   bg-sage-500/10 border border-sage-500/30
                   rounded-full text-sage-300 text-sm font-sans"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
        <span>Balance Sheet Balanced | A = L + E</span>
      </motion.div>
    )
  }

  // Warning or Error state: expandable card
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className={`rounded-lg overflow-hidden border
                  ${equation.severity === 'error'
                    ? 'border-l-4 border-l-clay-500 bg-obsidian-800/40'
                    : 'border-oatmeal-500/30 bg-obsidian-800/20'
                  }`}
    >
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full p-4 flex items-center justify-between
                   hover:bg-obsidian-700/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          {equation.severity === 'error' ? (
            <svg className="w-5 h-5 text-clay-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-oatmeal-400" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          )}
          <span className={`font-sans font-medium ${
            equation.severity === 'error' ? 'text-oatmeal-200' : 'text-oatmeal-300'
          }`}>
            Balance Sheet Equation — {equation.variance_percent < 0 ? 'Assets Short' : 'Equity Short'}
          </span>
        </div>
        <motion.svg
          animate={{ rotate: showDetails ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="w-5 h-5 text-oatmeal-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </button>

      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden border-t border-obsidian-600/30"
          >
            <div className="p-4 space-y-3 text-sm font-sans">
              {/* Equation Display */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-oatmeal-500 text-xs mb-1 block">Total Assets</label>
                  <div className="font-mono text-lg text-oatmeal-200">
                    ${equation.total_assets.toLocaleString()}
                  </div>
                </div>
                <div>
                  <label className="text-oatmeal-500 text-xs mb-1 block">Liab + Equity</label>
                  <div className="font-mono text-lg text-oatmeal-200">
                    ${equation.liabilities_plus_equity.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Variance */}
              <div className={`p-3 rounded ${
                equation.severity === 'error' ? 'bg-clay-500/10' : 'bg-oatmeal-500/10'
              }`}>
                <div className="flex justify-between items-center mb-1">
                  <span className={equation.severity === 'error' ? 'text-clay-400' : 'text-oatmeal-400'}>
                    Variance:
                  </span>
                  <span className={`font-mono font-bold ${
                    equation.severity === 'error' ? 'text-clay-300' : 'text-oatmeal-300'
                  }`}>
                    {equation.variance < 0 ? '-' : '+'}${Math.abs(equation.variance).toLocaleString()}
                  </span>
                </div>
                <div className="text-xs text-oatmeal-500">
                  {Math.abs(equation.variance_percent).toFixed(4)}% deviation
                </div>
              </div>

              {/* Likely Cause */}
              {equation.likely_cause && (
                <div className="p-3 bg-obsidian-700/30 rounded text-xs text-oatmeal-400">
                  <strong className="text-oatmeal-300">Likely Cause:</strong> {equation.likely_cause}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <button className="text-xs px-3 py-2 bg-obsidian-700 hover:bg-obsidian-600
                                 border border-obsidian-600 text-oatmeal-400 rounded
                                 transition-colors">
                  Review Trial Balance
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
```

---

## Part 4: Testing Strategy

### Backend Test Template (pytest)

```python
# backend/tests/test_advanced_detectors.py

import pytest
from advanced_detectors import (
    SuspenseAccountDetector,
    BalanceSheetEquationValidator,
    ConcentrationRiskDetector,
    RoundingAnomalyScanner,
    ContraAccountValidator
)

class TestSuspenseAccountDetector:
    def test_detects_suspense_with_balance(self):
        tb = [
            {'account_name': 'Suspense - Clearing', 'balance': 5000, 'category': 'asset'}
        ]
        alerts = SuspenseAccountDetector.detect(tb)
        assert len(alerts) == 1
        assert alerts[0].account == 'Suspense - Clearing'
        assert alerts[0].confidence >= 0.90

    def test_ignores_suspense_with_zero_balance(self):
        tb = [
            {'account_name': 'Suspense - Clearing', 'balance': 0, 'category': 'asset'}
        ]
        alerts = SuspenseAccountDetector.detect(tb)
        assert len(alerts) == 0

# ... more tests ...
```

### Frontend Component Test Template (Vitest + React Testing Library)

```tsx
// frontend/src/components/risk/__tests__/SuspenseAccountAlert.test.tsx

import { render, screen, fireEvent } from '@testing-library/react'
import { SuspenseAccountAlert } from '../SuspenseAccountAlert'

describe('SuspenseAccountAlert', () => {
  it('renders alert with account details', () => {
    const alert = {
      account: 'Suspense',
      amount: 5000,
      detected_type: 'asset',
      confidence: 0.95,
      reason: 'Test reason'
    }

    render(
      <SuspenseAccountAlert
        alert={alert}
        onDismiss={() => {}}
        onReassign={() => {}}
      />
    )

    expect(screen.getByText('Suspense Account Detected')).toBeInTheDocument()
    expect(screen.getByText(/Suspense/)).toBeInTheDocument()
    expect(screen.getByText(/5000/)).toBeInTheDocument()
  })

  it('calls onDismiss when close button clicked', () => {
    const onDismiss = jest.fn()
    const alert = { /* ... */ }

    render(
      <SuspenseAccountAlert
        alert={alert}
        onDismiss={onDismiss}
        onReassign={() => {}}
      />
    )

    fireEvent.click(screen.getByText('✕'))
    expect(onDismiss).toHaveBeenCalled()
  })
})
```

---

## Part 5: Zero-Storage Compliance Checklist

Before shipping each feature:

- [ ] **No Financial Data Stored:** Audit scores, anomalies, balances computed in-memory only
- [ ] **Session-Only State:** Dismissed items, user edits stored in React state (not DB)
- [ ] **Export-First:** Users can save results to PDF/Excel, not persisted in app
- [ ] **No User ID Linkage:** Results not associated with user profile (GDPR compliant)
- [ ] **No Caching:** Detectors re-run each upload, no historical caching of results

**Reference:** `CLAUDE.md` → "Zero-Storage trial balance analysis"

---

## Part 6: Deployment Checklist

### Pre-Release Steps

- [ ] All 5 detectors integrated into `/diagnostics/advanced-signals` endpoint
- [ ] TypeScript types exported from `frontend/src/types/diagnostics.ts`
- [ ] React components created and integrated into RiskDashboard + KeyMetricsSection
- [ ] Backend tests pass: `pytest backend/tests/test_advanced_detectors.py`
- [ ] Frontend tests pass: `npm run test` in frontend/
- [ ] Design validation: All components match UI_DESIGN_SPEC_PHASE_III.md
- [ ] Accessibility: WCAG AA color contrast verified, keyboard navigation tested
- [ ] Mobile responsiveness: Tested at 375px, 768px, 1024px+ breakpoints
- [ ] Frontend build: `npm run build` passes without errors
- [ ] PDF/Excel export includes new signals (if applicable)

### Release Notes Template

```markdown
## Phase III Advanced Diagnostic Signals (Sprint 40-43)

### New Features

1. **Suspense Account Detector** — Flags temporary/clearing accounts with balances
2. **Balance Sheet Equation Validator** — Verifies A = L + E with variance analysis
3. **Concentration Risk Detector** — Shows accounts dominating category totals (>25%)
4. **Rounding Anomaly Scanner** — Detects suspiciously round figures
5. **Contra-Account Validator** — Validates depreciation and allowance ratios

### Design
- All features follow Oat & Obsidian theme (clay-red left borders, Premium Restraint)
- Integrated into existing RiskDashboard and KeyMetricsSection
- Animated entrance with 40-50ms stagger pattern
- Collapsible sections for investigative signals

### Data Handling
- Zero-Storage compliant: All analysis computed in-memory
- Session-only storage for user edits (e.g., dismissed items)
- Results exportable to PDF and Excel workpapers

### Testing
- 50+ backend unit tests
- 20+ frontend component tests
- Full accessibility compliance (WCAG AA)
- Mobile-responsive across all breakpoints
```

---

**Implementation Status:** Ready for Backend & Frontend Engineers
**Last Updated:** 2026-02-04
**Owner:** Fintech Designer + Backend Lead
**Next Step:** Sprint 40 Task Kickoff
