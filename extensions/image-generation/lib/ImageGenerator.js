const OpenAI = require('openai');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');
const sharp = require('sharp');
const { glob } = require('glob');
const { fileExists, sleep } = require('./utils');
const { PathManager } = require('./PathManager');

class ImageGenerator {
  constructor(options = {}) {
    this.apiKey = process.env.OPENAI_API_KEY;
    this.openai = null;

    if (this.apiKey) {
      this.openai = new OpenAI({ apiKey: this.apiKey });
    }

    // Load prompts from env-specified file or options
    this.prompts = this.loadPrompts(options.promptsFile);

    // App name for SEO images (from env or options)
    this.appName = options.appName || process.env.APP_NAME || 'AI Application';

    this.stats = {
      generated: 0,
      seoGenerated: 0,
      optimized: 0,
      skipped: 0,
      failed: 0,
      totalCost: 0,
    };

    this.startTime = Date.now();
    this.pathManager = new PathManager({
      configDir: options.configDir || process.env.IMAGE_CONFIG_DIR,
      outputDir: options.outputDir || process.env.IMAGE_OUTPUT_DIR,
    });

    // Configuration
    this.optimizationConfig = {
      jpeg: { quality: 85, progressive: true, mozjpeg: true },
      webp: { quality: 85 },
      avif: { quality: 75 },
    };

    this.sizeConfig = {
      hero: { width: 1200, height: 800 },
      card: { width: 600, height: 400 },
      thumbnail: { width: 400, height: 300 },
      ogImage: { width: 1200, height: 630 },
      'gallery-1': { width: 800, height: 600 },
      'gallery-2': { width: 800, height: 600 },
      'gallery-3': { width: 800, height: 600 },
    };
  }

  loadPrompts(promptsFile) {
    const file = promptsFile || process.env.PROMPTS_FILE;

    if (file && fs.existsSync(file)) {
      try {
        const { CONTEXT_AWARE_PROMPTS } = require(path.resolve(file));
        console.log(`Loaded prompts from ${file}`);
        return CONTEXT_AWARE_PROMPTS;
      } catch (error) {
        console.warn(`Warning: Could not load prompts from ${file}: ${error.message}`);
      }
    }

    // Return empty prompts object
    return {
      landing: {},
      features: {},
      useCases: {},
      sources: {},
      resources: {},
      pages: {},
    };
  }

  // CLI functionality
  parseArgs(args = process.argv.slice(2)) {
    const flags = {};
    for (const arg of args) {
      if (arg.startsWith('--')) {
        const [key, value] = arg.substring(2).split('=');
        flags[key] = value || true;
      }
    }
    return { flags };
  }

  log(message) {
    const timestamp = new Date().toISOString().substring(11, 19);
    console.log(`[${timestamp}] ${message}`);
  }

  showSummary() {
    const duration = ((Date.now() - this.startTime) / 1000).toFixed(2);
    console.log(`\nSummary:`);
    console.log(`   AI Generated: ${this.stats.generated}`);
    console.log(`   SEO Generated: ${this.stats.seoGenerated}`);
    console.log(`   Optimized: ${this.stats.optimized}`);
    console.log(`   Failed: ${this.stats.failed}`);
    console.log(`   Skipped: ${this.stats.skipped}`);
    console.log(`   Duration: ${duration}s`);
    if (this.stats.totalCost) {
      console.log(`   Cost: $${this.stats.totalCost.toFixed(2)}`);
    }
    console.log();
  }

  handleError(error, context = 'execution') {
    console.error(`Error during ${context}: ${error.message}`);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }

  showHelp() {
    console.log('Creo Image Generation Extension');
    console.log('\nUsage: node index.js generate [options]');
    console.log('\nOptions:');
    console.log('  --estimate        Show cost estimation only');
    console.log('  --seo-only        Generate only SEO images');
    console.log('  --optimize-only   Optimize existing images only');
    console.log('  --quality         Image quality: standard|hd (default: hd)');
    console.log('  --help            Show this help message');
    console.log('\nEnvironment Variables:');
    console.log('  OPENAI_API_KEY    OpenAI API key (required for generation)');
    console.log('  IMAGE_CONFIG_DIR  Directory with paths.js config');
    console.log('  IMAGE_OUTPUT_DIR  Directory for generated images');
    console.log('  PROMPTS_FILE      Path to prompts.js file');
    console.log('  APP_NAME          App name for SEO images');
  }

  // Main execution methods
  async execute(args = process.argv.slice(2)) {
    const { flags } = this.parseArgs(args);

    if (flags.help) {
      this.showHelp();
      return;
    }

    try {
      if (flags.estimate) {
        return await this.estimateCosts(flags);
      } else if (flags['seo-only']) {
        return await this.generateSEOOnly(flags);
      } else if (flags['optimize-only']) {
        return await this.optimizeOnly(flags);
      } else {
        return await this.generateAll(flags);
      }
    } catch (error) {
      this.handleError(error, 'image generation');
    }
  }

  async estimateCosts(flags = {}) {
    this.log('Calculating cost estimation');

    const imagePaths = this.pathManager.generateImagePaths();
    const validPaths = this.pathManager.filterValidPaths(this.prompts);

    const quality = flags.quality || 'hd';
    const estimation = this.estimateCost(validPaths, quality);

    console.log(`\nCost Estimation:`);
    console.log(`   Images to generate: ${estimation.totalImages}`);
    console.log(`   Total cost: $${estimation.totalCost}`);
    console.log();

    return estimation;
  }

  async generateAll(flags = {}) {
    this.log('Starting complete image generation');

    const imagePaths = this.pathManager.generateImagePaths();
    const validPaths = this.pathManager.filterValidPaths(this.prompts);

    const quality = flags.quality || 'hd';
    const estimation = this.estimateCost(validPaths, quality);
    this.log(`Processing ${validPaths.length} images - Estimated cost: $${estimation.totalCost}`);

    // 1. AI Generation
    await this.generateAIImages(validPaths, quality);

    // 2. SEO Generation
    await this.generateSEOImages(imagePaths);

    // 3. Optimization
    await this.optimizeAllImages();

    this.showSummary();
    return this.stats;
  }

  async generateSEOOnly() {
    this.log('Generating SEO images only');
    const imagePaths = this.pathManager.generateImagePaths();
    await this.generateSEOImages(imagePaths);
    this.showSummary();
    return this.stats;
  }

  async optimizeOnly() {
    this.log('Optimizing existing images');
    await this.optimizeAllImages();
    this.showSummary();
    return this.stats;
  }

  // 1. AI Image Generation
  verifyApiKey() {
    if (!this.apiKey) {
      console.error('OPENAI_API_KEY not found. Please set your OpenAI API key.');
      console.log('Get your key at: https://platform.openai.com/api-keys');
      return false;
    }
    return true;
  }

  async generateAIImages(validPaths, quality = 'hd') {
    console.log(`Starting AI image generation with DALL-E 3...`);

    if (!this.verifyApiKey()) {
      return this.stats;
    }

    // Pre-analyze all images
    console.log(`\nAnalyzing ${validPaths.length} images...`);
    const imagesWithPrompts = [];
    const imagesWithoutPrompts = [];
    const existingImages = [];

    for (const pathInfo of validPaths) {
      const prompt = this.getPromptForPath(pathInfo);
      const fullPath = path.resolve(pathInfo.path);
      const exists = fileExists(pathInfo.path);

      if (exists) {
        existingImages.push({ ...pathInfo, fullPath });
      } else if (!prompt) {
        imagesWithoutPrompts.push({
          ...pathInfo,
          fullPath,
          reason: `No prompt for ${pathInfo.category}/${pathInfo.subcategory || 'main'}/${pathInfo.type}`,
        });
      } else {
        imagesWithPrompts.push({ ...pathInfo, fullPath, prompt });
      }
    }

    // Show report
    console.log(`\nAnalysis Summary:`);
    console.log(`   Already exist: ${existingImages.length}`);
    console.log(`   Will be generated: ${imagesWithPrompts.length}`);
    console.log(`   Skipped (no prompts): ${imagesWithoutPrompts.length}`);

    if (imagesWithPrompts.length === 0) {
      console.log(`\nNo images to generate.`);
      return this.stats;
    }

    console.log(`\nStarting generation of ${imagesWithPrompts.length} images...\n`);

    for (const imageInfo of imagesWithPrompts) {
      await this.generateImage(imageInfo.prompt, imageInfo.path, quality);
      await sleep(1000); // Rate limiting
    }

    return this.stats;
  }

  async generateImage(promptData, outputPath, quality = 'hd') {
    const fullPath = path.resolve(outputPath);

    if (fileExists(outputPath)) {
      console.log(`Skipping: ${fullPath} (already exists)`);
      this.stats.skipped++;
      return { success: true, generated: false };
    }

    console.log(`Generating: ${fullPath}...`);

    try {
      const response = await this.openai.images.generate({
        model: 'dall-e-3',
        prompt: promptData,
        n: 1,
        size: quality === 'hd' ? '1792x1024' : '1024x1024',
        quality: quality,
        response_format: 'url',
      });

      const imageUrl = response.data[0].url;
      await this.downloadImage(imageUrl, outputPath);

      console.log(`Generated: ${fullPath}`);
      this.stats.generated++;
      this.stats.totalCost += quality === 'hd' ? 0.08 : 0.04;

      return { success: true, generated: true };
    } catch (error) {
      console.error(`Failed to generate ${fullPath}: ${error.message}`);
      this.stats.failed++;
      return { success: false, generated: false };
    }
  }

  async downloadImage(url, outputPath) {
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const response = await axios({
      method: 'GET',
      url: url,
      responseType: 'stream',
    });

    const writer = fs.createWriteStream(outputPath);
    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
      writer.on('finish', resolve);
      writer.on('error', reject);
    });
  }

  getPromptForPath(pathInfo) {
    const { category, subcategory, type } = pathInfo;

    switch (category) {
      case 'landing':
        return this.prompts.landing?.[type];
      case 'features':
        return this.prompts.features?.[subcategory]?.[type];
      case 'useCases':
        return this.prompts.useCases?.[subcategory]?.[type];
      case 'sources':
        return this.prompts.sources?.[subcategory]?.[type];
      case 'resources':
        return this.prompts.resources?.[subcategory]?.[type];
      case 'pages':
        return this.prompts.pages?.[subcategory]?.[type];
      default:
        return null;
    }
  }

  // 2. SEO Image Generation
  async generateSEOImages(imagePaths) {
    console.log('Starting SEO image generation...\n');

    for (const pathInfo of imagePaths) {
      await this.generateSEOImage(pathInfo);
    }

    return this.stats;
  }

  async generateSEOImage(pathInfo) {
    const seoPath = pathInfo.path.replace(/\.(jpg|jpeg|png|webp)$/i, '_seo.jpg');

    if (fileExists(seoPath)) {
      this.stats.skipped++;
      return { success: true, generated: false };
    }

    const originalExists = fileExists(pathInfo.path);
    if (!originalExists) {
      this.stats.skipped++;
      return { success: false, generated: false };
    }

    try {
      console.log(`Generating SEO: ${path.basename(seoPath)}...`);

      const canvas = createCanvas(1200, 630);
      const ctx = canvas.getContext('2d');

      // Load and draw original image
      const originalImage = await loadImage(pathInfo.path);
      ctx.drawImage(originalImage, 0, 0, 1200, 630);

      // Add overlay and text
      ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
      ctx.fillRect(0, 0, 1200, 630);

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 48px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(this.appName, 600, 300);

      ctx.font = '32px Arial';
      ctx.fillText(this.getSEOText(pathInfo), 600, 350);

      // Save SEO image
      const dir = path.dirname(seoPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      const buffer = canvas.toBuffer('image/jpeg', { quality: 0.9 });
      fs.writeFileSync(seoPath, buffer);

      console.log(`Generated SEO: ${path.basename(seoPath)}`);
      this.stats.seoGenerated++;
      return { success: true, generated: true };
    } catch (error) {
      console.error(`Failed to generate SEO ${seoPath}: ${error.message}`);
      this.stats.failed++;
      return { success: false, generated: false };
    }
  }

  getSEOText(pathInfo) {
    const { category, subcategory } = pathInfo;

    if (subcategory) {
      const formatted = subcategory.charAt(0).toUpperCase() + subcategory.slice(1);
      return `${formatted} ${category}`;
    }

    return category.charAt(0).toUpperCase() + category.slice(1);
  }

  // 3. Image Optimization
  async optimizeAllImages() {
    console.log('Starting image optimization...\n');

    const outputDir = process.env.IMAGE_OUTPUT_DIR || './output';
    const imagePattern = path.join(outputDir, '**/*.{jpg,jpeg,png,webp}');
    const imageFiles = await glob(imagePattern, { cwd: process.cwd() });

    for (const imagePath of imageFiles) {
      await this.optimizeImage(imagePath);
    }

    return this.stats;
  }

  async optimizeImage(imagePath) {
    try {
      console.log(`Optimizing: ${path.basename(imagePath)}...`);

      const imageBuffer = fs.readFileSync(imagePath);
      const targetSize = this.getTargetSize(imagePath);

      let optimizedBuffer = sharp(imageBuffer)
        .resize(targetSize.width, targetSize.height, {
          fit: 'cover',
          position: 'center',
        })
        .jpeg(this.optimizationConfig.jpeg);

      const outputBuffer = await optimizedBuffer.toBuffer();
      fs.writeFileSync(imagePath, outputBuffer);

      console.log(`Optimized: ${path.basename(imagePath)}`);
      this.stats.optimized++;
      return { success: true };
    } catch (error) {
      console.error(`Failed to optimize ${imagePath}: ${error.message}`);
      this.stats.failed++;
      return { success: false };
    }
  }

  getTargetSize(imagePath) {
    const basename = path.basename(imagePath);

    for (const [type, size] of Object.entries(this.sizeConfig)) {
      if (basename.includes(type)) {
        return size;
      }
    }

    return { width: 800, height: 600 }; // default
  }

  // Cost estimation
  estimateCost(imagePaths, quality = 'hd') {
    const validPaths = imagePaths.filter(p => this.getPromptForPath(p));
    const costPerImage = quality === 'hd' ? 0.08 : 0.04;
    const totalCost = validPaths.length * costPerImage;

    return {
      totalImages: validPaths.length,
      costPerImage: costPerImage,
      totalCost: totalCost.toFixed(2),
      validPaths,
    };
  }

  getStats() {
    return {
      ...this.stats,
      totalCostFormatted: `$${this.stats.totalCost.toFixed(2)}`,
    };
  }

  resetStats() {
    this.stats = {
      generated: 0,
      seoGenerated: 0,
      optimized: 0,
      skipped: 0,
      failed: 0,
      totalCost: 0,
    };
  }
}

module.exports = { ImageGenerator };
