# Creo Image Generation Extension

Optional Creo extension that adds AI-powered image generation using DALL-E 3 (cloud) and ComfyUI with Stable Diffusion XL (local).

## Prerequisites

- **Node.js 18+**
- **Creo core** installed (`~/.claude/skills/creo/`)
- **OPENAI_API_KEY** for DALL-E 3 generation
- **ComfyUI** (optional) for local Stable Diffusion XL generation -- see `comfyui/SETUP.md`

## Install

```bash
# macOS / Linux
chmod +x install.sh
./install.sh

# Windows (PowerShell)
.\install.ps1
```

## Usage

### DALL-E 3 (Cloud)

```bash
# Estimate cost before generating
/creo image-generation estimate

# Generate all images
/creo image-generation generate

# Generate SEO overlay images only
/creo image-generation generate --seo-only

# Optimize existing images (resize + compress)
/creo image-generation optimize
```

### ComfyUI (Local GPU)

Requires ComfyUI running locally. See `comfyui/SETUP.md` for setup.

```bash
# Generate all categories
/creo image-generation comfyui

# Generate specific category
/creo image-generation comfyui landing
/creo image-generation comfyui features audio
```

### Direct Node.js usage

```bash
cd ~/.claude/skills/creo-image-generation

# DALL-E 3
OPENAI_API_KEY=sk-... node index.js generate
OPENAI_API_KEY=sk-... node index.js generate --estimate
node index.js generate --optimize-only

# ComfyUI
node comfyui/generate-batch.js
node comfyui/generate-batch.js landing
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (DALL-E) | OpenAI API key |
| `IMAGE_CONFIG_DIR` | No | Directory with `paths.js` config |
| `IMAGE_OUTPUT_DIR` | No | Output directory for generated images |
| `PROMPTS_FILE` | No | Path to prompts.js with generation prompts |
| `APP_NAME` | No | App name for SEO image overlays |
| `COMFYUI_URL` | No | ComfyUI URL (default: `http://127.0.0.1:8000`) |

## Cost Reference (DALL-E 3)

| Quality | Resolution | Cost |
|---------|-----------|------|
| Standard | 1024x1024 | $0.040 / image |
| HD | 1792x1024 | $0.080 / image |

## Uninstall

```bash
# macOS / Linux
chmod +x uninstall.sh
./uninstall.sh

# Windows (PowerShell)
.\uninstall.ps1
```
