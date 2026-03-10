# Camera & Segmentation (Mirror System)

## Overview

Real-time person segmentation for the projector display. Captures camera → segments person → composites on transparent background → WebP → base64 → WebSocket → projector.

## Key Files

### `backend/mirror_service.py`
- `MirrorSegmenter` class — Camera capture + person segmentation
- **Thread safety**: Dedicated single-thread `ThreadPoolExecutor` for all OpenCV/camera operations (AVFoundation on macOS requires same-thread access)
- Mask refinement pipeline: sigmoid threshold → morphological operations → distance-transform edge feathering
- Output resized to `MIRROR_OUTPUT_WIDTH` (default 960px) before WebP encoding for performance
- CPU-heavy work offloaded via `asyncio.to_thread`

### `backend/vision_segmenter.py`
- Apple Vision Framework wrapper (macOS only, via PyObjC)
- Input resized to 1024×768 before CGImage conversion for Neural Engine efficiency
- Quality levels: 0=fast, 1=balanced, 2=accurate (default)

### Segmenter Selection
Automatic selection via `MIRROR_SEGMENTER` env var:
- `auto` (default) — Vision Framework on macOS, MediaPipe on Linux
- `vision` — Force Apple Vision (macOS only)
- `mediapipe` — Force MediaPipe (cross-platform)

## Environment Variables

All optional, set in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MIRROR_CAMERA_INDEX` | 0 | Camera device index |
| `MIRROR_WIDTH` | 1920 | Capture width |
| `MIRROR_HEIGHT` | 1080 | Capture height |
| `MIRROR_FPS` | 30 | Target framerate |
| `MIRROR_OUTPUT_WIDTH` | 960 | Output width before WebP encoding |
| `MIRROR_SEG_WIDTH` | 640 | Segmentation internal resolution (MediaPipe) |
| `MIRROR_WEBP_QUALITY` | 60 | WebP quality 0-100 |
| `MIRROR_MASK_BLUR` | 7 | Mask blur kernel size (odd number) |
| `MIRROR_MASK_THRESHOLD` | 0.5 | Mask cutoff 0.0-1.0 |
| `MIRROR_EDGE_FEATHER` | 15 | Edge feather width in px |
| `MIRROR_MORPH_SIZE` | 5 | Morphology kernel size |
| `MIRROR_VISION_QUALITY` | 2 | Vision quality: 0=fast, 1=balanced, 2=accurate |
| `MIRROR_SEGMENTER` | auto | Backend: auto/vision/mediapipe |

## Important Notes

- Docker container cannot access host camera without `devices:` config on Linux
- On Mac Studio, run backend natively (not in Docker) for camera access
- MediaPipe is the fallback for non-macOS environments (WSL2, Linux)
