const fs = require('fs');
const path = require('path');

class ConfigParser {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
  }

  parseConfig() {
    if (this.config) return this.config;

    try {
      // Read the TypeScript config file
      const configContent = fs.readFileSync(this.configPath, 'utf8');

      // Extract the ImagesConfig object
      const configMatch = configContent.match(/export const ImagesConfig = ({[\s\S]*?}) as const;/);
      if (!configMatch) {
        throw new Error('Could not find ImagesConfig export in config file');
      }

      // Convert TypeScript object to JavaScript and evaluate it
      const configObjectStr = configMatch[1];
      const jsConfigStr = this.convertTsToJs(configObjectStr);

      // Safely evaluate the configuration
      this.config = this.safeEval(jsConfigStr);

      return this.config;
    } catch (error) {
      console.error(`Error parsing config file: ${error.message}`);
      throw error;
    }
  }

  convertTsToJs(tsStr) {
    // Remove TypeScript-specific syntax and convert to plain JavaScript
    return tsStr
      .replace(/\/\/.*$/gm, '') // Remove single-line comments
      .replace(/\/\*[\s\S]*?\*\//g, '') // Remove multi-line comments
      .replace(/,(\s*[}\]])/g, '$1'); // Remove trailing commas
  }

  safeEval(jsStr) {
    // Create a safe evaluation context
    const evalCode = `(function() { return ${jsStr}; })()`;
    return eval(evalCode);
  }

  // Feature pages (audio-transcription, video-transcription, etc.)
  getFeatureTypes() {
    const config = this.parseConfig();
    return Object.keys(config.features || {}).filter(key => key !== 'main');
  }

  // Use case pages (podcasters, journalists, etc.)
  getUseCaseTypes() {
    const config = this.parseConfig();
    return Object.keys(config.useCases || {}).filter(key => key !== 'main');
  }

  // Source pages (youtube, zoom, etc.)
  getSourceTypes() {
    const config = this.parseConfig();
    return Object.keys(config.sources || {}).filter(key => key !== 'main');
  }

  // Resource pages (api-docs, tutorials, etc.)
  getResourceTypes() {
    const config = this.parseConfig();
    return Object.keys(config.resources || {}).filter(key => key !== 'main');
  }

  // Static pages (pricing, about, contact, etc.)
  getPageTypes() {
    const config = this.parseConfig();
    return Object.keys(config.pages || {});
  }

  // Get image types for features
  getFeatureImageTypes() {
    const config = this.parseConfig();
    const firstFeature = Object.values(config.features || {})[1]; // Skip 'main'
    return firstFeature ? Object.keys(firstFeature) : [];
  }

  // Get image types for use cases
  getUseCaseImageTypes() {
    const config = this.parseConfig();
    const firstUseCase = Object.values(config.useCases || {})[1]; // Skip 'main'
    return firstUseCase ? Object.keys(firstUseCase) : [];
  }

  // Get image types for sources
  getSourceImageTypes() {
    const config = this.parseConfig();
    const firstSource = Object.values(config.sources || {})[1]; // Skip 'main'
    return firstSource ? Object.keys(firstSource) : [];
  }

  // Get image types for resources
  getResourceImageTypes() {
    const config = this.parseConfig();
    const firstResource = Object.values(config.resources || {})[1]; // Skip 'main'
    return firstResource ? Object.keys(firstResource) : [];
  }

  // Get image types for a specific page
  getPageImageTypes(pageName) {
    const config = this.parseConfig();
    const page = config.pages?.[pageName];
    return page ? Object.keys(page) : [];
  }

  hasLandingImages() {
    const config = this.parseConfig();
    return !!(config.landing && Object.keys(config.landing).length > 0);
  }

  getLandingImageTypes() {
    const config = this.parseConfig();
    return config.landing ? Object.keys(config.landing) : [];
  }

  getFullConfig() {
    return this.parseConfig();
  }

  camelToKebab(str) {
    return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
  }

  kebabToCamel(str) {
    return str.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
  }

  // Get all categories
  getCategories() {
    const config = this.parseConfig();
    return Object.keys(config);
  }

  // Get all items in a category
  getCategoryItems(category) {
    const config = this.parseConfig();
    return Object.keys(config[category] || {}).filter(key => key !== 'main');
  }

  // Get image types for main/index pages of a category
  getMainImageTypes(category) {
    const config = this.parseConfig();
    const main = config[category]?.main;
    return main ? Object.keys(main) : [];
  }
}

module.exports = { ConfigParser };
