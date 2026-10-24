/**
 * Authorities Paciolus cites — who publishes each source and where to read it.
 *
 * Sprint 835. Every code in `METHODOLOGY_SOURCES` resolves to exactly one
 * authority here by prefix (`authorityForCode`); `test_methodology_sources.py`
 * checks that, so a newly cited source cannot appear on the Sources page
 * without an issuer and a place to read it.
 *
 * Links go to the issuer's own index page rather than deep links, which move.
 * Some sources (FASB Codification, AICPA guides) need a free or paid account.
 */

export interface Authority {
  key: string
  name: string
  /** What the issuer is, in one line. */
  description: string
  /** Where a reader can find the source. */
  url: string
  /** How to access it (free, free account, purchase). */
  access: string
  /** Code prefixes this authority owns, e.g. 'ISA ' or 'IRC §'. */
  prefixes: string[]
}

export const AUTHORITIES: Authority[] = [
  {
    key: 'pcaob',
    name: 'Public Company Accounting Oversight Board (PCAOB)',
    description: 'Sets auditing standards (AS) for audits of US public companies.',
    url: 'https://pcaobus.org/oversight/standards/auditing-standards',
    access: 'Free',
    prefixes: ['AS ', 'PCAOB '],
  },
  {
    key: 'iaasb',
    name: 'International Auditing and Assurance Standards Board (IAASB)',
    description: 'Issues the International Standards on Auditing (ISA), used in most countries outside US public-company audits.',
    url: 'https://www.iaasb.org/standards-pronouncements',
    access: 'Free (handbook download)',
    prefixes: ['ISA '],
  },
  {
    key: 'aicpa',
    name: 'American Institute of CPAs (AICPA)',
    description: 'Issues the US auditing standards for non-public entities (AU-C) and practice guides such as the Audit Sampling guide.',
    url: 'https://www.aicpa-cima.com/resources/download/aicpa-statements-on-auditing-standards-currently-effective',
    access: 'Free account for standards; guides are sold',
    prefixes: ['AU-C ', 'AICPA ', 'SOC '],
  },
  {
    key: 'fasb',
    name: 'Financial Accounting Standards Board (FASB)',
    description: 'Maintains the Accounting Standards Codification (ASC), US GAAP.',
    url: 'https://asc.fasb.org/',
    access: 'Free basic view (account required)',
    prefixes: ['ASC '],
  },
  {
    key: 'ifrs',
    name: 'IFRS Foundation / International Accounting Standards Board',
    description: 'Issues IFRS Accounting Standards (IFRS and the older IAS).',
    url: 'https://www.ifrs.org/issued-standards/list-of-standards/',
    access: 'Free account for full text',
    prefixes: ['IFRS ', 'IAS '],
  },
  {
    key: 'irs',
    name: 'Internal Revenue Service and the Internal Revenue Code',
    description: 'US federal tax law (IRC sections) and the IRS forms, instructions and publications that apply it.',
    url: 'https://www.irs.gov/forms-instructions',
    access: 'Free',
    prefixes: ['IRC ', 'Form ', 'Pub '],
  },
  {
    key: 'uscode',
    name: 'United States Code',
    description: 'Federal statutes outside the tax code, such as the federal holiday calendar.',
    url: 'https://uscode.house.gov/',
    access: 'Free',
    prefixes: ['5 U.S.C.'],
  },
  {
    key: 'coso',
    name: 'Committee of Sponsoring Organizations of the Treadway Commission (COSO)',
    description: 'Publishes the Internal Control — Integrated Framework (2013).',
    url: 'https://www.coso.org/',
    access: 'Executive summary free; framework sold',
    prefixes: ['COSO '],
  },
  {
    key: 'acfe',
    name: 'Association of Certified Fraud Examiners (ACFE)',
    description: 'Publishes the Report to the Nations, a periodic study of occupational fraud.',
    url: 'https://www.acfe.com/',
    access: 'Free',
    prefixes: ['ACFE '],
  },
  {
    key: 'literature',
    name: 'Published statistical and forensic literature',
    description:
      'Methods from books rather than standard-setters: Nigrini, Benford’s Law (Wiley, 2012); Iglewicz & Hoaglin, How to Detect and Handle Outliers (ASQC Quality Press, 1993).',
    url: '',
    access: 'Books (libraries and booksellers)',
    prefixes: ['Nigrini ', 'Iglewicz '],
  },
]

/** The authority that publishes `code`, by longest matching prefix. */
export function authorityForCode(code: string): Authority | undefined {
  let best: Authority | undefined
  let bestLen = -1
  for (const authority of AUTHORITIES) {
    for (const prefix of authority.prefixes) {
      if (code.startsWith(prefix) && prefix.length > bestLen) {
        best = authority
        bestLen = prefix.length
      }
    }
  }
  return best
}
