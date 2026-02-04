'use client';

/**
 * ThemeTest Component
 * Visual verification of the Oat & Obsidian theme
 *
 * Usage: Import and render this component to verify all theme colors and typography
 */

export function ThemeTest() {
  return (
    <div className="min-h-screen bg-obsidian-800 p-8">
      <div className="max-w-4xl mx-auto space-y-12">

        {/* Header */}
        <header className="text-center">
          <h1 className="text-5xl font-serif text-oatmeal-200 mb-2">
            Oat & Obsidian
          </h1>
          <p className="text-oatmeal-400 font-sans">
            Brand Identity Theme Test
          </p>
        </header>

        {/* Color Palette */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Color Palette</h2>

          {/* Obsidian */}
          <div className="mb-6">
            <h3 className="font-sans font-bold text-oatmeal-300 mb-3">Obsidian (Primary Dark)</h3>
            <div className="flex gap-2">
              <div className="w-16 h-16 rounded-lg bg-obsidian-50 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">50</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-100 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">100</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-200 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">200</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-300 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">300</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-400 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">400</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-500 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">500</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-600 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">600</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-700 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">700</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-800 border-2 border-sage-500 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">800*</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-obsidian-900 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">900</span>
              </div>
            </div>
          </div>

          {/* Oatmeal */}
          <div className="mb-6">
            <h3 className="font-sans font-bold text-oatmeal-300 mb-3">Oatmeal (Light/Secondary)</h3>
            <div className="flex gap-2">
              <div className="w-16 h-16 rounded-lg bg-oatmeal-50 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">50</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-oatmeal-100 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">100</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-oatmeal-200 border-2 border-sage-500 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">200*</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-oatmeal-300 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">300</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-oatmeal-400 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">400</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-oatmeal-500 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">500</span>
              </div>
            </div>
          </div>

          {/* Clay */}
          <div className="mb-6">
            <h3 className="font-sans font-bold text-oatmeal-300 mb-3">Clay Red (Expenses/Errors)</h3>
            <div className="flex gap-2">
              <div className="w-16 h-16 rounded-lg bg-clay-50 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">50</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-100 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">100</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-200 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">200</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-300 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">300</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-400 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">400</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-500 border-2 border-oatmeal-200 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">500*</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-600 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">600</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-clay-700 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">700</span>
              </div>
            </div>
          </div>

          {/* Sage */}
          <div className="mb-6">
            <h3 className="font-sans font-bold text-oatmeal-300 mb-3">Sage Green (Income/Success)</h3>
            <div className="flex gap-2">
              <div className="w-16 h-16 rounded-lg bg-sage-50 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">50</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-100 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">100</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-200 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">200</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-300 flex items-end justify-center pb-1">
                <span className="text-[10px] text-obsidian-800">300</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-400 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">400</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-500 border-2 border-oatmeal-200 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">500*</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-600 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">600</span>
              </div>
              <div className="w-16 h-16 rounded-lg bg-sage-700 flex items-end justify-center pb-1">
                <span className="text-[10px] text-oatmeal-200">700</span>
              </div>
            </div>
          </div>

          <p className="text-oatmeal-500 text-sm mt-4">* Base color (DEFAULT)</p>
        </section>

        {/* Typography */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Typography</h2>

          <div className="space-y-4">
            <div>
              <span className="text-oatmeal-500 text-sm font-sans">font-serif (Merriweather)</span>
              <p className="font-serif text-3xl text-oatmeal-200">The quick brown fox jumps over the lazy dog</p>
            </div>

            <div>
              <span className="text-oatmeal-500 text-sm font-sans">font-sans (Lato)</span>
              <p className="font-sans text-xl text-oatmeal-200">The quick brown fox jumps over the lazy dog</p>
            </div>

            <div>
              <span className="text-oatmeal-500 text-sm font-sans">font-mono (JetBrains Mono)</span>
              <p className="font-mono text-lg text-oatmeal-200">$1,234,567.89 | 0123456789</p>
            </div>
          </div>
        </section>

        {/* Buttons */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Buttons</h2>

          <div className="flex flex-wrap gap-4">
            <button className="btn-primary">Primary (Sage)</button>
            <button className="btn-secondary">Secondary (Obsidian)</button>
            <button className="btn-danger">Danger (Clay)</button>
          </div>
        </section>

        {/* Badges */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Badges</h2>

          <div className="flex flex-wrap gap-4">
            <span className="badge-success">Balanced</span>
            <span className="badge-error">Out of Balance</span>
            <span className="badge-neutral">Pending</span>
          </div>
        </section>

        {/* Status Pills */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Status Pills</h2>

          <div className="flex flex-wrap gap-4">
            <div className="status-pill">
              <span className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></span>
              <span>Active</span>
            </div>
            <div className="status-pill-warning">
              <span className="w-2 h-2 bg-oatmeal-400 rounded-full"></span>
              <span>Pending Review</span>
            </div>
            <div className="status-pill-danger">
              <span className="w-2 h-2 bg-clay-400 rounded-full"></span>
              <span>Action Required</span>
            </div>
          </div>
        </section>

        {/* Stat Cards */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Stat Cards</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="stat-card">
              <p className="text-oatmeal-400 text-sm font-sans mb-1">Total Assessments</p>
              <p className="text-3xl font-mono font-bold text-oatmeal-100">24</p>
              <p className="text-oatmeal-500 text-xs font-sans mt-1">This month</p>
            </div>
            <div className="stat-card">
              <p className="text-oatmeal-400 text-sm font-sans mb-1">Active Clients</p>
              <p className="text-3xl font-mono font-bold text-sage-400">12</p>
              <p className="text-oatmeal-500 text-xs font-sans mt-1">Portfolio</p>
            </div>
            <div className="stat-card">
              <p className="text-oatmeal-400 text-sm font-sans mb-1">Flagged Items</p>
              <p className="text-3xl font-mono font-bold text-clay-400">3</p>
              <p className="text-oatmeal-500 text-xs font-sans mt-1">Require attention</p>
            </div>
          </div>
        </section>

        {/* Financial Data Example */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Financial Data Display</h2>

          <div className="bg-obsidian-800 rounded-xl p-4">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-oatmeal-400">Total Debits:</span>
              <span className="text-oatmeal-200 text-right font-mono">$125,430.00</span>

              <span className="text-oatmeal-400">Total Credits:</span>
              <span className="text-oatmeal-200 text-right font-mono">$125,430.00</span>

              <span className="text-oatmeal-400">Difference:</span>
              <span className="text-sage-400 text-right font-mono">$0.00</span>

              <span className="text-oatmeal-400">Abnormal Balance:</span>
              <span className="text-clay-400 text-right font-mono">-$5,000.00</span>
            </div>
          </div>
        </section>

        {/* Semantic States */}
        <section className="card">
          <h2 className="text-2xl font-serif text-oatmeal-200 mb-6">Semantic States</h2>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Success */}
            <div className="bg-sage-500/10 border border-sage-500/30 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 bg-sage-500 rounded-full"></div>
                <span className="text-sage-300 font-bold">Success State</span>
              </div>
              <p className="text-sage-200/70 text-sm">Trial balance is balanced. Income recorded.</p>
            </div>

            {/* Error */}
            <div className="bg-clay-500/10 border border-clay-500/30 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 bg-clay-500 rounded-full"></div>
                <span className="text-clay-300 font-bold">Error State</span>
              </div>
              <p className="text-clay-200/70 text-sm">Out of balance. Abnormal expense detected.</p>
            </div>

            {/* Warning */}
            <div className="bg-oatmeal-200/10 border border-oatmeal-400/30 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 bg-oatmeal-400 rounded-full"></div>
                <span className="text-oatmeal-300 font-bold">Warning State</span>
              </div>
              <p className="text-oatmeal-400 text-sm">Material risk alert. Review recommended.</p>
            </div>

            {/* Info */}
            <div className="bg-obsidian-600 border border-obsidian-400 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 bg-obsidian-400 rounded-full"></div>
                <span className="text-oatmeal-300 font-bold">Info State</span>
              </div>
              <p className="text-oatmeal-500 text-sm">Immaterial item. Below threshold.</p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center text-oatmeal-500 text-sm">
          <p>Oat & Obsidian Theme v1.0 | Paciolus Brand Identity</p>
        </footer>

      </div>
    </div>
  );
}

export default ThemeTest;
