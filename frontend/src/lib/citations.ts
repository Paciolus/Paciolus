/**
 * Citations data for audit standards referenced across the platform.
 * Each entry provides the standard code, full name, and links to
 * both the official source and a freely accessible alternative.
 */

export interface CitationData {
  code: string
  fullName: string
  officialUrl: string
  officialNote: string
  freeUrl?: string
  freeNote?: string
}

export const CITATIONS: Record<string, CitationData> = {
  'ISA 240': {
    code: 'ISA 240',
    fullName: 'International Standard on Auditing 240 — The Auditor\u2019s Responsibilities Relating to Fraud in an Audit of Financial Statements',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-240-Revised_0.pdf',
    officialNote: 'IFAC (free PDF)',
    freeUrl: 'https://pcaobus.org/oversight/standards/auditing-standards/details/AS2401',
    freeNote: 'PCAOB AS 2401 (US equivalent, free)',
  },
  'ISA 315': {
    code: 'ISA 315',
    fullName: 'International Standard on Auditing 315 (Revised 2019) — Identifying and Assessing the Risks of Material Misstatement',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-315-Revised-2019.pdf',
    officialNote: 'IFAC (free PDF)',
  },
  'ISA 500': {
    code: 'ISA 500',
    fullName: 'International Standard on Auditing 500 — Audit Evidence',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-500-Revised_0.pdf',
    officialNote: 'IFAC (free PDF)',
  },
  'ISA 501': {
    code: 'ISA 501',
    fullName: 'International Standard on Auditing 501 — Audit Evidence: Specific Considerations for Selected Items',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-501.pdf',
    officialNote: 'IFAC (free PDF)',
  },
  'ISA 505': {
    code: 'ISA 505',
    fullName: 'International Standard on Auditing 505 — External Confirmations',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-505-Revised_0.pdf',
    officialNote: 'IFAC (free PDF)',
  },
  'ISA 520': {
    code: 'ISA 520',
    fullName: 'International Standard on Auditing 520 — Analytical Procedures',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-520.pdf',
    officialNote: 'IFAC (free PDF)',
  },
  'ISA 530': {
    code: 'ISA 530',
    fullName: 'International Standard on Auditing 530 — Audit Sampling',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-530.pdf',
    officialNote: 'IFAC (free PDF)',
    freeUrl: 'https://pcaobus.org/oversight/standards/auditing-standards/details/AS2315',
    freeNote: 'PCAOB AS 2315 (US equivalent, free)',
  },
  'ISA 540': {
    code: 'ISA 540',
    fullName: 'International Standard on Auditing 540 (Revised) — Auditing Accounting Estimates and Related Disclosures',
    officialUrl: 'https://www.ifac.org/system/files/publications/files/ISA-540-Revised_0.pdf',
    officialNote: 'IFAC (free PDF)',
  },
  'PCAOB AS 2315': {
    code: 'PCAOB AS 2315',
    fullName: 'PCAOB Auditing Standard No. 2315 — Audit Sampling',
    officialUrl: 'https://pcaobus.org/oversight/standards/auditing-standards/details/AS2315',
    officialNote: 'PCAOB (free)',
  },
  'PCAOB AS 2401': {
    code: 'PCAOB AS 2401',
    fullName: 'PCAOB Auditing Standard No. 2401 — Consideration of Fraud in a Financial Statement Audit',
    officialUrl: 'https://pcaobus.org/oversight/standards/auditing-standards/details/AS2401',
    officialNote: 'PCAOB (free)',
  },
  'ASC 606': {
    code: 'ASC 606',
    fullName: 'FASB Accounting Standards Codification Topic 606 — Revenue from Contracts with Customers',
    officialUrl: 'https://asc.fasb.org/606',
    officialNote: 'FASB (registration required)',
    freeUrl: 'https://www.iasplus.com/en-us/standards/fasb/revenue/asc606',
    freeNote: 'Deloitte IAS Plus summary (free)',
  },
  'IFRS 15': {
    code: 'IFRS 15',
    fullName: 'International Financial Reporting Standard 15 — Revenue from Contracts with Customers',
    officialUrl: 'https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/',
    officialNote: 'IFRS Foundation',
    freeUrl: 'https://www.iasplus.com/en/standards/ifrs/ifrs15',
    freeNote: 'Deloitte IAS Plus summary (free)',
  },
  'IAS 2': {
    code: 'IAS 2',
    fullName: 'International Accounting Standard 2 — Inventories',
    officialUrl: 'https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/',
    officialNote: 'IFRS Foundation',
    freeUrl: 'https://www.iasplus.com/en/standards/ias/ias2',
    freeNote: 'Deloitte IAS Plus summary (free)',
  },
  'IAS 7': {
    code: 'IAS 7',
    fullName: 'International Accounting Standard 7 — Statement of Cash Flows',
    officialUrl: 'https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/',
    officialNote: 'IFRS Foundation',
    freeUrl: 'https://www.iasplus.com/en/standards/ias/ias7',
    freeNote: 'Deloitte IAS Plus summary (free)',
  },
  'IAS 16': {
    code: 'IAS 16',
    fullName: 'International Accounting Standard 16 — Property, Plant and Equipment',
    officialUrl: 'https://www.ifrs.org/issued-standards/list-of-standards/ias-16-property-plant-and-equipment/',
    officialNote: 'IFRS Foundation',
    freeUrl: 'https://www.iasplus.com/en/standards/ias/ias16',
    freeNote: 'Deloitte IAS Plus summary (free)',
  },
  'ASC 230': {
    code: 'ASC 230',
    fullName: 'FASB Accounting Standards Codification Topic 230 — Statement of Cash Flows',
    officialUrl: 'https://asc.fasb.org/230',
    officialNote: 'FASB (registration required)',
    freeUrl: 'https://www.iasplus.com/en-us/standards/fasb/broad-transactions/asc230',
    freeNote: 'Deloitte IAS Plus summary (free)',
  },
}

/** Look up a citation by code. Returns undefined if not found. */
export function getCitation(code: string): CitationData | undefined {
  return CITATIONS[code]
}
