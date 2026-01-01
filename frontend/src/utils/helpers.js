// Utility helper functions

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const getIdentifierType = (query) => {
  // Auto-detect query type
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const phoneRegex = /^[\d\s\-\+\(\)]{10,}$/;
  const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
  
  if (emailRegex.test(query)) return 'email';
  if (phoneRegex.test(query)) return 'phone';
  if (domainRegex.test(query)) return 'domain';
  
  return 'username';
};

export const calculateConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#6bff6b';
  if (confidence >= 0.5) return '#ffeb3b';
  return '#ff6b6b';
};
