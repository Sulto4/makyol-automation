import { useEffect } from 'react';
import { useThemeStore } from '../store/themeStore';

/**
 * Syncs the theme store's resolvedTheme to the DOM by toggling the 'dark' class
 * on document.documentElement. Listens for OS prefers-color-scheme changes when
 * mode is 'system'.
 */
export function useTheme() {
  const mode = useThemeStore((s) => s.mode);
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme);
  const setMode = useThemeStore((s) => s.setMode);

  // Sync 'dark' class on <html> whenever resolvedTheme changes
  useEffect(() => {
    const root = document.documentElement;
    if (resolvedTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [resolvedTheme]);

  // Listen for OS-level prefers-color-scheme changes when mode is 'system'
  useEffect(() => {
    if (mode !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = () => {
      // Re-trigger resolution by setting mode to 'system' again
      setMode('system');
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mode, setMode]);

  return { mode, resolvedTheme, setMode };
}
