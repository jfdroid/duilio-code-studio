/**
 * helpers.js - Utility functions for common tasks.
 */

/**
 * formatDate - Formats a given date to a specified format.
 * @param {Date} date - The date to format.
 * @param {string} format - The desired format (e.g., 'YYYY-MM-DD', 'MM/DD/YYYY').
 * @returns {string} - The formatted date string.
 */
function formatDate(date, format) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day);
}

/**
 * getFormattedDate - Returns the current date in a specified format.
 * @param {string} format - The desired format (e.g., 'YYYY-MM-DD', 'MM/DD/YYYY').
 * @returns {string} - The formatted current date string.
 */
function getFormattedDate(format) {
  return formatDate(new Date(), format);
}

export { formatDate, getFormattedDate };