const path = require('path');
const fs = require('fs');
const { ConfigParser } = require('./ConfigParser');

class PathManager {
  constructor(options = {}) {
    this.paths = [];

    // Load paths from env or options
    this.configDir = options.configDir || process.env.IMAGE_CONFIG_DIR || './config';
    this.outputDir = options.outputDir || process.env.IMAGE_OUTPUT_DIR || './output';

    // Load paths configuration
    this.PATHS = this.loadPathsConfig();

    // Initialize config parser if images config exists
    if (this.PATHS.imagesConfig && fs.existsSync(this.PATHS.imagesConfig)) {
      this.configParser = new ConfigParser(this.PATHS.imagesConfig);
    } else {
      this.configParser = null;
    }

    // Initialize dynamic configuration
    this.loadConfiguration();
  }

  loadPathsConfig() {
    const pathsConfigFile = path.join(this.configDir, 'paths.js');

    if (fs.existsSync(pathsConfigFile)) {
      const { PATHS } = require(path.resolve(pathsConfigFile));
      return PATHS;
    }

    // Default paths structure
    const baseOutputDir = path.resolve(this.outputDir);
    return {
      baseDir: path.resolve('.'),
      outputDir: baseOutputDir,
      landing: path.join(baseOutputDir, 'landing'),
      features: path.join(baseOutputDir, 'features'),
      useCases: path.join(baseOutputDir, 'use-cases'),
      sources: path.join(baseOutputDir, 'sources'),
      pages: path.join(baseOutputDir, 'pages'),
      resources: path.join(baseOutputDir, 'resources'),
      imagesConfig: null,
    };
  }

  loadConfiguration() {
    try {
      if (this.configParser) {
        // Load configuration dynamically from images.config.ts
        this.featureTypes = this.configParser.getFeatureTypes();
        this.useCaseTypes = this.configParser.getUseCaseTypes();
        this.sourceTypes = this.configParser.getSourceTypes();
        this.resourceTypes = this.configParser.getResourceTypes();
        this.pageTypes = this.configParser.getPageTypes();

        this.featureImageTypes = this.convertConfigKeysToFileNames(
          this.configParser.getFeatureImageTypes()
        );
        this.useCaseImageTypes = this.convertConfigKeysToFileNames(
          this.configParser.getUseCaseImageTypes()
        );
        this.sourceImageTypes = this.convertConfigKeysToFileNames(
          this.configParser.getSourceImageTypes()
        );
        this.resourceImageTypes = this.convertConfigKeysToFileNames(
          this.configParser.getResourceImageTypes()
        );
        this.landingImageTypes = this.convertConfigKeysToFileNames(
          this.configParser.getLandingImageTypes()
        );

        console.log(`Loaded configuration from ${this.PATHS.imagesConfig}`);
      } else {
        this.loadDefaultConfiguration();
      }
    } catch (error) {
      console.warn(`Warning: Could not load dynamic config, using defaults: ${error.message}`);
      this.loadDefaultConfiguration();
    }
  }

  loadDefaultConfiguration() {
    this.featureTypes = [];
    this.useCaseTypes = [];
    this.sourceTypes = [];
    this.resourceTypes = [];
    this.pageTypes = [];
    this.featureImageTypes = ['hero', 'card', 'thumbnail', 'ogImage'];
    this.useCaseImageTypes = ['hero', 'card', 'thumbnail', 'ogImage'];
    this.sourceImageTypes = ['hero', 'card', 'thumbnail', 'ogImage'];
    this.resourceImageTypes = ['hero', 'card', 'ogImage'];
    this.landingImageTypes = ['hero', 'ogImage', 'heroMobile'];
  }

  convertConfigKeysToFileNames(configKeys) {
    return configKeys.map(key => {
      switch (key) {
        case 'ogImage':
          return 'og-image';
        case 'heroMobile':
          return 'hero-mobile';
        case 'step1':
          return 'step-1';
        case 'step2':
          return 'step-2';
        case 'step3':
          return 'step-3';
        default:
          return key;
      }
    });
  }

  camelToKebab(str) {
    return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
  }

  generateImagePaths() {
    this.paths = [];

    this.addLandingPaths();
    this.addFeaturePaths();
    this.addUseCasePaths();
    this.addSourcePaths();
    this.addResourcePaths();
    this.addPagePaths();

    return this.paths;
  }

  addLandingPaths() {
    this.landingImageTypes.forEach(imageType => {
      this.paths.push({
        category: 'landing',
        type: imageType,
        path: path.join(this.PATHS.landing, `${imageType}.webp`),
      });
    });
  }

  addFeaturePaths() {
    // Main features index page
    ['hero', 'og-image'].forEach(imageType => {
      this.paths.push({
        category: 'features',
        subcategory: 'main',
        type: imageType,
        path: path.join(this.PATHS.features, `main-${imageType}.webp`),
      });
    });

    // Individual feature pages
    this.featureTypes.forEach(feature => {
      const folderName = this.camelToKebab(feature);
      this.featureImageTypes.forEach(imageType => {
        this.paths.push({
          category: 'features',
          subcategory: feature,
          type: imageType,
          path: path.join(this.PATHS.features, folderName, `${imageType}.webp`),
        });
      });
    });
  }

  addUseCasePaths() {
    // Main use cases index page
    ['hero', 'og-image'].forEach(imageType => {
      this.paths.push({
        category: 'useCases',
        subcategory: 'main',
        type: imageType,
        path: path.join(this.PATHS.useCases, `main-${imageType}.webp`),
      });
    });

    // Individual use case pages
    this.useCaseTypes.forEach(useCase => {
      const folderName = this.camelToKebab(useCase);
      this.useCaseImageTypes.forEach(imageType => {
        this.paths.push({
          category: 'useCases',
          subcategory: useCase,
          type: imageType,
          path: path.join(this.PATHS.useCases, folderName, `${imageType}.webp`),
        });
      });
    });
  }

  addSourcePaths() {
    // Main sources index page
    ['hero', 'og-image'].forEach(imageType => {
      this.paths.push({
        category: 'sources',
        subcategory: 'main',
        type: imageType,
        path: path.join(this.PATHS.sources, `main-${imageType}.webp`),
      });
    });

    // Individual source pages
    this.sourceTypes.forEach(source => {
      const folderName = this.camelToKebab(source);
      this.sourceImageTypes.forEach(imageType => {
        this.paths.push({
          category: 'sources',
          subcategory: source,
          type: imageType,
          path: path.join(this.PATHS.sources, folderName, `${imageType}.webp`),
        });
      });
    });
  }

  addResourcePaths() {
    // Main resources index page
    ['hero', 'og-image'].forEach(imageType => {
      this.paths.push({
        category: 'resources',
        subcategory: 'main',
        type: imageType,
        path: path.join(this.PATHS.resources, `main-${imageType}.webp`),
      });
    });

    // Individual resource pages
    this.resourceTypes.forEach(resource => {
      const folderName = this.camelToKebab(resource);
      this.resourceImageTypes.forEach(imageType => {
        this.paths.push({
          category: 'resources',
          subcategory: resource,
          type: imageType,
          path: path.join(this.PATHS.resources, folderName, `${imageType}.webp`),
        });
      });
    });
  }

  addPagePaths() {
    if (!this.configParser) return;

    this.pageTypes.forEach(pageName => {
      const folderName = this.camelToKebab(pageName);
      const pageImageTypes = this.configParser.getPageImageTypes(pageName);

      pageImageTypes.forEach(imageType => {
        const fileName = this.convertConfigKeysToFileNames([imageType])[0];
        this.paths.push({
          category: 'pages',
          subcategory: pageName,
          type: imageType,
          path: path.join(this.PATHS.pages, folderName, `${fileName}.webp`),
        });
      });
    });
  }

  getPathsByCategory(category) {
    return this.paths.filter(p => p.category === category);
  }

  getPathsBySubcategory(category, subcategory) {
    return this.paths.filter(p => p.category === category && p.subcategory === subcategory);
  }

  getPathsByType(type) {
    return this.paths.filter(p => p.type === type);
  }

  filterValidPaths(prompts) {
    return this.paths.filter(p => {
      switch (p.category) {
        case 'landing':
          return prompts.landing?.[p.type];
        case 'features':
          return prompts.features?.[p.subcategory]?.[p.type];
        case 'useCases':
          return prompts.useCases?.[p.subcategory]?.[p.type];
        case 'sources':
          return prompts.sources?.[p.subcategory]?.[p.type];
        case 'resources':
          return prompts.resources?.[p.subcategory]?.[p.type];
        case 'pages':
          return prompts.pages?.[p.subcategory]?.[p.type];
        default:
          return false;
      }
    });
  }

  getAllPaths() {
    if (this.paths.length === 0) {
      this.generateImagePaths();
    }
    return this.paths;
  }

  getStats() {
    return {
      total: this.paths.length,
      landing: this.getPathsByCategory('landing').length,
      features: this.getPathsByCategory('features').length,
      useCases: this.getPathsByCategory('useCases').length,
      sources: this.getPathsByCategory('sources').length,
      resources: this.getPathsByCategory('resources').length,
      pages: this.getPathsByCategory('pages').length,
    };
  }
}

module.exports = { PathManager };
