import { render, screen } from '@testing-library/react';
import App from './App';

test('renders OSINT Intelligence Platform header', () => {
  render(<App />);
  const headerElement = screen.getByText(/OSINT Intelligence Platform/i);
  expect(headerElement).toBeInTheDocument();
});

test('renders tagline', () => {
  render(<App />);
  const taglineElement = screen.getByText(/Comprehensive Surface Web Intelligence Aggregation/i);
  expect(taglineElement).toBeInTheDocument();
});

test('renders footer', () => {
  render(<App />);
  const footerElement = screen.getByText(/Phase 1: Surface Web OSINT Collection/i);
  expect(footerElement).toBeInTheDocument();
});
