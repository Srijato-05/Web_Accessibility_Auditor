import { createContext, useContext, useState, useEffect } from 'react';

export type Theme = 'cyberpunk' | 'hc-dark' | 'hc-light' | 'colorblind';
export type TextSize = 'normal' | 'large' | 'extra-large';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  textSize: TextSize;
  setTextSize: (size: TextSize) => void;
  dyslexiaFont: boolean;
  setDyslexiaFont: (val: boolean) => void;
  reduceMotion: boolean;
  setReduceMotion: (val: boolean) => void;
  enableHotkeys: boolean;
  setEnableHotkeys: (val: boolean) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    return (localStorage.getItem('theme') as Theme) || 'cyberpunk';
  });
  const [textSize, setTextSizeState] = useState<TextSize>(() => {
    return (localStorage.getItem('text-size') as TextSize) || 'normal';
  });
  const [dyslexiaFont, setDyslexiaFontState] = useState<boolean>(() => {
    return localStorage.getItem('dyslexia-font') === 'true';
  });
  const [reduceMotion, setReduceMotionState] = useState<boolean>(() => {
    return localStorage.getItem('reduce-motion') === 'true';
  });
  const [enableHotkeys, setEnableHotkeysState] = useState<boolean>(() => {
    return localStorage.getItem('enable-hotkeys') !== 'false';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute('data-text-size', textSize);
    localStorage.setItem('text-size', textSize);
  }, [textSize]);

  useEffect(() => {
    if (dyslexiaFont) {
      document.body.classList.add('dyslexia-font');
    } else {
      document.body.classList.remove('dyslexia-font');
    }
    localStorage.setItem('dyslexia-font', dyslexiaFont ? 'true' : 'false');
  }, [dyslexiaFont]);

  useEffect(() => {
    document.documentElement.setAttribute('data-reduce-motion', reduceMotion ? 'true' : 'false');
    localStorage.setItem('reduce-motion', reduceMotion ? 'true' : 'false');
  }, [reduceMotion]);

  useEffect(() => {
    if (!enableHotkeys) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (!e.altKey) return;

      const key = e.key.toLowerCase();
      const code = e.code;
      console.log(`[ThemeContext Hotkey] Alt+${key} (code: ${code})`);
      
      if (key === 't' || code === 'KeyT') {
        e.preventDefault();
        e.stopPropagation();
        const themes: Theme[] = ['cyberpunk', 'hc-dark', 'hc-light', 'colorblind'];
        const currentIndex = themes.indexOf(theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setThemeState(themes[nextIndex]);
      } else if (key === 'd' || code === 'KeyD') {
        e.preventDefault();
        e.stopPropagation();
        window.location.hash = '#/dashboard';
      } else if (key === 'h' || code === 'KeyH') {
        e.preventDefault();
        e.stopPropagation();
        window.location.hash = '#/help';
      } else if (key === 's' || code === 'KeyS') {
        e.preventDefault();
        e.stopPropagation();
        window.location.hash = '#/';
      } else if (key === 'r' || code === 'KeyR' || key === 'm' || code === 'KeyM') {
        e.preventDefault();
        e.stopPropagation();
        setReduceMotionState(!reduceMotion);
      } else if (key === 'f' || code === 'KeyF') {
        e.preventDefault();
        e.stopPropagation();
        setDyslexiaFontState(!dyslexiaFont);
      } else if (key === 'k' || code === 'KeyK') {
        e.preventDefault();
        e.stopPropagation();
        const searchInput = document.querySelector('input[placeholder*="Search"], input[id*="search"], input[type="text"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [enableHotkeys, theme, reduceMotion, dyslexiaFont]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const setTextSize = (newSize: TextSize) => {
    setTextSizeState(newSize);
  };

  const setDyslexiaFont = (val: boolean) => {
    setDyslexiaFontState(val);
  };

  const setReduceMotion = (val: boolean) => {
    setReduceMotionState(val);
  };

  const setEnableHotkeys = (val: boolean) => {
    setEnableHotkeysState(val);
    localStorage.setItem('enable-hotkeys', val ? 'true' : 'false');
  };

  return (
    <ThemeContext value={{
      theme,
      setTheme,
      textSize,
      setTextSize,
      dyslexiaFont,
      setDyslexiaFont,
      reduceMotion,
      setReduceMotion,
      enableHotkeys,
      setEnableHotkeys
    }}>
      {children}
    </ThemeContext>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
