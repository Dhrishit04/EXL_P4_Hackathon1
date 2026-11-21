/* Drives the vendored banna cursor build (public/banna.js) on the landing page. */

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
