// URL parsing and validation utilities

/**
 * Parse a URL and return its components
 */
export const parseUrl = (url: string): {
  protocol: string;
  hostname: string;
  port: string;
  pathname: string;
  search: string;
  hash: string;
} | null => {
  try {
    const urlObj = new URL(url);
    return {
      protocol: urlObj.protocol,
      hostname: urlObj.hostname,
      port: urlObj.port,
      pathname: urlObj.pathname,
      search: urlObj.search,
      hash: urlObj.hash,
    };
  } catch {
    return null;
  }
};

/**
 * Validate if a string is a valid URL
 */
export const isValidUrl = (string: string): boolean => {
  try {
    new URL(string);
    return true;
  } catch {
    return false;
  }
};

/**
 * Extract domain from URL
 */
export const extractDomain = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname;
  } catch {
    return '';
  }
};

/**
 * Extract subdomain from URL
 */
export const extractSubdomain = (url: string): string => {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname;
    const parts = hostname.split('.');
    
    if (parts.length <= 2) {
      return '';
    }
    
    return parts.slice(0, -2).join('.');
  } catch {
    return '';
  }
};

/**
 * Get base domain (without subdomains)
 */
export const getBaseDomain = (url: string): string => {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname;
    const parts = hostname.split('.');
    
    // Handle common 2-part domains
    if (parts.length === 2) {
      return hostname;
    }
    
    // Handle 3+ part domains
    const tld = parts.slice(-2).join('.');
    return tld;
  } catch {
    return '';
  }
};

/**
 * Check if domain is likely to be an email provider
 */
export const isEmailProvider = (domain: string): boolean => {
  const emailProviders = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com',
    'icloud.com', 'protonmail.com', 'yandex.com', 'mail.com', 'zoho.com',
    'gmx.com', 'tutanota.com', 'fastmail.com', 'yopmail.com', '10minutemail.com'
  ];
  
  return emailProviders.some(provider => domain.includes(provider));
};

/**
 * Check if domain is likely to be a temporary email service
 */
export const isTemporaryEmail = (domain: string): boolean => {
  const temporaryEmailDomains = [
    '10minutemail.com', 'yopmail.com', 'tempmail.org', 'guerrillamail.com',
    'mailinator.com', 'dropmail.me', 'temp-mail.org', 'throwaway.email',
    'getnada.com', 'fakemail.net', 'maildrop.cc', 'trashmail.com'
  ];
  
  return temporaryEmailDomains.includes(domain);
};

/**
 * Extract username from social media URL
 */
export const extractUsernameFromUrl = (url: string, platform?: string): string | null => {
  const patterns: Record<string, RegExp> = {
    twitter: /(?:twitter\.com|x\.com)\/([a-zA-Z0-9_]+)/i,
    instagram: /instagram\.com\/([a-zA-Z0-9_.]+)/i,
    facebook: /facebook\.com\/([a-zA-Z0-9.]+)/i,
    linkedin: /linkedin\.com\/in\/([a-zA-Z0-9-]+)/i,
    github: /github\.com\/([a-zA-Z0-9-]+)/i,
    reddit: /reddit\.com\/user\/([a-zA-Z0-9_-]+)/i,
    tiktok: /tiktok\.com\/@([a-zA-Z0-9_.]+)/i,
    youtube: /youtube\.com\/@([a-zA-Z0-9_-]+)/i,
    youtube_channel: /youtube\.com\/channel\/([a-zA-Z0-9_-]+)/i,
  };
  
  if (platform && patterns[platform]) {
    const match = url.match(patterns[platform]);
    return match ? match[1] : null;
  }
  
  // Try all patterns
  for (const pattern of Object.values(patterns)) {
    const match = url.match(pattern);
    if (match) {
      return match[1];
    }
  }
  
  return null;
};

/**
 * Validate email format
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate phone number format (basic validation)
 */
export const isValidPhoneNumber = (phone: string): boolean => {
  const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
  return phoneRegex.test(phone);
};

/**
 * Extract query parameters from URL
 */
export const getUrlParams = (url: string): Record<string, string> => {
  try {
    const urlObj = new URL(url);
    const params: Record<string, string> = {};
    
    urlObj.searchParams.forEach((value, key) => {
      params[key] = value;
    });
    
    return params;
  } catch {
    return {};
  }
};

/**
 * Build URL with query parameters
 */
export const buildUrl = (baseUrl: string, params: Record<string, string>): string => {
  try {
    const url = new URL(baseUrl);
    
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
    
    return url.toString();
  } catch {
    return baseUrl;
  }
};

/**
 * Check if URL is secure (HTTPS)
 */
export const isSecureUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'https:';
  } catch {
    return false;
  }
};

/**
 * Extract file extension from URL
 */
export const getFileExtension = (url: string): string => {
  try {
    const pathname = new URL(url).pathname;
    const parts = pathname.split('.');
    return parts.length > 1 ? parts.pop()!.toLowerCase() : '';
  } catch {
    return '';
  }
};

/**
 * Check if URL is likely an image
 */
export const isImageUrl = (url: string): boolean => {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'];
  const extension = getFileExtension(url);
  return imageExtensions.includes(extension);
};

/**
 * Check if URL is likely a document
 */
export const isDocumentUrl = (url: string): boolean => {
  const documentExtensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'];
  const extension = getFileExtension(url);
  return documentExtensions.includes(extension);
};

/**
 * Sanitize URL for safe display
 */
export const sanitizeUrl = (url: string): string => {
  // Remove potentially dangerous protocols
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:'];
  
  for (const protocol of dangerousProtocols) {
    if (url.toLowerCase().startsWith(protocol)) {
      return '';
    }
  }
  
  return url;
};

/**
 * Check if domain looks suspicious
 */
export const isSuspiciousDomain = (domain: string): boolean => {
  const suspiciousPatterns = [
    /\d{4,}/, // Too many numbers
    /[a-zA-Z]{20,}/, // Too long
    /[aeiou]{5,}/i, // Too many vowels
    /(.)\1{4,}/, // Repeated characters
    /[0-9a-f]{32,}/i, // Hex strings (potential hashes)
  ];
  
  return suspiciousPatterns.some(pattern => pattern.test(domain));
};