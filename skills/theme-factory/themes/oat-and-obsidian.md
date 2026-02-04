# Oat & Obsidian Theme

> **Brand Identity for Paciolus** — A professional accounting webapp theme that balances warmth with precision.

---

## Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| **Obsidian** | `#212121` | Primary text, headers, dark mode backgrounds |
| **Oatmeal** | `#EBE9E4` | Light backgrounds, secondary surfaces |
| **Clay Red** | `#BC4749` | Expenses, alerts, errors, abnormal balances |
| **Sage Green** | `#4A7C59` | Income, success states, positive indicators |

### Extended Palette (Generated)

**Obsidian Scale:**
- obsidian-50: #f5f5f5
- obsidian-100: #e0e0e0
- obsidian-200: #bdbdbd
- obsidian-300: #9e9e9e
- obsidian-400: #757575
- obsidian-500: #616161
- obsidian-600: #424242
- obsidian-700: #303030
- obsidian-800: #212121 (Base)
- obsidian-900: #121212

**Oatmeal Scale:**
- oatmeal-50: #FAFAF9
- oatmeal-100: #F5F4F2
- oatmeal-200: #EBE9E4 (Base)
- oatmeal-300: #DDD9D1
- oatmeal-400: #C9C3B8
- oatmeal-500: #B5AD9F

**Clay Scale:**
- clay-50: #FDF2F2
- clay-100: #FBE5E5
- clay-200: #F5CCCC
- clay-300: #E99A9B
- clay-400: #D16C6E
- clay-500: #BC4749 (Base)
- clay-600: #A33D3F
- clay-700: #882F31

**Sage Scale:**
- sage-50: #F2F7F4
- sage-100: #E5EFE9
- sage-200: #C8DED1
- sage-300: #9BC5AB
- sage-400: #6FA882
- sage-500: #4A7C59 (Base)
- sage-600: #3D6649
- sage-700: #30503A

---

## Typography

| Element | Font Family | Weight | Usage |
|---------|-------------|--------|-------|
| **Headers** | Merriweather | 700 (Bold) | H1-H6, brand name, section titles |
| **Body** | Lato | 400 (Regular) | Body text, paragraphs, UI elements |
| **Body Bold** | Lato | 700 (Bold) | Emphasis, labels, buttons |
| **Mono** | JetBrains Mono | 400 | Numbers, code, financial data |

### Font Sizes (rem)
- Display: 3.75rem (60px)
- H1: 2.25rem (36px)
- H2: 1.875rem (30px)
- H3: 1.5rem (24px)
- Body: 1rem (16px)
- Small: 0.875rem (14px)
- XS: 0.75rem (12px)

---

## Semantic Mappings

| Context | Color | Example |
|---------|-------|---------|
| **Primary Action** | Sage Green | "Upload", "Analyze", "Submit" buttons |
| **Destructive Action** | Clay Red | "Delete", "Clear" buttons |
| **Neutral Action** | Obsidian | "Cancel", secondary buttons |
| **Success State** | Sage Green | Balanced trial balance, income |
| **Error State** | Clay Red | Out of balance, expenses, abnormal |
| **Warning State** | Oatmeal + Obsidian border | Material alerts |
| **Info State** | Obsidian-400 | Tooltips, hints |

---

## Dark Mode (Default)

- Background: Obsidian-800 (#212121)
- Surface: Obsidian-700 (#303030)
- Card: Obsidian-600 (#424242)
- Text Primary: Oatmeal-200 (#EBE9E4)
- Text Secondary: Oatmeal-400 (#C9C3B8)
- Border: Obsidian-500 (#616161)

## Light Mode (Optional)

- Background: Oatmeal-100 (#F5F4F2)
- Surface: Oatmeal-50 (#FAFAF9)
- Card: White (#FFFFFF)
- Text Primary: Obsidian-800 (#212121)
- Text Secondary: Obsidian-500 (#616161)
- Border: Oatmeal-400 (#C9C3B8)

---

## Application Rules

1. **Never use raw hex values** — Always use Tailwind theme tokens
2. **Maintain contrast** — Minimum 4.5:1 for body text, 3:1 for large text
3. **Consistent semantic usage** — Green always means positive/income, Red always means negative/expense
4. **Typography hierarchy** — Merriweather for emphasis only, Lato for readability
