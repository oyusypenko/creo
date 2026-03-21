const fs = require('fs');
const path = require('path');

/**
 * Check if file exists
 */
function fileExists(filePath) {
  try {
    return fs.existsSync(filePath);
  } catch (error) {
    return false;
  }
}

/**
 * Ensure directory exists, create if not
 */
function ensureDirectoryExists(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    console.log(`Created directory: ${dirPath}`);
  }
}

/**
 * Calculate cost estimation for DALL-E 3 generation
 * Standard quality: $0.040 per image
 * HD quality: $0.080 per image
 */
function calculateCost(imageCount, quality = 'hd') {
  const costPerImage = quality === 'hd' ? 0.08 : 0.04;
  return (imageCount * costPerImage).toFixed(2);
}

/**
 * Format file size in human readable format
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get file stats if exists
 */
function getFileStats(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      return {
        exists: true,
        size: stats.size,
        sizeFormatted: formatFileSize(stats.size),
        modified: stats.mtime,
      };
    }
  } catch (error) {
    // File doesn't exist or error reading
  }
  return {
    exists: false,
    size: 0,
    sizeFormatted: '0 Bytes',
    modified: null,
  };
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Log with timestamp
 */
function logWithTimestamp(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

module.exports = {
  fileExists,
  ensureDirectoryExists,
  calculateCost,
  formatFileSize,
  getFileStats,
  sleep,
  logWithTimestamp,
};
