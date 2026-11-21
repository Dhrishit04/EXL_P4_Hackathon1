/* Defines the browser routes and shared console layout. */
import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import App from './App'

const LandingPage = lazy(() =>
  import('./pages/LandingPage').then((module) => ({ default: module.LandingPage })),
)
const DashboardPage = lazy(() =>
  import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })),
)
const InventoryPage = lazy(() =>
  import('./pages/InventoryPage').then((module) => ({ default: module.InventoryPage })),
)
const ModelDetailPage = lazy(() =>
  import('./pages/ModelDetailPage').then((module) => ({ default: module.ModelDetailPage })),
)

function PageLoading() {
  return <p className="p-8 text-sm text-slate-500" role="status">Loading workspace…</p>
}

export const router = createBrowserRouter([
  { path: '/', element: <Suspense fallback={<PageLoading />}><LandingPage /></Suspense> },
  {
    element: <App />,
    children: [
      { path: 'dashboard', element: <Suspense fallback={<PageLoading />}><DashboardPage /></Suspense> },
      { path: 'models', element: <Suspense fallback={<PageLoading />}><InventoryPage /></Suspense> },
      { path: 'models/:modelId', element: <Suspense fallback={<PageLoading />}><ModelDetailPage /></Suspense> },
    ],
  },
])
