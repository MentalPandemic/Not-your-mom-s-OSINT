import { useEffect } from 'react';

/**
 * Custom hook for keyboard shortcuts
 */
export const useKeyboardShortcuts = () => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle shortcuts when not typing in input fields
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        (event.target as HTMLElement)?.contentEditable === 'true'
      ) {
        return;
      }

      const { ctrlKey, metaKey, altKey, shiftKey, key } = event;
      const isCtrlOrCmd = ctrlKey || metaKey;

      // Global shortcuts
      if (isCtrlOrCmd && key === 'k') {
        event.preventDefault();
        // Focus search input - would dispatch an action to open search
      }

      if (isCtrlOrCmd && key === 'e') {
        event.preventDefault();
        // Open export panel - would dispatch an action
      }

      if (isCtrlOrCmd && key === 's') {
        event.preventDefault();
        // Save current workspace - would dispatch an action
      }

      if (isCtrlOrCmd && key === 'n') {
        event.preventDefault();
        // New search - would dispatch an action
      }

      if (key === 'Escape') {
        // Close modals, panels, etc. - would dispatch actions
      }

      if (key === '?' && shiftKey) {
        event.preventDefault();
        // Show help dialog
      }

      // Navigation shortcuts
      if (!isCtrlOrCmd && !altKey && !shiftKey) {
        switch (key) {
          case '1':
            event.preventDefault();
            // Switch to search view
            break;
          case '2':
            event.preventDefault();
            // Switch to results view
            break;
          case '3':
            event.preventDefault();
            // Switch to graph view
            break;
          case '4':
            event.preventDefault();
            // Switch to timeline view
            break;
          case '5':
            event.preventDefault();
            // Switch to export view
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);
};

/**
 * Hook for debounced value
 */
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook for local storage
 */
export const useLocalStorage = <T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void] => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue];
};

/**
 * Hook for previous value
 */
export const usePrevious = <T>(value: T): T | undefined => {
  const ref = useRef<T>();
  
  useEffect(() => {
    ref.current = value;
  }, [value]);
  
  return ref.current;
};

/**
 * Hook for window size
 */
export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

/**
 * Hook for click outside
 */
export const useClickOutside = (
  ref: React.RefObject<HTMLElement>,
  handler: () => void
) => {
  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [ref, handler]);
};

/**
 * Hook for intersection observer
 */
export const useIntersectionObserver = (
  ref: React.RefObject<HTMLElement>,
  options?: IntersectionObserverInit
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      options
    );

    observer.observe(element);
    return () => {
      observer.unobserve(element);
    };
  }, [ref, options]);

  return isIntersecting;
};

/**
 * Hook for async operations
 */
export const useAsync = <T, E = string>(
  asyncFunction: () => Promise<T>,
  immediate = true
) => {
  const [status, setStatus] = useState<'idle' | 'pending' | 'success' | 'error'>('idle');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<E | null>(null);

  const execute = useCallback(() => {
    setStatus('pending');
    setData(null);
    setError(null);

    return asyncFunction()
      .then((response: T) => {
        setData(response);
        setStatus('success');
        return response;
      })
      .catch((error: E) => {
        setError(error);
        setStatus('error');
        throw error;
      });
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return {
    execute,
    status,
    data,
    error,
    isPending: status === 'pending',
    isSuccess: status === 'success',
    isError: status === 'error',
  };
};

/**
 * Hook for copy to clipboard
 */
export const useCopyToClipboard = () => {
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const copy = async (text: string) => {
    if (!navigator?.clipboard) {
      console.warn('Clipboard not supported');
      return false;
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(text);
      return true;
    } catch (error) {
      console.warn('Copy failed', error);
      setCopiedText(null);
      return false;
    }
  };

  useEffect(() => {
    if (copiedText) {
      const timeout = setTimeout(() => setCopiedText(null), 2000);
      return () => clearTimeout(timeout);
    }
  }, [copiedText]);

  return { copy, copiedText };
};

import { useState, useEffect, useRef, useCallback } from 'react';