export default function Home() {
  return (
    <div className="space-y-8">
      <section className="text-center py-12">
        <h1 className="text-5xl font-bold mb-4">Welcome to SmartRecon-AI</h1>
        <p className="text-xl text-gray-600 mb-8">
          Production-grade, AI-assisted bug bounty reconnaissance agent
        </p>
        <div className="flex justify-center gap-4">
          <a
            href="/targets"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
          >
            Create Target
          </a>
          <a
            href="/dashboard"
            className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition"
          >
            View Dashboard
          </a>
        </div>
      </section>

      <section className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-bold mb-2">🔍 Automated Recon</h3>
          <p className="text-gray-600">
            Orchestrates proven tools like Amass, Subfinder, HTTPX, FFUF, and Nuclei
            for comprehensive asset discovery and vulnerability scanning.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-bold mb-2">🤖 AI-Powered Analysis</h3>
          <p className="text-gray-600">
            LLM-driven triage, risk scoring, and intelligent prioritization
            of findings with automated PoC generation.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-bold mb-2">📊 Professional Reports</h3>
          <p className="text-gray-600">
            Export comprehensive reports in Markdown, HTML, or PDF formats,
            optimized for bug bounty platforms.
          </p>
        </div>
      </section>

      <section className="bg-yellow-50 border-l-4 border-yellow-500 p-6 rounded">
        <h3 className="text-lg font-bold mb-2">⚠️ Disclaimer</h3>
        <p className="text-gray-700">
          <strong>FOR AUTHORIZED TESTING ONLY</strong> - This tool is intended for
          authorized security testing and bug bounty programs only. Users are solely
          responsible for obtaining proper authorization before scanning any targets.
          Unauthorized testing may be illegal and unethical.
        </p>
      </section>

      <section>
        <h2 className="text-3xl font-bold mb-4">Quick Start</h2>
        <ol className="list-decimal list-inside space-y-2 text-gray-700">
          <li>Create a target and define its scope (domains, IP ranges)</li>
          <li>Confirm explicit authorization to test the target</li>
          <li>Start a scan with your preferred configuration</li>
          <li>Review AI-prioritized findings in real-time</li>
          <li>Export professional reports for submission</li>
        </ol>
      </section>
    </div>
  )
}
