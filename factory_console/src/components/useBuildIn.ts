/* Drives the vendored banna cursor build (public/banna.js) on the landing page and console routes. */
import { useEffect } from 'react'
import { useIsFetching } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'

interface BuildOptions {
  root?: Element | null
  agents?: number
  speed?: number
  bar?: boolean
  maxWait?: number
  exclude?: string
}

declare global {
  interface Window {
    Banna?: { start(options?: BuildOptions): void; skip(): void; stop(): void }
  }
}

// Live data, model workspace tabs and gate review controls are never hidden behind cursors.
const CONSOLE_EXCLUDE = [
  'table',
  'pre',
  'form',
  'select',
  '.recharts-wrapper',
  '.recharts-responsive-container',
  '[role="status"]',
  '[aria-labelledby="gate-review-heading"]',
  'div:has(> nav[aria-label="Model workspaces"]) ~ *',
].join(', ')

/** Starts a cursor build; if banna fails, everything it hid is shown again. */
export function startBuild(options?: BuildOptions) {
  try {
    window.Banna?.start(options)
  } catch (error) {
    document.querySelectorAll('.sb-wait').forEach((element) => element.classList.remove('sb-wait'))
    console.warn('banna stopped:', error)
  }
}

/** Stops the current build and reveals anything still waiting. */
export function stopBuild() {
  window.Banna?.stop()
}

/** Builds each console route's header and cards once per session, after its data has loaded. */
export function useBuildIn() {
  const { pathname } = useLocation()
  const ready = useIsFetching() === 0

  useEffect(() => {
    if (!ready) return
    const root = document.querySelector('main.page-outlet')
    // A page still showing its loading line is not ready; the effect runs again once fetching settles.
    if (!root || root.querySelector('[role="status"]')) return
    const key = `mp-built:${pathname}`
    try {
      if (sessionStorage.getItem(key)) return
      sessionStorage.setItem(key, '1')
    } catch {
      // Storage can be unavailable; building again does no harm.
    }
    startBuild({ root, agents: 3, speed: 2, bar: false, maxWait: 3, exclude: CONSOLE_EXCLUDE })
    return stopBuild
  }, [pathname, ready])
}
