import '@testing-library/jest-dom/vitest';

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = function() {};
