import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.open
window.open = vi.fn();

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = vi.fn();
