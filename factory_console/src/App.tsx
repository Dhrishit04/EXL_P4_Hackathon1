/* Provides the shared application shell and nested page outlet. */
import { Outlet } from 'react-router-dom'
import { ModeBanner } from './components/ModeBanner'
import { ReviewerProvider } from './components/ReviewerProvider'
import { Sidebar } from './components/Sidebar'
import { Topbar } from './components/Topbar'

/** Renders the console navigation, mode notice, and active route. */
export default function App() {
  return (
    <ReviewerProvider>
      <div className="app-shell">
        <Sidebar />
        <div className="app-main">
          <Topbar />
          <ModeBanner />
          <main className="page-outlet">
            <Outlet />
          </main>
        </div>
      </div>
    </ReviewerProvider>
  )
}
