// Data formatting utilities
import { format, formatDistanceToNow, parseISO } from 'date-fns';

/**
 * Format a date to a human-readable string
 */
export const formatDate = (date: Date | string, formatString: string = 'MMM dd, yyyy'): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatString);
};

/**
 * Format a date to a relative time string
 */
export const formatRelativeTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true });
};

/**
 * Format a confidence score as a percentage
 */
export const formatConfidence = (confidence: number): string => {
  return `${Math.round(confidence * 100)}%`;
};

/**
 * Format a file size in bytes to human-readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Format a number with thousand separators
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num);
};

/**
 * Format a currency amount
 */
export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

/**
 * Truncate text to a specified length
 */
export const truncateText = (text: string, maxLength: number, suffix: string = '...'): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Format a URL for display (remove protocol and trailing slash)
 */
export const formatUrl = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname + urlObj.pathname.replace(/\/$/, '');
  } catch {
    return url;
  }
};

/**
 * Format a phone number
 */
export const formatPhoneNumber = (phoneNumber: string): string => {
  const cleaned = phoneNumber.replace(/\D/g, '');
  
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  
  return phoneNumber;
};

/**
 * Format a list of items with proper punctuation
 */
export const formatList = (items: string[], conjunction: string = 'and'): string => {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} ${conjunction} ${items[1]}`;
  
  return `${items.slice(0, -1).join(', ')}, ${conjunction} ${items[items.length - 1]}`;
};