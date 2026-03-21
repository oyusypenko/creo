#!/usr/bin/env node

/**
 * Creo Image Generation Extension
 * Supports DALL-E 3 and ComfyUI (Stable Diffusion XL)
 */

require('dotenv').config();

const { ImageGenerator } = require('./lib/ImageGenerator');

function showMainHelp() {
  console.log('Creo Image Generation Extension');
  console.log('\nUsage: node index.js generate [options]');
  console.log('\nOptions:');
  console.log('  --estimate        Show cost estimation only');
  console.log('  --seo-only        Generate only SEO images');
  console.log('  --optimize-only   Optimize existing images only');
  console.log('  --help            Show help message');
  console.log('\nEnvironment Variables:');
  console.log('  OPENAI_API_KEY    OpenAI API key (required)');
  console.log('  IMAGE_CONFIG_DIR  Directory with paths.js config');
  console.log('  IMAGE_OUTPUT_DIR  Directory for generated images');
  console.log('  PROMPTS_FILE      Path to prompts.js file');
  console.log('  APP_NAME          App name for SEO images');
  console.log('\nExamples:');
  console.log('  npm run generate');
  console.log('  npm run generate-estimate');
  console.log('  npm run seo-only');
  console.log('  npm run optimize-only');
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const commandArgs = args.slice(1);

  try {
    if (command === 'generate' || !command) {
      const generator = new ImageGenerator();
      return await generator.execute(['generate', ...commandArgs]);
    } else if (command === 'help' || command === '--help' || command === '-h') {
      showMainHelp();
      return;
    } else {
      console.error(`Unknown command: ${command}`);
      console.log('\nRun "npm run generate --help" for available options.');
      process.exit(1);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { ImageGenerator, main };
