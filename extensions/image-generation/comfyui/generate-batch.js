/**
 * Batch Image Generator for ComfyUI
 * Generates marketing images using Stable Diffusion XL via ComfyUI
 *
 * Usage:
 *   node generate-batch.js                           # Generate all images
 *   node generate-batch.js landing                   # Generate landing page images only
 *   node generate-batch.js features audio            # Generate specific feature images
 *   node generate-batch.js --output my-folder        # Save to custom folder
 *   node generate-batch.js landing -o campaign-v2    # Combine options
 */

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

// Configuration
const COMFYUI_URL = process.env.COMFYUI_URL || 'http://127.0.0.1:8000';
const COMFYUI_OUTPUT_DIR = process.env.COMFYUI_OUTPUT_DIR || path.join(__dirname, '..', '..', 'output', 'comfyui');
const PROJECT_OUTPUT_DIR = process.env.PROJECT_OUTPUT_DIR || path.join(__dirname, '..', '..', 'output', 'marketing');
const CLIENT_ID = `batch-generator-${Date.now()}`;

// Parse CLI arguments
function parseArgs(args) {
  const result = {
    category: null,
    subcategory: null,
    outputFolder: 'marketing',
    help: false,
    promptsFile: null,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--help' || arg === '-h') {
      result.help = true;
    } else if (arg === '--output' || arg === '-o') {
      result.outputFolder = args[++i] || 'marketing';
    } else if (arg === '--prompts' || arg === '-p') {
      result.promptsFile = args[++i];
    } else if (!arg.startsWith('-')) {
      if (!result.category) {
        result.category = arg;
      } else if (!result.subcategory) {
        result.subcategory = arg;
      }
    }
  }

  return result;
}

// Load prompts from file
function loadPrompts(promptsFile) {
  const file = promptsFile || process.env.PROMPTS_FILE;

  if (file && fs.existsSync(file)) {
    try {
      const { CONTEXT_AWARE_PROMPTS } = require(path.resolve(file));
      return CONTEXT_AWARE_PROMPTS;
    } catch (error) {
      console.error(`Could not load prompts from ${file}: ${error.message}`);
    }
  }

  console.error('No prompts file found. Provide --prompts <file> or set PROMPTS_FILE env var.');
  process.exit(1);
}

// Image size presets for SDXL
const SIZE_PRESETS = {
  hero: { width: 1344, height: 768 }, // Landscape for hero sections
  heroMobile: { width: 768, height: 1344 }, // Portrait for mobile
  ogImage: { width: 1200, height: 630 }, // Social media preview
  card: { width: 1024, height: 1024 }, // Square cards
  thumbnail: { width: 512, height: 512 }, // Small thumbnails
};

// Negative prompt for photorealistic images
const NEGATIVE_PROMPT = `cartoon, anime, illustration, painting, drawing, sketch,
blurry, low quality, watermark, text, logo, ugly, deformed, disfigured,
bad anatomy, bad proportions, extra limbs, cloned face, mutated hands,
poorly drawn face, mutation, mutilated, out of frame, extra fingers,
extra arms, extra legs, poorly drawn hands, missing fingers, fused fingers`;

// Base workflow template
function createWorkflow(prompt, negativePrompt, width, height, filename) {
  return {
    prompt: {
      1: {
        class_type: 'CheckpointLoaderSimple',
        inputs: {
          ckpt_name: 'realvisxlV50_v50Bakedvae.safetensors',
        },
      },
      2: {
        class_type: 'CLIPTextEncode',
        inputs: {
          text: prompt + ', professional photography, 8k, sharp focus, high quality',
          clip: ['1', 1],
        },
      },
      3: {
        class_type: 'CLIPTextEncode',
        inputs: {
          text: negativePrompt,
          clip: ['1', 1],
        },
      },
      4: {
        class_type: 'EmptyLatentImage',
        inputs: {
          width: width,
          height: height,
          batch_size: 1,
        },
      },
      5: {
        class_type: 'KSampler',
        inputs: {
          seed: Math.floor(Math.random() * 1000000000),
          steps: 30,
          cfg: 7.5,
          sampler_name: 'dpmpp_2m',
          scheduler: 'karras',
          denoise: 1,
          model: ['1', 0],
          positive: ['2', 0],
          negative: ['3', 0],
          latent_image: ['4', 0],
        },
      },
      6: {
        class_type: 'VAEDecode',
        inputs: {
          samples: ['5', 0],
          vae: ['1', 2],
        },
      },
      7: {
        class_type: 'SaveImage',
        inputs: {
          filename_prefix: filename,
          images: ['6', 0],
        },
      },
    },
  };
}

// Queue prompt to ComfyUI
async function queuePrompt(workflow) {
  const response = await fetch(`${COMFYUI_URL}/prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: workflow.prompt,
      client_id: CLIENT_ID,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to queue prompt: ${response.statusText}`);
  }

  return response.json();
}

// Wait for generation to complete
function waitForCompletion(promptId) {
  return new Promise((resolve, reject) => {
    const wsUrl = COMFYUI_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws?clientId=${CLIENT_ID}`);

    ws.on('message', data => {
      const message = JSON.parse(data);

      if (message.type === 'executing') {
        if (message.data.node === null && message.data.prompt_id === promptId) {
          ws.close();
          resolve();
        }
      }

      if (message.type === 'execution_error') {
        ws.close();
        reject(new Error(message.data.exception_message));
      }
    });

    ws.on('error', reject);

    // Timeout after 5 minutes
    setTimeout(() => {
      ws.close();
      reject(new Error('Generation timeout'));
    }, 300000);
  });
}

// Copy generated files from ComfyUI output to project output
function copyGeneratedFiles(sourceFolder, destFolder) {
  const sourcePath = path.join(COMFYUI_OUTPUT_DIR, sourceFolder);
  const destPath = path.join(PROJECT_OUTPUT_DIR, destFolder);

  if (!fs.existsSync(sourcePath)) {
    console.log(`  No files to copy from ${sourcePath}`);
    return 0;
  }

  // Create destination directory
  if (!fs.existsSync(destPath)) {
    fs.mkdirSync(destPath, { recursive: true });
  }

  // Copy all PNG files
  const files = fs.readdirSync(sourcePath).filter(f => f.endsWith('.png'));
  for (const file of files) {
    const src = path.join(sourcePath, file);
    const dest = path.join(destPath, file);
    fs.copyFileSync(src, dest);
  }

  return files.length;
}

// Flatten prompts into generation tasks
function flattenPrompts(prompts, category = null, subcategory = null) {
  const tasks = [];

  function processLevel(obj, currentPath = []) {
    for (const [key, value] of Object.entries(obj)) {
      const nextPath = [...currentPath, key];

      if (typeof value === 'string') {
        // This is a prompt
        const imageType = key;
        const size = SIZE_PRESETS[imageType] || SIZE_PRESETS.hero;
        const filename = nextPath.join('/');

        tasks.push({
          path: nextPath,
          prompt: value,
          size,
          filename,
          imageType,
        });
      } else if (typeof value === 'object') {
        // Nested category
        processLevel(value, nextPath);
      }
    }
  }

  // Filter by category/subcategory if specified
  let targetPrompts = prompts;
  if (category && prompts[category]) {
    targetPrompts = { [category]: prompts[category] };
    if (subcategory && prompts[category][subcategory]) {
      targetPrompts = { [category]: { [subcategory]: prompts[category][subcategory] } };
    }
  }

  processLevel(targetPrompts);
  return tasks;
}

// Main generation function
async function generateImages(options) {
  const { category, subcategory, outputFolder, promptsFile } = options;
  const fullOutputPath = path.join(COMFYUI_OUTPUT_DIR, outputFolder);

  console.log('========================================');
  console.log('  ComfyUI Batch Image Generator');
  console.log('========================================\n');

  // Check if ComfyUI is running
  try {
    const health = await fetch(`${COMFYUI_URL}/system_stats`);
    if (!health.ok) throw new Error();
    console.log('+ ComfyUI is running');
  } catch {
    console.error('- ComfyUI is not running!');
    console.error('  Start ComfyUI Desktop first\n');
    process.exit(1);
  }

  console.log(`+ Output folder: ${fullOutputPath}\n`);

  // Load prompts
  const prompts = loadPrompts(promptsFile);

  // Get generation tasks
  const tasks = flattenPrompts(prompts, category, subcategory);
  console.log(`Found ${tasks.length} images to generate\n`);

  if (tasks.length === 0) {
    console.log('No matching prompts found.');
    console.log('Available categories:', Object.keys(prompts).join(', '));
    return;
  }

  // Generate each image
  let completed = 0;
  let failed = 0;

  for (const task of tasks) {
    const { prompt, size, filename } = task;

    console.log(`[${completed + failed + 1}/${tasks.length}] ${filename}`);
    console.log(`  Size: ${size.width}x${size.height}`);

    try {
      // Create workflow with custom output folder
      const workflow = createWorkflow(
        prompt,
        NEGATIVE_PROMPT,
        size.width,
        size.height,
        `${outputFolder}/${filename.replace(/\//g, '_')}`
      );

      // Queue and wait
      const { prompt_id } = await queuePrompt(workflow);
      console.log(`  Queued: ${prompt_id}`);

      await waitForCompletion(prompt_id);
      console.log('  + Completed\n');
      completed++;
    } catch (error) {
      console.log(`  - Failed: ${error.message}\n`);
      failed++;
    }
  }

  // Copy files to project folder
  console.log('Copying files to project folder...');
  const copiedCount = copyGeneratedFiles(outputFolder, outputFolder);

  const projectOutputPath = path.join(PROJECT_OUTPUT_DIR, outputFolder);

  // Summary
  console.log('========================================');
  console.log('  Generation Complete');
  console.log('========================================');
  console.log(`  + Generated: ${completed}`);
  console.log(`  - Failed: ${failed}`);
  console.log(`  Copied: ${copiedCount} files`);
  console.log(`\n  Output: ${projectOutputPath}`);
}

// CLI
const args = process.argv.slice(2);
const options = parseArgs(args);

if (options.help) {
  console.log(`
ComfyUI Batch Image Generator (Creo Extension)

Usage: node generate-batch.js [category] [subcategory] [options]

Options:
  -o, --output <folder>    Output folder name (default: marketing)
  -p, --prompts <file>     Path to prompts.js file
  -h, --help               Show this help

Examples:
  node generate-batch.js                              # All images
  node generate-batch.js landing                      # Landing only
  node generate-batch.js -o campaign-v2               # All with custom output
  node generate-batch.js landing -o landing-test      # Landing with custom output
  node generate-batch.js features audio -o audio-v1   # Specific feature

Environment:
  COMFYUI_URL          ComfyUI server URL (default: http://127.0.0.1:8000)
  PROMPTS_FILE         Path to prompts.js file
  COMFYUI_OUTPUT_DIR   ComfyUI output directory
  PROJECT_OUTPUT_DIR   Project output directory

Output: ${PROJECT_OUTPUT_DIR}/<folder>/
`);
  process.exit(0);
}

generateImages(options).catch(console.error);
