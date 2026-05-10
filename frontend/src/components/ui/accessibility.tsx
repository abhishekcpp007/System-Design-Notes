"use client";

/**
 * Skip to Content Link — WCAG 2.1 requirement.
 * Appears on focus (keyboard navigation) for screen reader users.
 */
export function SkipToContent() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-primary-600 focus:text-white focus:font-medium focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-300 focus:ring-offset-2"
    >
      Skip to main content
    </a>
  );
}

/**
 * Accessible focus trap for modals and overlays.
 * Traps keyboard focus within a container.
 */
export function useFocusTrap(containerRef: React.RefObject<HTMLElement>) {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== "Tab" || !containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  };

  return { handleKeyDown };
}

/**
 * Accessible live announcer for dynamic content changes.
 * Screen readers will announce content changes.
 */
export function LiveAnnouncer({ message, assertive = false }: { message: string; assertive?: boolean }) {
  return (
    <div
      role={assertive ? "alert" : "status"}
      aria-live={assertive ? "assertive" : "polite"}
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
}

/**
 * Visually Hidden component for screen-reader-only text.
 */
export function VisuallyHidden({ children, as: Tag = "span" }: { children: React.ReactNode; as?: keyof JSX.IntrinsicElements }) {
  return <Tag className="sr-only">{children}</Tag>;
}

/**
 * Accessible icon button with required aria-label.
 */
export function IconButton({
  onClick,
  ariaLabel,
  children,
  className = "",
  disabled = false,
}: {
  onClick: () => void;
  ariaLabel: string;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      disabled={disabled}
      className={`p-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-dark-bg disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {children}
    </button>
  );
}

/**
 * Accessible loading indicator.
 */
export function LoadingSpinner({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" aria-label={label} className="flex items-center justify-center">
      <svg
        className="animate-spin h-8 w-8 text-primary-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  );
}

/**
 * Error boundary fallback with accessible error messaging.
 */
export function ErrorFallback({
  error,
  resetAction,
}: {
  error: string;
  resetAction?: () => void;
}) {
  return (
    <div role="alert" aria-live="assertive" className="p-6 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
        Something went wrong
      </h2>
      <p className="text-red-600 dark:text-red-300 mb-4">{error}</p>
      {resetAction && (
        <button
          onClick={resetAction}
          className="px-4 py-2 rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Try again
        </button>
      )}
    </div>
  );
}
