import './globals.css'

export const metadata = {
  title: 'SmartRecon-AI - Bug Bounty Recon Agent',
  description: 'Production-grade AI-assisted bug bounty reconnaissance platform',
}

// API URL configuration (Railway support)
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <nav className="bg-gray-900 text-white p-4">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">SmartRecon-AI</h1>
            <div className="flex gap-4">
              <a href="/dashboard" className="hover:text-blue-400">Dashboard</a>
              <a href="/targets" className="hover:text-blue-400">Targets</a>
              <a href="/scans" className="hover:text-blue-400">Scans</a>
              <a href="/findings" className="hover:text-blue-400">Findings</a>
              <a href="/reports" className="hover:text-blue-400">Reports</a>
            </div>
          </div>
        </nav>
        <main className="container mx-auto p-8">
          {children}
        </main>
        <footer className="bg-gray-800 text-white text-center p-4 mt-8">
          <p>SmartRecon-AI v1.0 - FOR AUTHORIZED TESTING ONLY</p>
        </footer>
      </body>
    </html>
  )
}
