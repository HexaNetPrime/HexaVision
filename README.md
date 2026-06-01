# 🔍 HexaVision Enterprise v9.0

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)

### Professional Image Forensics Suite | Camera Fingerprinting | Face Detection

**🔬 AI-Powered | 🔐 Forensic Ready | 🌍 Open Source**

</div>

---

## 📸 What is HexaVision?

HexaVision is a **professional image forensics tool** that helps you:
- 🔍 Extract hidden metadata (EXIF, GPS)
- 👤 Detect and match faces
- 🔬 Identify exact camera device using **PRNU fingerprinting**
- ⚠️ Detect image manipulation (ELA)
- 🕵️ Find steganography hidden data
- 🌍 Reverse image search on Google/TinEye/Yandex

> **Perfect for:** Journalists, Forensic Analysts, Security Researchers, Privacy Advocates

---

## ✨ Features

| Module | Description | Status |
|--------|-------------|--------|
| 📷 **EXIF Extraction** | Camera model, date, settings | ✅ |
| 📍 **GPS Location** | Coordinates + Google Maps link | ✅ |
| 🔬 **PRNU Fingerprinting** | Unique camera noise pattern (NEW!) | ✅ |
| 👤 **Face Detection** | Find faces in images | ✅ |
| 👥 **Face Matching** | Compare two faces | ✅ |
| 🔐 **Steganography Detection** | LSB + Entropy analysis | ✅ |
| 🖼️ **Error Level Analysis (ELA)** | Detect image editing | ✅ |
| 🔍 **Reverse Image Search** | Google/TinEye/Yandex | ✅ |
| 📅 **Timeline Analysis** | File creation/modification history | ✅ |
| 🌍 **Deep GPS Analysis** | City, state, country from coordinates | ✅ |
| 💾 **Export Reports** | HTML / JSON format | ✅ |

---

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/hexavision.git
cd hexavision
pip install opencv-python pillow exifread numpy pywavelets
python hexavision_ai.py
