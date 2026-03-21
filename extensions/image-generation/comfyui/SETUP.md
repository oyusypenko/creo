# ComfyUI Setup Guide for Image Generation

## System Requirements
- **GPU:** NVIDIA GPU with 8GB+ VRAM (RTX 3060+ recommended)
- **Python:** 3.10+
- **Node.js:** 18+

## Quick Start

### Option 1: Portable Version (Recommended for Windows)

1. **Download ComfyUI Portable:**
   ```
   https://github.com/comfyanonymous/ComfyUI/releases
   ```
   Download: `ComfyUI_windows_portable_nvidia.7z`

2. **Extract** to `C:\ComfyUI\`

3. **Run:** Double-click `run_nvidia_gpu.bat`

4. **Open browser:** http://127.0.0.1:8188

---

### Option 2: Manual Installation (More Control)

```bash
# 1. Clone ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# 3. Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 4. Install ComfyUI dependencies
pip install -r requirements.txt

# 5. Run ComfyUI
python main.py
```

---

## Recommended Models for Marketing Images

### Base Models (Choose One)

| Model | Size | Quality | Style |
|-------|------|---------|-------|
| **SDXL 1.0** | 6.5GB | Excellent | Versatile |
| **Juggernaut XL** | 6.5GB | Excellent | Photorealistic |
| **RealVisXL** | 6.5GB | Excellent | Photography |
| **Dreamshaper XL** | 6.5GB | Good | Artistic |

### Download Links

**SDXL Base (Required):**
```
https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
```
Save to: `ComfyUI/models/checkpoints/`

**RealVisXL (Photorealistic - Recommended for marketing):**
```
https://civitai.com/models/139562/realvisxl-v50
```

**Juggernaut XL (Alternative):**
```
https://civitai.com/models/133005/juggernaut-xl
```

---

## Model Folder Structure

```
ComfyUI/
  models/
    checkpoints/          # Main models (.safetensors)
      sd_xl_base_1.0.safetensors
      realvisxl_v50.safetensors
    vae/                  # VAE models
      sdxl_vae.safetensors
    loras/                # LoRA models (style fine-tuning)
    controlnet/           # ControlNet models
    upscale_models/       # Upscalers
      4x-UltraSharp.pth
```

---

## Recommended Additional Downloads

### VAE (Better colors):
```
https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors
```
Save to: `ComfyUI/models/vae/`

### Upscaler (4K output):
```
https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x-UltraSharp.pth
```
Save to: `ComfyUI/models/upscale_models/`

---

## Recommended Settings for Marketing Images

### Resolution (SDXL optimal):
- **Hero images:** 1344 x 768 (landscape)
- **OG images:** 1200 x 630 (social preview)
- **Cards:** 1024 x 1024 (square)
- **Mobile:** 768 x 1344 (portrait)

### Quality Settings:
- **Steps:** 25-35
- **CFG Scale:** 7-8
- **Sampler:** DPM++ 2M Karras
- **Scheduler:** Karras

---

## Essential Custom Nodes

Install via ComfyUI Manager:

1. **ComfyUI Manager** (install first):
   ```
   cd ComfyUI/custom_nodes
   git clone https://github.com/ltdrdata/ComfyUI-Manager.git
   ```

2. After restart, use Manager to install:
   - **WAS Node Suite** - extra image tools
   - **rgthree's Nodes** - workflow utilities
   - **Efficiency Nodes** - batch processing

---

## Quick Test

1. Start ComfyUI
2. Load default workflow (drag image or JSON)
3. Set prompt: `Professional modern office, natural lighting, documentary style photography`
4. Set negative: `cartoon, anime, illustration, painting, drawing, blurry, low quality`
5. Click "Queue Prompt"

---

## Integration with Creo

Once ComfyUI is running, use the batch generator:

```bash
# Generate all marketing images
node comfyui/generate-batch.js --prompts path/to/prompts.js

# Generate landing page images only
node comfyui/generate-batch.js landing --prompts path/to/prompts.js

# Generate with custom output folder
node comfyui/generate-batch.js -o campaign-v2 --prompts path/to/prompts.js
```
