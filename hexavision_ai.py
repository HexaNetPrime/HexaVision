#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    HEXAVISION ENTERPRISE v9.0 - FINAL                        ║
║    Image Forensics | Face Detection | Face Matching | PRNU Camera Fingerprint║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
import os
import json
import hashlib
from datetime import datetime
import webbrowser
import threading
import numpy as np
import io
import urllib.request
import urllib.parse
import math
import warnings
warnings.filterwarnings('ignore')

try:
    from PIL import Image, ImageTk, ImageChops
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

try:
    import exifread
    EXIF_AVAILABLE = True
except:
    EXIF_AVAILABLE = False

# OpenCV for face detection
try:
    import cv2
    CV2_AVAILABLE = True
except:
    CV2_AVAILABLE = False

# PyWavelets for PRNU analysis
try:
    import pywt
    PYWT_AVAILABLE = True
except:
    PYWT_AVAILABLE = False

class HexaVision:
    def __init__(self, root):
        self.root = root
        self.root.title("HexaVision Enterprise v9.0 - Camera Fingerprinting")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(1400, screen_width - 100)
        height = min(800, screen_height - 100)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg='#0a0e27')
        self.root.minsize(1200, 700)
        
        # Variables
        self.current_images = []
        self.current_index = 0
        self.metadata_cache = {}
        self.current_page = 0
        self.total_pages = 14
        self.pages = []
        self.page_indicators = []
        self.thumbnail_data = None
        self.ela_running = False
        self.face_cascade = None
        self.face1_path = ""
        self.face2_path = ""
        
        # PRNU Database - store fingerprints for known cameras
        self.prnu_database = {}  # {device_id: fingerprint_array}
        self.prnu_reference_image = None
        
        # Colors
        self.colors = {
            'bg': '#0a0e27', 'card': '#131b3c', 'header': '#0f1535',
            'accent': '#00d9ff', 'accent2': '#ff0066', 'success': '#00ff88',
            'warning': '#ffaa00', 'danger': '#ff3366', 'text': '#ffffff', 'text2': '#a0aec0'
        }
        
        # Fonts
        self.fonts = {
            'title': Font(family="Orbitron", size=14, weight="bold"),
            'heading': Font(family="Segoe UI", size=11, weight="bold"),
            'normal': Font(family="Segoe UI", size=10),
            'small': Font(family="Segoe UI", size=9),
            'mono': Font(family="Consolas", size=9)
        }
        
        # Create UI
        self.create_menu()
        self.create_header()
        self.create_main_frame()
        self.create_statusbar()
        self.bind_shortcuts()
        
        # Load face cascade
        self.load_face_cascade()
        
        self.update_status("Ready - Click 'Open' to start")
        
    def load_face_cascade(self):
        """Load OpenCV face detection cascade"""
        try:
            if CV2_AVAILABLE:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                if hasattr(self, 'face_status'):
                    self.face_status.config(text="👤 Face: Ready", fg=self.colors['success'])
                print("Face cascade loaded")
            else:
                if hasattr(self, 'face_status'):
                    self.face_status.config(text="👤 Face: OpenCV not installed", fg=self.colors['danger'])
        except Exception as e:
            print(f"Face cascade error: {e}")
            
    def create_menu(self):
        menubar = tk.Menu(self.root, bg=self.colors['header'], fg=self.colors['text'])
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image(s)", command=self.open_images, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Folder", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save HTML", command=self.save_html, accelerator="Ctrl+S")
        file_menu.add_command(label="Export JSON", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Strip Metadata", command=self.strip_metadata)
        tools_menu.add_command(label="Hash Analysis", command=self.hash_analysis)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_header(self):
        header = tk.Frame(self.root, bg=self.colors['header'], height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🔍 HEXAVISION v9.0 - CAMERA FINGERPRINTING", 
                        bg=self.colors['header'], fg=self.colors['accent'],
                        font=self.fonts['title'])
        title.pack(side=tk.LEFT, padx=20)
        
        self.img_count = tk.Label(header, text="📷 0 images", 
                                   bg=self.colors['header'], fg=self.colors['success'],
                                   font=self.fonts['normal'])
        self.img_count.pack(side=tk.RIGHT, padx=20)
        
        self.face_status = tk.Label(header, text="👤 Face: Loading...", 
                                     bg=self.colors['header'], fg=self.colors['warning'],
                                     font=self.fonts['small'])
        self.face_status.pack(side=tk.RIGHT, padx=10)
        
        self.prnu_status = tk.Label(header, text="🔬 PRNU: " + ("Ready" if PYWT_AVAILABLE else "Not Available"), 
                                     bg=self.colors['header'], fg=self.colors['success'] if PYWT_AVAILABLE else self.colors['danger'],
                                     font=self.fonts['small'])
        self.prnu_status.pack(side=tk.RIGHT, padx=10)
        
    def create_main_frame(self):
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Navigation
        nav_frame = tk.Frame(main, bg=self.colors['header'], height=35)
        nav_frame.pack(fill=tk.X, pady=(0, 8))
        nav_frame.pack_propagate(False)
        
        btn_frame = tk.Frame(nav_frame, bg=self.colors['header'])
        btn_frame.pack(pady=5)
        
        self.prev_btn = tk.Button(btn_frame, text="◀ PREV", command=self.prev_page,
                                   bg=self.colors['card'], fg=self.colors['text'],
                                   font=self.fonts['small'], padx=12)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        for i in range(1, 15):
            lbl = tk.Label(btn_frame, text=f"  {i}  ", bg=self.colors['card'],
                          fg=self.colors['text2'], font=self.fonts['small'])
            lbl.pack(side=tk.LEFT, padx=2)
            self.page_indicators.append(lbl)
            
        self.next_btn = tk.Button(btn_frame, text="NEXT ▶", command=self.next_page,
                                   bg=self.colors['card'], fg=self.colors['text'],
                                   font=self.fonts['small'], padx=12)
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
        self.pages_container = tk.Frame(main, bg=self.colors['bg'])
        self.pages_container.pack(fill=tk.BOTH, expand=True)
        
        # Create all 14 pages
        self.create_page1()
        self.create_page2()
        self.create_page3()
        self.create_page4()
        self.create_page5()
        self.create_page6()
        self.create_page7()
        self.create_page8()
        self.create_page9()
        self.create_page10()
        self.create_page11()
        self.create_page12()
        self.create_page13()
        self.create_page14()  # PRNU Camera Fingerprinting
        
        self.show_page(0)
        
    def create_page1(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        for i in range(3):
            page.columnconfigure(i, weight=1)
        page.rowconfigure(0, weight=1)
        
        f1 = tk.LabelFrame(page, text="📷 IMAGE", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f1.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.create_image_box(f1)
        
        f2 = tk.LabelFrame(page, text="📷 EXIF DATA", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f2.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        self.create_exif_box(f2)
        
        f3 = tk.LabelFrame(page, text="📍 GPS LOCATION", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f3.grid(row=0, column=2, padx=4, pady=4, sticky="nsew")
        self.create_gps_box(f3)
        
    def create_page2(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        for i in range(2):
            page.columnconfigure(i, weight=1)
        page.rowconfigure(0, weight=1)
        
        f1 = tk.LabelFrame(page, text="📁 FILE INFO", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f1.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.create_fileinfo_box(f1)
        
        f2 = tk.LabelFrame(page, text="⚠️ RISK", fg=self.colors['warning'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f2.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        self.create_risk_box(f2)
        
    def create_page3(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        for i in range(2):
            page.columnconfigure(i, weight=1)
        page.rowconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        
        f1 = tk.LabelFrame(page, text="📊 STATISTICS", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f1.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.create_stats_box(f1)
        
        f2 = tk.LabelFrame(page, text="💀 DANGER", fg=self.colors['danger'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f2.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")
        self.create_danger_box(f2)
        
        f3 = tk.LabelFrame(page, text="🛠️ TOOLS", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f3.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        self.create_tools_box(f3)
        
        f4 = tk.LabelFrame(page, text="🔍 QUICK ANALYSIS", fg=self.colors['accent'],
                          bg=self.colors['card'], font=self.fonts['heading'])
        f4.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")
        self.create_analysis_box(f4)
        
    def create_page4(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="🔬 ERROR LEVEL ANALYSIS", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="Compression Quality: 90 (DEFAULT)\n• Bright areas = Edited\n• Dark areas = Original", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        quality_frame = tk.Frame(left_frame, bg=self.colors['card'])
        quality_frame.pack(pady=10)
        
        tk.Label(quality_frame, text="Quality (70-99):", bg=self.colors['card'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.ela_quality = tk.IntVar(value=90)
        scale = tk.Scale(quality_frame, from_=70, to=99, orient=tk.HORIZONTAL,
                         variable=self.ela_quality, bg=self.colors['card'],
                         fg=self.colors['text'], length=150)
        scale.pack(side=tk.LEFT, padx=10)
        
        self.ela_btn = tk.Button(left_frame, text="🔬 RUN ELA", command=self.run_ela,
                                  bg=self.colors['accent2'], fg='white',
                                  font=self.fonts['heading'], pady=8, width=20)
        self.ela_btn.pack(pady=10)
        
        self.ela_progress = ttk.Progressbar(left_frame, length=200, mode='indeterminate')
        self.ela_progress.pack(pady=5)
        
        result_label = tk.Label(right_frame, text="📊 ELA RESULT", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.ela_image_label = tk.Label(right_frame, text="Result will appear here",
                                         bg=self.colors['card'], fg=self.colors['text2'],
                                         font=self.fonts['normal'])
        self.ela_image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        score_frame = tk.Frame(right_frame, bg=self.colors['card'])
        score_frame.pack(fill=tk.X, pady=5)
        tk.Label(score_frame, text="Score:", bg=self.colors['card'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        self.ela_score = tk.Label(score_frame, text="Not analyzed", bg=self.colors['card'],
                                   fg=self.colors['accent2'])
        self.ela_score.pack(side=tk.LEFT, padx=10)
        
    def create_page5(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="🖼️ THUMBNAIL EXTRACTION", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="सिर्फ JPEG फाइलों पर काम करता है\n\nअगर थंबनेल और मेन फोटो में अंतर है\nतो फोटो एडिटेड है!", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        self.thumb_btn = tk.Button(left_frame, text="🔍 EXTRACT THUMBNAIL", command=self.extract_thumbnail,
                                    bg=self.colors['accent2'], fg='white',
                                    font=self.fonts['heading'], pady=8, width=20)
        self.thumb_btn.pack(pady=10)
        
        self.save_thumb_btn = tk.Button(left_frame, text="💾 SAVE THUMBNAIL", command=self.save_thumbnail,
                                         bg=self.colors['accent'], fg='#0a0e27',
                                         font=self.fonts['heading'], pady=8, width=20, state=tk.DISABLED)
        self.save_thumb_btn.pack(pady=5)
        
        self.thumb_progress = ttk.Progressbar(left_frame, length=200, mode='indeterminate')
        self.thumb_progress.pack(pady=5)
        
        result_label = tk.Label(right_frame, text="📸 THUMBNAIL RESULT", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.thumb_image_label = tk.Label(right_frame, text="Click 'EXTRACT THUMBNAIL' to start",
                                           bg=self.colors['card'], fg=self.colors['text2'],
                                           font=self.fonts['normal'])
        self.thumb_image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        status_frame = tk.Frame(right_frame, bg=self.colors['card'])
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(status_frame, text="Status:", bg=self.colors['card'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        self.thumb_status = tk.Label(status_frame, text="Not Extracted", bg=self.colors['card'],
                                      fg=self.colors['accent2'])
        self.thumb_status.pack(side=tk.LEFT, padx=10)
        
    def create_page6(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="🔍 REVERSE IMAGE SEARCH", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="यह फीचर इंटरनेट पर इस फोटो को खोजेगा\n\nफेक प्रोफाइल और कॉपीराइट उल्लंघन चेक करने के लिए", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        engines_frame = tk.LabelFrame(left_frame, text="Search Engines", 
                                       fg=self.colors['accent'], bg=self.colors['card'])
        engines_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.search_google = tk.BooleanVar(value=True)
        self.search_tineye = tk.BooleanVar(value=True)
        self.search_yandex = tk.BooleanVar(value=True)
        self.search_bing = tk.BooleanVar(value=False)
        
        tk.Checkbutton(engines_frame, text="🌐 Google Images", variable=self.search_google,
                      bg=self.colors['card'], fg=self.colors['text']).pack(anchor=tk.W, padx=20, pady=3)
        tk.Checkbutton(engines_frame, text="🔍 TinEye", variable=self.search_tineye,
                      bg=self.colors['card'], fg=self.colors['text']).pack(anchor=tk.W, padx=20, pady=3)
        tk.Checkbutton(engines_frame, text="🇷🇺 Yandex", variable=self.search_yandex,
                      bg=self.colors['card'], fg=self.colors['text']).pack(anchor=tk.W, padx=20, pady=3)
        tk.Checkbutton(engines_frame, text="📷 Bing", variable=self.search_bing,
                      bg=self.colors['card'], fg=self.colors['text']).pack(anchor=tk.W, padx=20, pady=3)
        
        self.search_btn = tk.Button(left_frame, text="🔍 START SEARCH", command=self.start_reverse_search,
                                     bg=self.colors['accent2'], fg='white',
                                     font=self.fonts['heading'], pady=8, width=20)
        self.search_btn.pack(pady=10)
        
        self.search_progress = ttk.Progressbar(left_frame, length=200, mode='indeterminate')
        self.search_progress.pack(pady=5)
        
        result_label = tk.Label(right_frame, text="📊 SEARCH RESULTS", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.search_result_text = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                              fg=self.colors['text'],
                                                              font=self.fonts['mono'])
        self.search_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.search_result_text.insert(1.0, "🔍 Click 'START SEARCH' to begin\n\nSearch engines will open in your browser.")
        
    def create_page7(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="🌍 DEEP GPS ANALYSIS", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="GPS coordinates से पूरी लोकेशन जानकारी निकालेगा:\nCity, State, Country, Street Address", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        gps_frame = tk.LabelFrame(left_frame, text="📍 Current GPS", 
                                   fg=self.colors['accent'], bg=self.colors['card'])
        gps_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.deep_gps_coords = tk.Label(gps_frame, text="No GPS data found\nOpen an image with GPS coordinates first",
                                        bg=self.colors['card'], fg=self.colors['text2'],
                                        font=self.fonts['small'])
        self.deep_gps_coords.pack(pady=15)
        
        btn_frame = tk.Frame(left_frame, bg=self.colors['card'])
        btn_frame.pack(pady=15)
        
        self.deep_gps_btn = tk.Button(btn_frame, text="🌍 ANALYZE LOCATION", command=self.analyze_deep_gps,
                                       bg=self.colors['accent2'], fg='white',
                                       font=self.fonts['heading'], padx=15, pady=8, state=tk.DISABLED)
        self.deep_gps_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_map_btn = tk.Button(btn_frame, text="🗺️ OPEN MAP", command=self.open_gps_maps,
                                       bg=self.colors['accent'], fg='#0a0e27',
                                       font=self.fonts['heading'], padx=15, pady=8, state=tk.DISABLED)
        self.open_map_btn.pack(side=tk.LEFT, padx=5)
        
        self.deep_gps_progress = ttk.Progressbar(left_frame, length=200, mode='indeterminate')
        self.deep_gps_progress.pack(pady=10)
        
        result_label = tk.Label(right_frame, text="📍 LOCATION DETAILS", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.deep_gps_result = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                           fg=self.colors['text'],
                                                           font=self.fonts['mono'])
        self.deep_gps_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_page8(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="📅 TIMELINE ANALYSIS", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="फोटो की पूरी टाइमलाइन दिखाएगा:\nFile Created, File Modified, Photo Taken", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        self.timeline_btn = tk.Button(left_frame, text="📅 GENERATE TIMELINE", command=self.generate_timeline,
                                       bg=self.colors['accent2'], fg='white',
                                       font=self.fonts['heading'], pady=8, width=20)
        self.timeline_btn.pack(pady=10)
        
        self.timeline_progress = ttk.Progressbar(left_frame, length=200, mode='indeterminate')
        self.timeline_progress.pack(pady=5)
        
        result_label = tk.Label(right_frame, text="📊 TIMELINE RESULT", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.timeline_text = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                         fg=self.colors['text'],
                                                         font=self.fonts['mono'])
        self.timeline_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.timeline_text.insert(1.0, "📅 Click 'GENERATE TIMELINE' to begin analysis")
        
    def create_page9(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="🔐 STEGANOGRAPHY DETECTION", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="यह फीचर फोटो के अंदर छिपे हुए डेटा को डिटेक्ट करता है\n\n• LSB एनालिसिस\n• एन्ट्रॉपी डिटेक्शन\n• EOF डेटा चेक", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        self.steg_btn = tk.Button(left_frame, text="🔐 RUN STEGANOGRAPHY SCAN", command=self.run_steg_scan,
                                   bg=self.colors['accent2'], fg='white',
                                   font=self.fonts['heading'], pady=8, width=25)
        self.steg_btn.pack(pady=10)
        
        self.steg_progress = ttk.Progressbar(left_frame, length=200, mode='indeterminate')
        self.steg_progress.pack(pady=5)
        
        result_label = tk.Label(right_frame, text="📊 STEGANOGRAPHY REPORT", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.steg_result_text = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                            fg=self.colors['text'],
                                                            font=self.fonts['mono'])
        self.steg_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_page10(self):
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        main_frame = tk.Frame(page, bg=self.colors['card'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(main_frame, text="ℹ️ TOOL INFORMATION", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=20)
        
        info_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         HEXAVISION FEATURES                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📷 IMAGE FORENSICS:                                                         ║
║  • EXIF Metadata Extraction - Camera info, settings, timestamps             ║
║  • GPS Location Detection - Coordinates and maps                            ║
║  • File Hashes - MD5, SHA1 for integrity verification                       ║
║                                                                              ║
║  🔬 ADVANCED ANALYSIS:                                                       ║
║  • Error Level Analysis (ELA) - Detect image manipulation                   ║
║  • Thumbnail Extraction - Extract hidden thumbnail from JPEGs               ║
║  • Reverse Image Search - Search image on Google/TinEye/Yandex              ║
║  • Deep GPS Analysis - Get city, state, country from coordinates            ║
║  • Timeline Analysis - File creation/modification history                   ║
║  • Steganography Detection - Find hidden data in images                     ║
║  • 🔬 PRNU Camera Fingerprinting - Identify exact camera device (NEW!)      ║
║                                                                              ║
║  👤 FACE FEATURES:                                                           ║
║  • Face Detection - Find faces in images                                    ║
║  • Face Matching - Compare two faces                                        ║
║                                                                              ║
║  💾 EXPORT:                                                                  ║
║  • HTML Report Generation                                                   ║
║  • JSON Export for programmatic use                                         ║
║                                                                              ║
║  🎮 SHORTCUTS:                                                               ║
║  • ← → : Change pages                                                       ║
║  • PgUp/PgDn : Browse images                                                ║
║  • Ctrl+O : Open images                                                     ║
║  • Ctrl+S : Save HTML report                                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        info_display = scrolledtext.ScrolledText(main_frame, bg=self.colors['card'],
                                                   fg=self.colors['text'],
                                                   font=self.fonts['mono'])
        info_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        info_display.insert(1.0, info_text)
        info_display.config(state=tk.DISABLED)
        
    def create_page11(self):
        """Page 11: Face Detection"""
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="👤 FACE DETECTION", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="फोटो में चेहरे ढूंढेगा\n\n• एक या कई चेहरे\n• चेहरे की लोकेशन बताएगा\n• आंखें भी डिटेक्ट करेगा", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        self.detect_btn = tk.Button(left_frame, text="👤 DETECT FACES", command=self.detect_faces,
                                     bg=self.colors['accent2'], fg='white',
                                     font=self.fonts['heading'], pady=10, width=25)
        self.detect_btn.pack(pady=10)
        
        params_frame = tk.LabelFrame(left_frame, text="Detection Parameters", 
                                      fg=self.colors['accent'], bg=self.colors['card'],
                                      font=self.fonts['heading'])
        params_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(params_frame, text="Scale Factor (1.05 - 1.5):", bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W, padx=10, pady=2)
        
        self.scale_factor = tk.DoubleVar(value=1.1)
        scale_scale = tk.Scale(params_frame, from_=1.05, to=1.5, orient=tk.HORIZONTAL,
                                variable=self.scale_factor, bg=self.colors['card'],
                                fg=self.colors['text'], length=200, resolution=0.05)
        scale_scale.pack(padx=10, pady=5)
        
        tk.Label(params_frame, text="Min Neighbors (2-10):", bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W, padx=10, pady=2)
        
        self.min_neighbors = tk.IntVar(value=5)
        neighbors_scale = tk.Scale(params_frame, from_=2, to=10, orient=tk.HORIZONTAL,
                                    variable=self.min_neighbors, bg=self.colors['card'],
                                    fg=self.colors['text'], length=200)
        neighbors_scale.pack(padx=10, pady=5)
        
        result_label = tk.Label(right_frame, text="📊 FACE DETECTION RESULTS", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.face_result_text = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                            fg=self.colors['text'],
                                                            font=self.fonts['mono'])
        self.face_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_page12(self):
        """Page 12: Face Matching"""
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="👥 FACE MATCHING", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="दो चेहरों की तुलना करें\n\n• समानता प्रतिशत बताएगा\n• फेक प्रोफाइल डिटेक्ट करेगा", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        # Face 1 Selection
        face1_frame = tk.LabelFrame(left_frame, text="📸 FACE 1", 
                                     fg=self.colors['accent'], bg=self.colors['card'],
                                     font=self.fonts['heading'])
        face1_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.face1_path_var = tk.StringVar()
        tk.Entry(face1_frame, textvariable=self.face1_path_var, bg=self.colors['header'],
                fg=self.colors['text'], font=self.fonts['small']).pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(face1_frame, text="📂 Browse Face 1", command=lambda: self.browse_face(1),
                 bg=self.colors['accent'], fg='#0a0e27', font=self.fonts['small']).pack(pady=5)
        
        # Face 2 Selection
        face2_frame = tk.LabelFrame(left_frame, text="📸 FACE 2", 
                                     fg=self.colors['accent'], bg=self.colors['card'],
                                     font=self.fonts['heading'])
        face2_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.face2_path_var = tk.StringVar()
        tk.Entry(face2_frame, textvariable=self.face2_path_var, bg=self.colors['header'],
                fg=self.colors['text'], font=self.fonts['small']).pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(face2_frame, text="📂 Browse Face 2", command=lambda: self.browse_face(2),
                 bg=self.colors['accent'], fg='#0a0e27', font=self.fonts['small']).pack(pady=5)
        
        # Match Button
        self.match_btn = tk.Button(left_frame, text="🔍 COMPARE FACES", command=self.compare_faces,
                                    bg=self.colors['accent2'], fg='white',
                                    font=self.fonts['heading'], pady=12, width=25)
        self.match_btn.pack(pady=10)
        
        # Threshold
        thresh_frame = tk.Frame(left_frame, bg=self.colors['card'])
        thresh_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(thresh_frame, text="Match Sensitivity:", bg=self.colors['card'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.match_threshold = tk.DoubleVar(value=0.7)
        thresh_scale = tk.Scale(thresh_frame, from_=0.3, to=0.9, orient=tk.HORIZONTAL,
                                 variable=self.match_threshold, bg=self.colors['card'],
                                 fg=self.colors['text'], length=150, resolution=0.05)
        thresh_scale.pack(side=tk.LEFT, padx=10)
        
        # Result display
        result_label = tk.Label(right_frame, text="📊 MATCHING RESULT", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.match_result_text = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                             fg=self.colors['text'],
                                                             font=self.fonts['mono'], height=20)
        self.match_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.match_result_text.insert(1.0, "🔍 Select two face images and click 'COMPARE FACES'")
        
    def create_page13(self):
        """Page 13: About"""
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        main_frame = tk.Frame(page, bg=self.colors['card'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(main_frame, text="📋 ABOUT HEXAVISION", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=20)
        
        about_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         HEXAVISION ENTERPRISE v9.0                            ║
║                      Professional Image Forensics Suite                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   DEVELOPED BY: HexaNet Prime                                                ║
║   VERSION: 9.0                                                               ║
║   RELEASE: 2025                                                              ║
║                                                                              ║
║   FEATURES:                                                                  ║
║   • EXIF Metadata Extraction                                                 ║
║   • GPS Location Detection                                                   ║
║   • Error Level Analysis (ELA)                                              ║
║   • Thumbnail Extraction                                                     ║
║   • Reverse Image Search                                                     ║
║   • Deep GPS Analysis                                                        ║
║   • Timeline Analysis                                                        ║
║   • Steganography Detection                                                  ║
║   • Face Detection                                                           ║
║   • Face Matching                                                            ║
║   • 🔬 PRNU Camera Fingerprinting (NEW!)                                    ║
║   • HTML/JSON Export                                                         ║
║                                                                              ║
║   REQUIREMENTS:                                                              ║
║   • pip install opencv-python pillow exifread numpy pywavelets              ║
║                                                                              ║
║   ⚠️  DISCLAIMER:                                                            ║
║   This tool is for educational and forensic purposes only.                  ║
║   Only analyze images you own or have permission to analyze.                ║
║                                                                              ║
║   🔗 HexaNet Prime - AI Powered. Hacker Driven.                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        about_display = scrolledtext.ScrolledText(main_frame, bg=self.colors['card'],
                                                    fg=self.colors['text'],
                                                    font=self.fonts['mono'])
        about_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        about_display.insert(1.0, about_text)
        about_display.config(state=tk.DISABLED)
        
    def create_page14(self):
        """Page 14: PRNU Camera Fingerprinting"""
        page = tk.Frame(self.pages_container, bg=self.colors['bg'])
        self.pages.append(page)
        
        left_frame = tk.Frame(page, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = tk.Frame(page, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title = tk.Label(left_frame, text="🔬 PRNU CAMERA FINGERPRINTING", 
                        bg=self.colors['card'], fg=self.colors['accent2'],
                        font=self.fonts['title'])
        title.pack(pady=10)
        
        info = tk.Label(left_frame, text="हर कैमरे का unique noise pattern पहचानेगा\n\n• फोटो किस specific कैमरे से ली गई\n• सिर्फ मॉडल नहीं, exact device\n• Sensor noise analysis", 
                       bg=self.colors['card'], fg=self.colors['text2'],
                       font=self.fonts['small'])
        info.pack(pady=5)
        
        # Current Image Analysis
        analyze_frame = tk.LabelFrame(left_frame, text="📸 ANALYZE CURRENT IMAGE", 
                                       fg=self.colors['accent'], bg=self.colors['card'],
                                       font=self.fonts['heading'])
        analyze_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.prnu_analyze_btn = tk.Button(analyze_frame, text="🔬 ANALYZE CAMERA NOISE", command=self.analyze_camera_noise,
                                           bg=self.colors['accent2'], fg='white',
                                           font=self.fonts['heading'], pady=8, width=25)
        self.prnu_analyze_btn.pack(pady=10)
        
        # Extract fingerprint from current image as reference
        fingerprint_frame = tk.LabelFrame(left_frame, text="📚 REFERENCE FINGERPRINT", 
                                           fg=self.colors['accent'], bg=self.colors['card'],
                                           font=self.fonts['heading'])
        fingerprint_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.prnu_extract_btn = tk.Button(fingerprint_frame, text="📌 EXTRACT AS REFERENCE", command=self.extract_reference_fingerprint,
                                           bg=self.colors['accent'], fg='#0a0e27',
                                           font=self.fonts['small'], pady=5)
        self.prnu_extract_btn.pack(pady=5)
        
        # Compare with reference
        compare_frame = tk.LabelFrame(left_frame, text="🔍 COMPARE WITH REFERENCE", 
                                       fg=self.colors['accent'], bg=self.colors['card'],
                                       font=self.fonts['heading'])
        compare_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.prnu_compare_btn = tk.Button(compare_frame, text="🎯 COMPARE WITH STORED REFERENCE", command=self.compare_with_reference,
                                           bg=self.colors['accent2'], fg='white',
                                           font=self.fonts['small'], pady=5)
        self.prnu_compare_btn.pack(pady=5)
        
        # Status
        self.prnu_ref_label = tk.Label(left_frame, text="Reference: Not set", bg=self.colors['card'],
                                        fg=self.colors['text2'], font=self.fonts['small'])
        self.prnu_ref_label.pack(pady=5)
        
        self.prnu_progress = ttk.Progressbar(left_frame, length=250, mode='indeterminate')
        self.prnu_progress.pack(pady=10)
        
        # Result display
        result_label = tk.Label(right_frame, text="📊 PRNU ANALYSIS REPORT", 
                               bg=self.colors['card'], fg=self.colors['accent'],
                               font=self.fonts['heading'])
        result_label.pack()
        
        self.prnu_result_text = scrolledtext.ScrolledText(right_frame, bg=self.colors['card'],
                                                            fg=self.colors['text'],
                                                            font=self.fonts['mono'])
        self.prnu_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.prnu_result_text.insert(1.0, "🔬 PRNU CAMERA FINGERPRINTING\n\n" + 
                                      "PRNU (Photo Response Non-Uniformity) हर कैमरे का unique sensor noise pattern होता है.\n\n" +
                                      "इस फीचर से आप पता लगा सकते हैं कि फोटो किस specific कैमरे से ली गई है.\n\n" +
                                      "कैसे use करें:\n" +
                                      "1. 'ANALYZE CAMERA NOISE' से current image का noise pattern देखें\n" +
                                      "2. 'EXTRACT AS REFERENCE' से किसी फोटो को reference के तौर पर सेव करें\n" +
                                      "3. 'COMPARE WITH REFERENCE' से दूसरी फोटो compare करें")
        
    # ============ PRNU CAMERA FINGERPRINTING ============
    
    def extract_prnu_fingerprint(self, img_path, max_size=512):
        """Extract PRNU noise fingerprint from image"""
        if not PYWT_AVAILABLE:
            return None, "PyWavelets not installed"
        
        try:
            # Read and resize image
            img = cv2.imread(img_path)
            if img is None:
                return None, "Could not read image"
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Resize for faster processing
            h, w = gray.shape
            if h > max_size or w > max_size:
                scale = max_size / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                gray = cv2.resize(gray, (new_w, new_h))
            
            # Apply wavelet transform to extract noise (high-frequency components)
            coeffs = pywt.dwt2(gray.astype(np.float32), 'db4')
            cA, (cH, cV, cD) = coeffs
            
            # Extract noise from high-frequency components
            noise = np.sqrt(cH**2 + cV**2 + cD**2)
            
            # Normalize
            noise = (noise - np.mean(noise)) / (np.std(noise) + 1e-7)
            
            # Create fingerprint hash for matching
            fingerprint = {
                'data': noise.flatten()[:10000],  # Store first 10000 values for matching
                'shape': noise.shape,
                'mean': float(np.mean(noise)),
                'std': float(np.std(noise)),
                'energy': float(np.sum(noise**2))
            }
            
            return fingerprint, None
            
        except Exception as e:
            return None, str(e)
    
    def analyze_camera_noise(self):
        """Analyze current image for camera noise fingerprint"""
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        if not PYWT_AVAILABLE:
            messagebox.showerror("Error", "PyWavelets not installed!\n\nPlease run: pip install pywavelets")
            return
        
        self.prnu_progress.start()
        self.prnu_analyze_btn.config(state=tk.DISABLED, text="⏳ ANALYZING...")
        self.update_status("Analyzing camera noise fingerprint...")
        
        thread = threading.Thread(target=self._perform_prnu_analysis, daemon=True)
        thread.start()
        
    def _perform_prnu_analysis(self):
        img_path = self.current_images[self.current_index]
        fingerprint, error = self.extract_prnu_fingerprint(img_path)
        
        if fingerprint is None:
            result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔬 PRNU ANALYSIS REPORT                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ❌ ERROR: {error}                                                            
║                                                                              ║
║  💡 TIPS:                                                                    ║
║  • Make sure the image is clear                                             ║
║  • Image should be from a camera (not screenshot)                           ║
║  • Try with a different image                                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            self.root.after(0, lambda: self._update_prnu_results(result_text))
            return
        
        # Calculate noise statistics
        noise_mean = fingerprint['mean']
        noise_std = fingerprint['std']
        noise_energy = fingerprint['energy']
        
        # Determine noise characteristics
        if noise_energy > 1000:
            noise_level = "HIGH - Very distinct camera fingerprint"
            color_indicator = "🔴"
        elif noise_energy > 500:
            noise_level = "MEDIUM - Moderate camera fingerprint"
            color_indicator = "🟡"
        else:
            noise_level = "LOW - Weak camera fingerprint"
            color_indicator = "🟢"
        
        result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔬 PRNU CAMERA FINGERPRINT ANALYSIS                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📸 FILE: {os.path.basename(img_path)}                                       
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │                         NOISE STATISTICS                               │ ║
║  ├────────────────────────────────────────────────────────────────────────┤ ║
║  │  Noise Energy:  {noise_energy:.2f}                                                  │ ║
║  │  Noise Mean:    {noise_mean:.4f}                                                   │ ║
║  │  Noise Std Dev: {noise_std:.4f}                                                   │ ║
║  │  Fingerprint Size: {fingerprint['shape'][0]} x {fingerprint['shape'][1]}                                    │ ║
║  └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  🎯 CAMERA FINGERPRINT STRENGTH: {color_indicator} {noise_level}                      ║
║                                                                              ║
"""
        
        if noise_energy > 800:
            result_text += """
║  ✅ This image has a STRONG camera fingerprint!                              ║
║  • Can be used to identify the exact camera device                          ║
║  • Good for forensic analysis                                                ║
║                                                                              ║
"""
        elif noise_energy > 400:
            result_text += """
║  🟡 This image has a MODERATE camera fingerprint                             ║
║  • May help identify the camera                                              ║
║  • Works best with reference images                                          ║
║                                                                              ║
"""
        else:
            result_text += """
║  ⚠️ This image has a WEAK camera fingerprint                                 ║
║  • Image may be heavily compressed                                           ║
║  • May be a screenshot or social media image                                 ║
║  • Camera identification may be difficult                                    ║
║                                                                              ║
"""
        
        result_text += """
║  💡 WHAT IS PRNU?                                                            ║
║  • Every camera sensor has unique noise pattern                            ║
║  • Like a digital fingerprint for cameras                                   ║
║  • Can identify exact device that took the photo                           ║
║                                                                              ║
║  🔧 NEXT STEPS:                                                              ║
║  • Click 'EXTRACT AS REFERENCE' to save this fingerprint                    ║
║  • Then compare other images to see if same camera                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        self.root.after(0, lambda: self._update_prnu_results(result_text))
        
    def extract_reference_fingerprint(self):
        """Extract and store reference fingerprint from current image"""
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        if not PYWT_AVAILABLE:
            messagebox.showerror("Error", "PyWavelets not installed!")
            return
        
        self.prnu_progress.start()
        self.prnu_extract_btn.config(state=tk.DISABLED, text="⏳ EXTRACTING...")
        self.update_status("Extracting reference fingerprint...")
        
        thread = threading.Thread(target=self._perform_reference_extraction, daemon=True)
        thread.start()
        
    def _perform_reference_extraction(self):
        img_path = self.current_images[self.current_index]
        fingerprint, error = self.extract_prnu_fingerprint(img_path)
        
        if fingerprint is None:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to extract fingerprint: {error}"))
            self.root.after(0, lambda: self.prnu_extract_btn.config(state=tk.NORMAL, text="📌 EXTRACT AS REFERENCE"))
            self.root.after(0, lambda: self.prnu_progress.stop())
            return
        
        self.prnu_reference_fingerprint = fingerprint
        self.prnu_reference_image = img_path
        
        self.root.after(0, lambda: self.prnu_ref_label.config(text=f"Reference: {os.path.basename(img_path)}", fg=self.colors['success']))
        self.root.after(0, lambda: self.prnu_extract_btn.config(state=tk.NORMAL, text="📌 EXTRACT AS REFERENCE"))
        self.root.after(0, lambda: self.prnu_progress.stop())
        self.root.after(0, lambda: messagebox.showinfo("Success", f"Reference fingerprint extracted!\n\nImage: {os.path.basename(img_path)}\nNoise Energy: {fingerprint['energy']:.2f}"))
        self.update_status(f"Reference fingerprint saved from {os.path.basename(img_path)}")
        
    def compare_with_reference(self):
        """Compare current image fingerprint with stored reference"""
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        if not hasattr(self, 'prnu_reference_fingerprint') or self.prnu_reference_fingerprint is None:
            messagebox.showwarning("Warning", "No reference fingerprint stored!\n\nFirst extract a reference fingerprint from a known image.")
            return
        
        if not PYWT_AVAILABLE:
            messagebox.showerror("Error", "PyWavelets not installed!")
            return
        
        self.prnu_progress.start()
        self.prnu_compare_btn.config(state=tk.DISABLED, text="⏳ COMPARING...")
        self.update_status("Comparing fingerprints...")
        
        thread = threading.Thread(target=self._perform_fingerprint_comparison, daemon=True)
        thread.start()
        
    def _perform_fingerprint_comparison(self):
        img_path = self.current_images[self.current_index]
        fingerprint, error = self.extract_prnu_fingerprint(img_path)
        
        if fingerprint is None:
            self.root.after(0, lambda: self._update_prnu_results(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔬 FINGERPRINT COMPARISON                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ❌ ERROR: Could not extract fingerprint from current image                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""))
            return
        
        # Calculate similarity between fingerprints
        ref_data = self.prnu_reference_fingerprint['data']
        curr_data = fingerprint['data']
        
        # Align lengths
        min_len = min(len(ref_data), len(curr_data))
        ref_aligned = ref_data[:min_len]
        curr_aligned = curr_data[:min_len]
        
        # Calculate correlation
        correlation = np.corrcoef(ref_aligned, curr_aligned)[0, 1]
        if np.isnan(correlation):
            correlation = 0
        similarity = max(0, min(100, correlation * 100))
        
        # Compare energy
        energy_diff = abs(self.prnu_reference_fingerprint['energy'] - fingerprint['energy'])
        energy_similarity = max(0, 100 - (energy_diff / 10))
        
        # Weighted score
        final_score = (similarity * 0.7) + (energy_similarity * 0.3)
        
        # Determine match result
        if final_score > 60:
            match_result = "✅✅✅ HIGH CONFIDENCE - Same Camera!"
            match_color = "🟢"
            explanation = "These images were likely taken by the SAME camera device!"
            danger_add = 0
        elif final_score > 40:
            match_result = "🤔🤔🤔 MEDIUM CONFIDENCE - Possibly Same Camera"
            match_color = "🟡"
            explanation = "These images may be from the same camera, but not 100% certain"
            danger_add = 5
        else:
            match_result = "❌❌❌ LOW CONFIDENCE - Different Cameras"
            match_color = "🔴"
            explanation = "These images were likely taken by DIFFERENT camera devices!"
            danger_add = 10
        
        result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔬 PRNU FINGERPRINT COMPARISON                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📸 REFERENCE IMAGE: {os.path.basename(self.prnu_reference_image)}                    
║  📸 CURRENT IMAGE:  {os.path.basename(img_path)}                                    
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │                         COMPARISON RESULTS                             │ ║
║  ├────────────────────────────────────────────────────────────────────────┤ ║
║  │  Correlation Score:  {correlation:.2%}                                                │ ║
║  │  Similarity Score:   {similarity:.1f}%                                                │ ║
║  │  Energy Score:       {energy_similarity:.1f}%                                                │ ║
║  │  Final Confidence:   {final_score:.1f}%                                                │ ║
║  └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  🎯 VERDICT: {match_color} {match_result}                                        ║
║                                                                              ║
║  📋 EXPLANATION:                                                             ║
║  {explanation}                                      
║                                                                              ║
"""
        
        if final_score > 60:
            result_text += """
║  💡 INTERPRETATION:                                                          ║
║  • High correlation means similar sensor noise pattern                      ║
║  • Strong evidence that same camera took both photos                       ║
║  • Useful for tracking images from same device                              ║
║                                                                              ║
"""
        elif final_score > 40:
            result_text += """
║  💡 INTERPRETATION:                                                          ║
║  • Moderate correlation - some similarity detected                         ║
║  • Could be same camera model or similar sensor                            ║
║  • More reference images needed for confirmation                           ║
║                                                                              ║
"""
        else:
            result_text += """
║  💡 INTERPRETATION:                                                          ║
║  • Low correlation - different sensor noise patterns                       ║
║  • Likely different cameras or heavily processed images                    ║
║  • Useful for detecting fake/edited images                                 ║
║                                                                              ║
"""
        
        result_text += """
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        # Update danger meter
        if danger_add > 0:
            current_meta = self.metadata_cache.get(img_path, {})
            current_danger = self.get_danger(current_meta)
            new_danger = min(current_danger + danger_add, 100)
            self.root.after(0, lambda: self._update_prnu_results_with_danger(result_text, new_danger))
        else:
            self.root.after(0, lambda: self._update_prnu_results(result_text))
        
    def _update_prnu_results(self, result_text, new_danger=None):
        self.prnu_progress.stop()
        self.prnu_analyze_btn.config(state=tk.NORMAL, text="🔬 ANALYZE CAMERA NOISE")
        self.prnu_extract_btn.config(state=tk.NORMAL, text="📌 EXTRACT AS REFERENCE")
        self.prnu_compare_btn.config(state=tk.NORMAL, text="🎯 COMPARE WITH STORED REFERENCE")
        
        self.prnu_result_text.delete(1.0, tk.END)
        self.prnu_result_text.insert(1.0, result_text)
        
        if new_danger:
            current = int(self.danger_label.cget("text").replace("%", ""))
            if new_danger > current:
                self.danger_label.config(text=f"{new_danger}%")
                self.danger_progress['value'] = new_danger
                if new_danger >= 70:
                    self.danger_label.config(fg=self.colors['danger'])
                    self.danger_desc.config(text="HIGH RISK! Different cameras detected!")
                elif new_danger >= 40:
                    self.danger_label.config(fg=self.colors['warning'])
                    self.danger_desc.config(text="MEDIUM RISK - Possible different cameras")
                
                self.risk_text.insert(tk.END, f"\n\n🔬 PRNU: Different camera fingerprints detected!")
                self.risk_text.see(tk.END)
        
        self.update_status("PRNU analysis completed")
        
    def _update_prnu_results_with_danger(self, result_text, new_danger):
        self.prnu_progress.stop()
        self.prnu_analyze_btn.config(state=tk.NORMAL, text="🔬 ANALYZE CAMERA NOISE")
        self.prnu_extract_btn.config(state=tk.NORMAL, text="📌 EXTRACT AS REFERENCE")
        self.prnu_compare_btn.config(state=tk.NORMAL, text="🎯 COMPARE WITH STORED REFERENCE")
        
        self.prnu_result_text.delete(1.0, tk.END)
        self.prnu_result_text.insert(1.0, result_text)
        
        current = int(self.danger_label.cget("text").replace("%", ""))
        if new_danger > current:
            self.danger_label.config(text=f"{new_danger}%")
            self.danger_progress['value'] = new_danger
            if new_danger >= 70:
                self.danger_label.config(fg=self.colors['danger'])
                self.danger_desc.config(text="HIGH RISK! Different cameras detected!")
            elif new_danger >= 40:
                self.danger_label.config(fg=self.colors['warning'])
                self.danger_desc.config(text="MEDIUM RISK - Possible different cameras")
            
            self.risk_text.insert(tk.END, f"\n\n🔬 PRNU: Different camera fingerprints detected!")
            self.risk_text.see(tk.END)
        
        self.update_status("PRNU comparison completed")
        
    # ============ FACE MATCHING ============
    
    def browse_face(self, face_num):
        """Browse image for face comparison"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            if face_num == 1:
                self.face1_path_var.set(file_path)
            else:
                self.face2_path_var.set(file_path)
                
    def extract_face_histogram(self, img_path):
        """Extract face region and compute histogram for matching"""
        try:
            if not CV2_AVAILABLE or self.face_cascade is None:
                return None, None, None
                
            img = cv2.imread(img_path)
            if img is None:
                return None, None, None
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
            
            if len(faces) == 0:
                return None, None, None
            
            x, y, w, h = faces[0]
            face_roi = img[y:y+h, x:x+w]
            
            hist_features = []
            for channel in range(3):
                hist = cv2.calcHist([face_roi], [channel], None, [32], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                hist_features.extend(hist)
            
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            gray_hist = cv2.calcHist([gray_face], [0], None, [32], [0, 256])
            gray_hist = cv2.normalize(gray_hist, gray_hist).flatten()
            hist_features.extend(gray_hist)
            
            return hist_features, (x, y, w, h), face_roi
            
        except Exception as e:
            print(f"Error extracting face: {e}")
            return None, None, None
            
    def compare_faces(self):
        """Compare two faces using histogram matching"""
        face1_path = self.face1_path_var.get()
        face2_path = self.face2_path_var.get()
        
        if not face1_path or not face2_path:
            messagebox.showwarning("Warning", "Please select both face images!")
            return
        
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not installed!")
            return
        
        if self.face_cascade is None:
            messagebox.showerror("Error", "Face detector not loaded!")
            return
        
        self.match_btn.config(state=tk.DISABLED, text="⏳ COMPARING...")
        self.update_status("Comparing faces...")
        
        thread = threading.Thread(target=self._perform_face_matching, args=(face1_path, face2_path), daemon=True)
        thread.start()
        
    def _perform_face_matching(self, face1_path, face2_path):
        """Perform face matching"""
        try:
            hist1, _, _ = self.extract_face_histogram(face1_path)
            hist2, _, _ = self.extract_face_histogram(face2_path)
            
            if hist1 is None:
                result_text = self._get_no_face_result(1)
                self.root.after(0, lambda: self._update_match_results(result_text, None))
                return
            
            if hist2 is None:
                result_text = self._get_no_face_result(2)
                self.root.after(0, lambda: self._update_match_results(result_text, None))
                return
            
            hist1 = np.array(hist1)
            hist2 = np.array(hist2)
            similarity = np.corrcoef(hist1, hist2)[0, 1]
            similarity = max(0, min(1, similarity)) * 100
            
            threshold = self.match_threshold.get() * 100
            is_match = similarity >= threshold
            
            result_text = self._get_match_result_text(similarity, is_match, threshold, face1_path, face2_path)
            
            new_danger = None
            if not is_match and similarity < 50:
                current_danger = int(self.danger_label.cget("text").replace("%", ""))
                new_danger = min(current_danger + 25, 100)
                if new_danger > current_danger:
                    self.root.after(0, lambda: self.danger_label.config(text=f"{new_danger}%"))
                    self.root.after(0, lambda: self.danger_progress.config(value=new_danger))
                    if new_danger >= 70:
                        self.root.after(0, lambda: self.danger_label.config(fg=self.colors['danger']))
                        self.root.after(0, lambda: self.danger_desc.config(text="HIGH RISK! Fake profile detected!"))
                    elif new_danger >= 40:
                        self.root.after(0, lambda: self.danger_label.config(fg=self.colors['warning']))
                        self.root.after(0, lambda: self.danger_desc.config(text="Different faces - Possible fake"))
                    self.root.after(0, lambda: self.risk_text.insert(tk.END, "\n\n👥 FACE MATCH: Different faces detected!"))
            
            self.root.after(0, lambda: self._update_match_results(result_text, new_danger))
            
        except Exception as e:
            error_msg = str(e)
            result_text = self._get_error_result(error_msg)
            self.root.after(0, lambda: self._update_match_results(result_text, None))
            
    def _get_match_result_text(self, similarity, is_match, threshold, face1_path, face2_path):
        """Generate match result text"""
        face1_name = os.path.basename(face1_path)
        face2_name = os.path.basename(face2_path)
        
        if similarity >= 80:
            result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ✅✅✅  ये दोनों चेहरे एक जैसे हैं!  ✅✅✅                       ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                        │ ║
║   │         फोटो 1 का चेहरा        =        फोटो 2 का चेहरा               │ ║
║   │               👤                             👤                         │ ║
║   │                                                                        │ ║
║   │              ये एक ही व्यक्ति है!                                      │ ║
║   │                                                                        │ ║
║   │   📊 समानता: {similarity:.1f}% (बहुत अच्छा मैच)                               │ ║
║   │   🎯 सीमा: {threshold:.0f}%                                                 │ ║
║   │                                                                        │ ║
║   └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║   💡 मतलब: दोनों फोटो में एक ही व्यक्ति है                                   ║
║                                                                              ║
║   📸 फोटो 1: {face1_name}                                                   
║   📸 फोटो 2: {face2_name}                                                   
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        elif similarity >= 60:
            result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           🤔🤔🤔  हो सकता है एक ही व्यक्ति, लेकिन पक्का नहीं  🤔🤔🤔          ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                        │ ║
║   │         फोटो 1 का चेहरा        ?        फोटो 2 का चेहरा               │ ║
║   │               👤                             👤                         │ ║
║   │                                                                        │ ║
║   │          हो सकता है एक ही व्यक्ति हो                                    │ ║
║   │          लेकिन फोटो खराब होने से सही पता नहीं चल पाया                  │ ║
║   │                                                                        │ ║
║   │   📊 समानता: {similarity:.1f}% (थोड़ा मैच)                                    │ ║
║   │   🎯 सीमा: {threshold:.0f}%                                                 │ ║
║   │                                                                        │ ║
║   └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║   💡 सुझाव: बेहतर क्वालिटी वाली फोटो से दोबारा try करो                       ║
║                                                                              ║
║   📸 फोटो 1: {face1_name}                                                   
║   📸 फोटो 2: {face2_name}                                                   
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        elif similarity >= 40:
            result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           😐😐😐  थोड़ा मिलता है, लेकिन शायद अलग व्यक्ति है  😐😐😐          ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                        │ ║
║   │         फोटो 1 का चेहरा        ≠        फोटो 2 का चेहरा               │ ║
║   │               👤                             👤                         │ ║
║   │                                                                        │ ║
║   │              शायद ये अलग-अलग लोग हैं                                    │ ║
║   │                                                                        │ ║
║   │   📊 समानता: {similarity:.1f}% (बहुत कम मैच)                                  │ ║
║   │   🎯 सीमा: {threshold:.0f}%                                                 │ ║
║   │                                                                        │ ║
║   └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║   💡 मतलब: ये दोनों शायद अलग-अलग लोग हैं                                      ║
║   ⚠️ सावधान: अगर यह एक ही व्यक्ति होना चाहिए था, तो फोटो एडिट हो सकती है     ║
║                                                                              ║
║   📸 फोटो 1: {face1_name}                                                   
║   📸 फोटो 2: {face2_name}                                                   
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        else:
            result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        ❌❌❌  ये दोनों चेहरे एक जैसे नहीं हैं!  ❌❌❌                         ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                        │ ║
║   │         फोटो 1 का चेहरा        ≠        फोटो 2 का चेहरा               │ ║
║   │               👤                             👤                         │ ║
║   │                                                                        │ ║
║   │              ये दो अलग-अलग लोग हैं!                                     │ ║
║   │                                                                        │ ║
║   │   📊 समानता: {similarity:.1f}% (बिल्कुल भी मैच नहीं)                          │ ║
║   │   🎯 सीमा: {threshold:.0f}%                                                 │ ║
║   │                                                                        │ ║
║   └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║   💡 मतलब: फोटो 1 में जो व्यक्ति है, वह फोटो 2 वाला नहीं है                  ║
║                                                                              ║
║   ⚠️  सावधान: अगर यह एक ही व्यक्ति होना चाहिए था,                           ║
║       तो कोई फोटो एडिट करके चेहरा बदल सकता है!                              ║
║                                                                              ║
║   📸 फोटो 1: {face1_name}                                                   
║   📸 फोटो 2: {face2_name}                                                   
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return result_text
        
    def _get_no_face_result(self, face_num):
        """Generate no face result text"""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ❌❌❌  फोटो में कोई चेहरा नहीं मिला!  ❌❌❌                      ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                        │ ║
║   │              फोटो {face_num} में कोई चेहरा नहीं दिख रहा है                 │ ║
║   │                                                                        │ ║
║   │   💡 सुझाव:                                                            │ ║
║   │   • ऐसी फोटो लें जिसमें चेहरा साफ दिख रहा हो                          │ ║
║   │   • चेहरा सीधा (front-facing) होना चाहिए                              │ ║
║   │   • अच्छी रोशनी में फोटो लें                                           │ ║
║   │   • फोटो धुंधली (blur) न हो                                             │ ║
║   │                                                                        │ ║
║   └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
    def _get_error_result(self, error_msg):
        """Generate error result text"""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ❌❌❌  त्रुटि (Error) आ गई!  ❌❌❌                         ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                        │ ║
║   │   त्रुटि: {error_msg}                                                    │ ║
║   │                                                                        │ ║
║   │   💡 सुझाव:                                                            │ ║
║   │   • OpenCV ठीक से install है? Check करें                               │ ║
║   │   • pip install opencv-python                                          │ ║
║   │   • फोटो सही format में है? (JPG, PNG, BMP)                            │ ║
║   │   • फोटो खराब तो नहीं है?                                               │ ║
║   │                                                                        │ ║
║   └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            
    def _update_match_results(self, result_text, new_danger):
        self.match_btn.config(state=tk.NORMAL, text="🔍 COMPARE FACES")
        self.match_result_text.delete(1.0, tk.END)
        self.match_result_text.insert(1.0, result_text)
        
        if new_danger:
            current = int(self.danger_label.cget("text").replace("%", ""))
            if new_danger > current:
                self.danger_label.config(text=f"{new_danger}%")
                self.danger_progress['value'] = new_danger
                if new_danger >= 70:
                    self.danger_label.config(fg=self.colors['danger'])
                    self.danger_desc.config(text="HIGH RISK! Fake profile detected!")
                elif new_danger >= 40:
                    self.danger_label.config(fg=self.colors['warning'])
                    self.danger_desc.config(text="MEDIUM RISK - Different faces")
                
                self.risk_text.insert(tk.END, f"\n\n👥 FACE MATCH: Different faces detected!")
                self.risk_text.see(tk.END)
        
        self.update_status("Face matching completed")
        
    # ============ FACE DETECTION ============
    
    def detect_faces(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not installed!")
            return
        
        if self.face_cascade is None:
            messagebox.showerror("Error", "Face detector not loaded!")
            return
        
        self.detect_btn.config(state=tk.DISABLED, text="⏳ DETECTING...")
        self.update_status("Detecting faces...")
        
        thread = threading.Thread(target=self._perform_face_detection, daemon=True)
        thread.start()
        
    def _perform_face_detection(self):
        img_path = self.current_images[self.current_index]
        
        try:
            img = cv2.imread(img_path)
            if img is None:
                raise Exception("Could not read image")
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            scale = self.scale_factor.get()
            neighbors = self.min_neighbors.get()
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=scale, minNeighbors=neighbors, minSize=(30, 30))
            
            num_faces = len(faces)
            
            report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         👤 FACE DETECTION REPORT                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📸 FILE: {os.path.basename(img_path)}                                       
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │                         DETECTION RESULTS                              │ ║
║  ├────────────────────────────────────────────────────────────────────────┤ ║
║  │  Faces Detected: {num_faces}{' ' * (54 - len(str(num_faces)))} │ ║
║  │  Scale Factor:   {scale:.2f}{' ' * (53 - len(f'{scale:.2f}'))} │ ║
║  │  Min Neighbors:  {neighbors}{' ' * (54 - len(str(neighbors)))} │ ║
║  └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
"""
            
            if num_faces == 0:
                report += """
║  ⚠️ NO FACES DETECTED!                                                        ║
║                                                                              ║
║  💡 TIPS:                                                                    ║
║  • Ensure the image contains clear faces                                    ║
║  • Try lowering Scale Factor (1.05-1.1)                                     ║
║  • Try lowering Min Neighbors (2-3)                                         ║
║                                                                              ║
"""
            elif num_faces == 1:
                x, y, w, h = faces[0]
                report += f"""
║  ✅ SINGLE FACE DETECTED                                                      ║
║                                                                              ║
║  📍 FACE LOCATION:                                                           ║
║  • X Position: {x}                                                          ║
║  • Y Position: {y}                                                          ║
║  • Width: {w}                                                               ║
║  • Height: {h}                                                              ║
║                                                                              ║
"""
            else:
                report += f"""
║  👥 MULTIPLE FACES DETECTED ({num_faces} faces)                                                ║
║                                                                              ║
"""
                for i, (x, y, w, h) in enumerate(faces):
                    report += f"║  Face {i+1}: Position ({x}, {y}) | Size: {w}x{h}{' ' * (27 - len(str(w)))} ║\n"
                report += "║                                                                              ║\n"
            
            report += """
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            
            self.root.after(0, lambda: self._update_face_results(report))
            
        except Exception as e:
            error_msg = str(e)
            report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         👤 FACE DETECTION REPORT                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ❌ ERROR: {error_msg}                                                        
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            self.root.after(0, lambda: self._update_face_results(report))
            
    def _update_face_results(self, report):
        self.detect_btn.config(state=tk.NORMAL, text="👤 DETECT FACES")
        self.face_result_text.delete(1.0, tk.END)
        self.face_result_text.insert(1.0, report)
        self.update_status("Face detection completed")
        
    # ============ STEGANOGRAPHY DETECTION ============
    
    def run_steg_scan(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        self.steg_progress.start()
        self.steg_btn.config(state=tk.DISABLED, text="⏳ SCANNING...")
        self.update_status("Running steganography detection...")
        
        thread = threading.Thread(target=self._perform_steg_scan, daemon=True)
        thread.start()
        
    def _perform_steg_scan(self):
        img_path = self.current_images[self.current_index]
        results = []
        threat_level = 0
        
        # LSB Analysis
        if PIL_AVAILABLE:
            try:
                img = Image.open(img_path)
                if img.mode in ['RGB', 'RGBA']:
                    pixels = list(img.getdata())
                    sample_size = min(5000, len(pixels))
                    lsb_sum = 0
                    
                    for i in range(sample_size):
                        if isinstance(pixels[i], tuple):
                            for channel in pixels[i][:3]:
                                lsb_sum += channel & 1
                    
                    lsb_ratio = lsb_sum / (sample_size * 3)
                    
                    if lsb_ratio > 0.53 or lsb_ratio < 0.47:
                        threat_level += 30
                        results.append(f"📊 LSB Ratio: {lsb_ratio:.2%} 🔴 UNUSUAL")
                    else:
                        results.append(f"📊 LSB Ratio: {lsb_ratio:.2%} ✅ NORMAL")
            except:
                pass
        
        # Entropy Analysis
        try:
            with open(img_path, 'rb') as f:
                data = f.read(32768)
                
            freq = [0] * 256
            for byte in data:
                freq[byte] += 1
            
            entropy = 0
            total = len(data)
            for count in freq:
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)
            
            results.append(f"\n📈 RANDOMNESS (ENTROPY): {entropy:.2f}/8.00")
            
            if entropy > 7.0:
                threat_level += 40
                results.append("   🔴 EXTREME RANDOMNESS - Possible hidden data")
            elif entropy > 6.0:
                threat_level += 25
                results.append("   🟡 HIGH RANDOMNESS - Suspicious")
            elif entropy > 4.0:
                threat_level += 10
                results.append("   🟠 MODERATE RANDOMNESS - Slightly suspicious")
            else:
                results.append("   ✅ LOW RANDOMNESS - Normal")
        except:
            pass
        
        # Determine threat level
        if threat_level >= 70:
            threat_text = "🔴 HIGH THREAT - Likely contains hidden data!"
            emoji = "🔴"
        elif threat_level >= 40:
            threat_text = "🟡 MEDIUM THREAT - Suspicious patterns detected"
            emoji = "🟡"
        elif threat_level >= 20:
            threat_text = "🟠 LOW THREAT - Some anomalies detected"
            emoji = "🟠"
        else:
            threat_text = "🟢 CLEAN - No hidden data detected"
            emoji = "🟢"
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔐 STEGANOGRAPHY DETECTION REPORT                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📸 FILE: {os.path.basename(img_path)}                                       
║                                                                              ║
"""
        for line in results:
            report += f"{line}\n"
        
        report += f"""
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🎯 VERDICT: {emoji} {threat_text}                                            ║
║  📊 THREAT SCORE: {threat_level}/100                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        steg_danger = min(threat_level // 2, 30)
        current_meta = self.metadata_cache.get(img_path, {})
        current_danger = self.get_danger(current_meta)
        new_danger = min(current_danger + steg_danger, 100)
        
        self.root.after(0, lambda: self._update_steg_results(report, new_danger))
        
    def _update_steg_results(self, report, new_danger):
        self.steg_progress.stop()
        self.steg_btn.config(state=tk.NORMAL, text="🔐 RUN STEGANOGRAPHY SCAN")
        self.steg_result_text.delete(1.0, tk.END)
        self.steg_result_text.insert(1.0, report)
        
        current = int(self.danger_label.cget("text").replace("%", ""))
        if new_danger > current:
            self.danger_label.config(text=f"{new_danger}%")
            self.danger_progress['value'] = new_danger
            if new_danger >= 70:
                self.danger_label.config(fg=self.colors['danger'])
                self.danger_desc.config(text="HIGH RISK! Hidden data detected!")
            elif new_danger >= 40:
                self.danger_label.config(fg=self.colors['warning'])
                self.danger_desc.config(text="MEDIUM RISK - Possible hidden data")
        
        self.update_status("Steganography scan complete")
        
    # ============ BASIC FEATURES (Image, EXIF, GPS, etc.) ============
    
    def create_image_box(self, parent):
        self.image_label = tk.Label(parent, text="No Image\n\nClick Open",
                                     bg=self.colors['card'], fg=self.colors['text2'],
                                     font=self.fonts['normal'])
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        nav = tk.Frame(parent, bg=self.colors['card'])
        nav.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(nav, text="◀", command=self.prev_image,
                 bg=self.colors['header'], fg='white', width=3).pack(side=tk.LEFT)
        
        self.img_counter = tk.Label(nav, text="0/0", bg=self.colors['card'],
                                     fg=self.colors['text'], font=self.fonts['normal'])
        self.img_counter.pack(side=tk.LEFT, expand=True)
        
        tk.Button(nav, text="▶", command=self.next_image,
                 bg=self.colors['header'], fg='white', width=3).pack(side=tk.RIGHT)
        
        tk.Button(parent, text="📂 OPEN", command=self.open_images,
                 bg=self.colors['accent'], fg='#0a0e27', font=self.fonts['normal']).pack(fill=tk.X, padx=10, pady=10)
        
    def create_exif_box(self, parent):
        sf = tk.Frame(parent, bg=self.colors['card'])
        sf.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(sf, text="🔍", bg=self.colors['card'],
                fg=self.colors['accent']).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_exif())
        tk.Entry(sf, textvariable=self.search_var, bg=self.colors['header'],
                fg=self.colors['text'], font=self.fonts['normal']).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        tf = tk.Frame(parent, bg=self.colors['card'])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll = tk.Scrollbar(tf)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.exif_tree = ttk.Treeview(tf, columns=('Value',), show='tree headings',
                                       yscrollcommand=scroll.set, height=14)
        self.exif_tree.heading('#0', text='Tag')
        self.exif_tree.heading('Value', text='Value')
        self.exif_tree.column('#0', width=200)
        self.exif_tree.column('Value', width=250)
        
        self.exif_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.exif_tree.yview)
        
    def create_gps_box(self, parent):
        self.gps_text = tk.Text(parent, bg=self.colors['card'], fg=self.colors['text'],
                                 font=self.fonts['mono'], wrap=tk.WORD, height=18)
        self.gps_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        bf = tk.Frame(parent, bg=self.colors['card'])
        bf.pack(fill=tk.X, padx=10, pady=10)
        
        self.map_btn = tk.Button(bf, text="🗺️ MAP", command=self.open_maps,
                                  bg=self.colors['accent'], fg='#0a0e27', state=tk.DISABLED)
        self.map_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.copy_gps_btn = tk.Button(bf, text="📋 COPY", command=self.copy_gps,
                                       bg=self.colors['header'], fg=self.colors['text'], state=tk.DISABLED)
        self.copy_gps_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
    def create_fileinfo_box(self, parent):
        self.fileinfo_text = tk.Text(parent, bg=self.colors['card'], fg=self.colors['text'],
                                      font=self.fonts['mono'], wrap=tk.WORD, height=18)
        self.fileinfo_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_risk_box(self, parent):
        self.risk_text = tk.Text(parent, bg=self.colors['card'], fg=self.colors['text'],
                                  font=self.fonts['normal'], wrap=tk.WORD, height=18)
        self.risk_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_stats_box(self, parent):
        self.stats_text = tk.Text(parent, bg=self.colors['card'], fg=self.colors['text'],
                                   font=self.fonts['mono'], wrap=tk.WORD, height=8)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_danger_box(self, parent):
        center = tk.Frame(parent, bg=self.colors['card'])
        center.pack(expand=True)
        
        self.danger_label = tk.Label(center, text="0%", bg=self.colors['card'],
                                      fg=self.colors['success'], font=('Arial', 32, 'bold'))
        self.danger_label.pack(pady=10)
        
        self.danger_progress = ttk.Progressbar(center, length=150, mode='determinate')
        self.danger_progress.pack(pady=10)
        
        self.danger_desc = tk.Label(center, text="No image", bg=self.colors['card'],
                                     fg=self.colors['text2'], font=self.fonts['small'])
        self.danger_desc.pack()
        
    def create_tools_box(self, parent):
        btn_frame = tk.Frame(parent, bg=self.colors['card'])
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tools = [
            ("🔍 Reverse Search", lambda: self.show_page(5)),
            ("🗑️ Strip Metadata", self.strip_metadata),
            ("🔐 Hash Analysis", self.hash_analysis),
            ("💾 Save HTML", self.save_html),
            ("📋 Copy All", self.copy_all),
            ("🌍 Deep GPS", lambda: self.show_page(6)),
            ("📅 Timeline", lambda: self.show_page(7)),
            ("🔐 Steganography", lambda: self.show_page(8)),
            ("ℹ️ Info", lambda: self.show_page(9)),
            ("👤 Face Detection", lambda: self.show_page(10)),
            ("👥 Face Matching", lambda: self.show_page(11)),
            ("🔬 PRNU Camera", lambda: self.show_page(13))
        ]
        
        for text, cmd in tools:
            btn = tk.Button(btn_frame, text=text, command=cmd,
                           bg=self.colors['header'], fg=self.colors['text'],
                           font=self.fonts['normal'], relief=tk.FLAT, pady=6)
            btn.pack(fill=tk.X, pady=4)
            
    def create_analysis_box(self, parent):
        self.analysis_text = scrolledtext.ScrolledText(parent, bg=self.colors['card'], 
                                                        fg=self.colors['text'],
                                                        font=self.fonts['mono'],
                                                        wrap=tk.WORD, height=12)
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Button(parent, text="▶ REFRESH", command=self.run_analysis,
                 bg=self.colors['accent'], fg='#0a0e27', font=self.fonts['normal']).pack(pady=10)
        
    def create_statusbar(self):
        footer = tk.Frame(self.root, bg=self.colors['header'], height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(footer, text="✅ Ready", bg=self.colors['header'],
                                      fg=self.colors['text2'], font=self.fonts['small'])
        self.status_label.pack(side=tk.LEFT, padx=15)
        
        tips = "← → : Pages | PgUp/PgDn : Images | 14 Pages | PRNU Camera Fingerprinting New!"
        tk.Label(footer, text=tips, bg=self.colors['header'], fg=self.colors['text2'],
                font=self.fonts['small']).pack(side=tk.RIGHT, padx=15)
        
    def bind_shortcuts(self):
        self.root.bind('<Left>', lambda e: self.prev_page())
        self.root.bind('<Right>', lambda e: self.next_page())
        self.root.bind('<Prior>', lambda e: self.prev_image())
        self.root.bind('<Next>', lambda e: self.next_image())
        self.root.bind('<Control-o>', lambda e: self.open_images())
        self.root.bind('<Control-s>', lambda e: self.save_html())
        
    def show_page(self, page_num):
        self.current_page = page_num
        for i, page in enumerate(self.pages):
            if i == page_num:
                page.pack(fill=tk.BOTH, expand=True)
                if i < len(self.page_indicators):
                    self.page_indicators[i].config(bg=self.colors['accent'], fg='#0a0e27')
            else:
                page.pack_forget()
                if i < len(self.page_indicators):
                    self.page_indicators[i].config(bg=self.colors['card'], fg=self.colors['text2'])
        
        self.prev_btn.config(state=tk.DISABLED if page_num == 0 else tk.NORMAL)
        self.next_btn.config(state=tk.DISABLED if page_num == len(self.pages)-1 else tk.NORMAL)
        
        if page_num == 2:
            self.run_analysis()
        if page_num == 6:
            self.update_deep_gps_state()
            
    def prev_page(self):
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
            
    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.show_page(self.current_page + 1)
            
    def open_images(self):
        files = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if files:
            self.current_images = list(files)
            self.current_index = 0
            self.img_count.config(text=f"📷 {len(files)} images")
            self.load_image()
            self.update_status(f"Loaded {len(files)} images")
            
    def open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_images = []
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                        self.current_images.append(os.path.join(root, f))
            if self.current_images:
                self.current_index = 0
                self.img_count.config(text=f"📷 {len(self.current_images)} images")
                self.load_image()
                self.update_status(f"Loaded {len(self.current_images)} images")
                
    def load_image(self):
        if not self.current_images:
            return
        path = self.current_images[self.current_index]
        self.display_image(path)
        self.extract_metadata(path)
        self.img_counter.config(text=f"{self.current_index + 1}/{len(self.current_images)}")
        self.run_analysis()
        self.update_deep_gps_state()
        
        # Reset displays
        self.thumb_image_label.config(text="Click 'EXTRACT THUMBNAIL' to start\n\nThumbnail will appear here", image="")
        self.thumb_status.config(text="Not Extracted")
        self.save_thumb_btn.config(state=tk.DISABLED)
        self.thumbnail_data = None
        self.ela_image_label.config(text="Result will appear here", image="")
        self.ela_score.config(text="Not analyzed")
        self.deep_gps_result.delete(1.0, tk.END)
        self.timeline_text.delete(1.0, tk.END)
        self.timeline_text.insert(1.0, "📅 Click 'GENERATE TIMELINE' to begin analysis")
        self.steg_result_text.delete(1.0, tk.END)
        self.face_result_text.delete(1.0, tk.END)
        self.match_result_text.delete(1.0, tk.END)
        self.match_result_text.insert(1.0, "🔍 Select two face images and click 'COMPARE FACES'")
        self.prnu_result_text.delete(1.0, tk.END)
        self.prnu_result_text.insert(1.0, "🔬 PRNU CAMERA FINGERPRINTING\n\nSelect an image and click 'ANALYZE CAMERA NOISE'")
        
    def display_image(self, path):
        if not PIL_AVAILABLE:
            self.image_label.config(text="PIL not installed")
            return
        try:
            img = Image.open(path)
            img.thumbnail((200, 160), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
        except Exception as e:
            self.image_label.config(text=f"Error: {str(e)}")
            
    def prev_image(self):
        if self.current_images and self.current_index > 0:
            self.current_index -= 1
            self.load_image()
            self.search_var.set("")
            
    def next_image(self):
        if self.current_images and self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.load_image()
            self.search_var.set("")
            
    def extract_metadata(self, path):
        def extract():
            meta = {'exif': {}, 'gps': None, 'file_stats': {}, 'hashes': {}, 'filename': os.path.basename(path)}
            
            if EXIF_AVAILABLE:
                try:
                    with open(path, 'rb') as f:
                        tags = exifread.process_file(f)
                        for tag, val in tags.items():
                            clean = tag.replace('Image ', '').replace('EXIF ', '').replace('GPS ', '')
                            meta['exif'][clean] = str(val)[:200]
                        meta['gps'] = self.get_gps(tags)
                except:
                    pass
                    
            try:
                s = os.stat(path)
                meta['file_stats'] = {
                    'Size': f"{s.st_size:,} bytes ({s.st_size/1024:.1f} KB)",
                    'Size_MB': s.st_size / (1024 * 1024),
                    'Created': datetime.fromtimestamp(s.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'Modified': datetime.fromtimestamp(s.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
            except:
                pass
                
            meta['hashes'] = self.get_hashes(path)
            self.metadata_cache[path] = meta
            self.root.after(0, lambda: self.update_displays(meta))
            self.root.after(0, lambda: self.run_analysis())
            self.root.after(0, lambda: self.update_deep_gps_state())
            
        threading.Thread(target=extract, daemon=True).start()
        
    def get_gps(self, tags):
        try:
            lat = tags.get('GPS GPSLatitude')
            lon = tags.get('GPS GPSLongitude')
            lat_ref = tags.get('GPS GPSLatitudeRef')
            lon_ref = tags.get('GPS GPSLongitudeRef')
            if lat and lon:
                d1 = float(lat.values[0].num) / float(lat.values[0].den)
                m1 = float(lat.values[1].num) / float(lat.values[1].den)
                s1 = float(lat.values[2].num) / float(lat.values[2].den)
                lat_val = d1 + (m1/60.0) + (s1/3600.0)
                
                d2 = float(lon.values[0].num) / float(lon.values[0].den)
                m2 = float(lon.values[1].num) / float(lon.values[1].den)
                s2 = float(lon.values[2].num) / float(lon.values[2].den)
                lon_val = d2 + (m2/60.0) + (s2/3600.0)
                
                if lat_ref and str(lat_ref) == 'S':
                    lat_val = -lat_val
                if lon_ref and str(lon_ref) == 'W':
                    lon_val = -lon_val
                    
                return {'lat': lat_val, 'lon': lon_val, 'link': f"https://www.google.com/maps?q={lat_val},{lon_val}"}
        except:
            pass
        return None
        
    def get_hashes(self, path):
        h = {}
        try:
            with open(path, 'rb') as f:
                d = f.read()
                h['MD5'] = hashlib.md5(d).hexdigest()[:32]
                h['SHA1'] = hashlib.sha1(d).hexdigest()[:32]
        except:
            pass
        return h
        
    def get_danger(self, meta):
        danger = 0
        if meta.get('gps'):
            danger += 50
        if len(meta.get('exif', {})) > 20:
            danger += 20
        if meta.get('exif', {}).get('ImageMake'):
            danger += 15
        return min(danger, 100)
        
    def update_displays(self, meta):
        for item in self.exif_tree.get_children():
            self.exif_tree.delete(item)
        for tag, val in list(meta.get('exif', {}).items())[:40]:
            self.exif_tree.insert('', 'end', text=tag, values=(val[:120],))
            
        self.gps_text.delete(1.0, tk.END)
        if meta.get('gps'):
            g = meta['gps']
            self.gps_text.insert(1.0, f"📍 GPS FOUND!\n\nLat: {g['lat']}°\nLon: {g['lon']}°\n\n{g['link']}")
            self.map_btn.config(state=tk.NORMAL)
            self.copy_gps_btn.config(state=tk.NORMAL)
            self.gps_text.link = g['link']
            self.gps_text.coords = f"{g['lat']}, {g['lon']}"
        else:
            self.gps_text.insert(1.0, "✅ No GPS data found.\nLocation is safe.")
            self.map_btn.config(state=tk.DISABLED)
            self.copy_gps_btn.config(state=tk.DISABLED)
            
        self.fileinfo_text.delete(1.0, tk.END)
        s = meta.get('file_stats', {})
        h = meta.get('hashes', {})
        self.fileinfo_text.insert(1.0, f"File: {meta.get('filename', 'N/A')}\n")
        self.fileinfo_text.insert(1.0, f"Size: {s.get('Size', 'N/A')}\n")
        self.fileinfo_text.insert(1.0, f"Created: {s.get('Created', 'N/A')}\n")
        self.fileinfo_text.insert(1.0, f"MD5: {h.get('MD5', 'N/A')}\n")
        self.fileinfo_text.insert(1.0, f"Camera: {meta.get('exif', {}).get('ImageMake', 'Unknown')}\n")
        self.fileinfo_text.insert(1.0, f"EXIF Tags: {len(meta.get('exif', {}))}\n")
        
        self.risk_text.delete(1.0, tk.END)
        if meta.get('gps'):
            self.risk_text.insert(1.0, "🔴 CRITICAL: GPS location exposed!\n")
        else:
            self.risk_text.insert(1.0, "🟢 GOOD: No GPS data\n")
        if meta.get('exif', {}).get('ImageMake'):
            self.risk_text.insert(1.0, "🟡 Camera info exposed\n")
            
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, f"EXIF Tags: {len(meta.get('exif', {}))}\n")
        self.stats_text.insert(1.0, f"GPS: {'Yes' if meta.get('gps') else 'No'}\n")
        self.stats_text.insert(1.0, f"Size: {s.get('Size_MB', 0):.2f} MB\n")
        
        d = self.get_danger(meta)
        self.danger_label.config(text=f"{d}%")
        self.danger_progress['value'] = d
        if d >= 70:
            self.danger_label.config(fg=self.colors['danger'])
            self.danger_desc.config(text="HIGH RISK! Do not share!")
        elif d >= 40:
            self.danger_label.config(fg=self.colors['warning'])
            self.danger_desc.config(text="MEDIUM RISK - Remove metadata")
        else:
            self.danger_label.config(fg=self.colors['success'])
            self.danger_desc.config(text="LOW RISK - Safe")
            
    def filter_exif(self):
        search = self.search_var.get().lower()
        if not self.current_images:
            return
        meta = self.metadata_cache.get(self.current_images[self.current_index], {})
        data = meta.get('exif', {})
        
        for item in self.exif_tree.get_children():
            self.exif_tree.delete(item)
            
        if not search:
            for tag, val in list(data.items())[:40]:
                self.exif_tree.insert('', 'end', text=tag, values=(val[:120],))
        else:
            for tag, val in data.items():
                if search in tag.lower() or search in val.lower():
                    self.exif_tree.insert('', 'end', text=tag, values=(val[:120],))
                    
    def run_analysis(self):
        if not self.current_images:
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(1.0, "No image loaded.")
            return
            
        meta = self.metadata_cache.get(self.current_images[self.current_index], {})
        d = self.get_danger(meta)
        
        analysis = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🔍 QUICK ANALYSIS                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  File: {meta.get('filename', 'Unknown')}                    
║                                                              ║
║  📍 GPS: {'FOUND' if meta.get('gps') else 'Not found'}
║  📷 Camera: {meta.get('exif', {}).get('ImageMake', 'Unknown')}
║  📊 EXIF Tags: {len(meta.get('exif', {}))}
║  💀 Danger Level: {d}%
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis)
        
    def extract_thumbnail(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        img_path = self.current_images[self.current_index]
        
        if not img_path.lower().endswith(('.jpg', '.jpeg')):
            messagebox.showinfo("Info", "Thumbnail extraction only works with JPEG files.")
            self.thumb_status.config(text="Not supported (not JPEG)")
            return
        
        self.thumb_progress.start()
        self.thumb_btn.config(state=tk.DISABLED, text="⏳ EXTRACTING...")
        self.thumb_status.config(text="Extracting...")
        self.update_status("Extracting thumbnail...")
        
        thread = threading.Thread(target=self._extract_thumbnail_worker, daemon=True)
        thread.start()
        
    def _extract_thumbnail_worker(self):
        img_path = self.current_images[self.current_index]
        
        try:
            if EXIF_AVAILABLE:
                with open(img_path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    
                    if 'JPEGThumbnail' in tags:
                        thumb_data = tags['JPEGThumbnail']
                        
                        if hasattr(thumb_data, 'bytes'):
                            thumb_bytes = thumb_data.bytes
                        else:
                            thumb_bytes = bytes(thumb_data)
                        
                        if len(thumb_bytes) > 100:
                            self.thumbnail_data = thumb_bytes
                            
                            thumb_img = Image.open(io.BytesIO(thumb_bytes))
                            thumb_img.thumbnail((300, 250), Image.Resampling.LANCZOS)
                            thumb_photo = ImageTk.PhotoImage(thumb_img)
                            thumb_size = len(thumb_bytes)
                            thumb_dim = f"{thumb_img.width} x {thumb_img.height}"
                            
                            self.root.after(0, lambda: self._update_thumbnail_ui(
                                thumb_photo, thumb_size, thumb_dim, "✅ Thumbnail extracted successfully!"))
                            return
                    
            self.root.after(0, self._thumbnail_not_found_ui)
            
        except Exception as e:
            self.root.after(0, lambda: self._thumbnail_error_ui(str(e)))
            
    def _update_thumbnail_ui(self, thumb_photo, size, dim, status):
        self.thumb_progress.stop()
        self.thumb_btn.config(state=tk.NORMAL, text="🔍 EXTRACT THUMBNAIL")
        self.thumb_image_label.config(image=thumb_photo, text="")
        self.thumb_image_label.image = thumb_photo
        self.thumb_status.config(text=status, fg=self.colors['success'])
        self.save_thumb_btn.config(state=tk.NORMAL)
        self.update_status(f"Thumbnail extracted: {size} bytes, {dim}")
        
    def _thumbnail_not_found_ui(self):
        self.thumb_progress.stop()
        self.thumb_btn.config(state=tk.NORMAL, text="🔍 EXTRACT THUMBNAIL")
        self.thumb_image_label.config(text="❌ No thumbnail found", image="")
        self.thumb_status.config(text="No thumbnail found", fg=self.colors['warning'])
        self.update_status("No thumbnail found")
        
    def _thumbnail_error_ui(self, error_msg):
        self.thumb_progress.stop()
        self.thumb_btn.config(state=tk.NORMAL, text="🔍 EXTRACT THUMBNAIL")
        self.thumb_image_label.config(text=f"Error: {error_msg}", image="")
        self.thumb_status.config(text="Error", fg=self.colors['danger'])
        self.update_status(f"Thumbnail error: {error_msg}")
        
    def save_thumbnail(self):
        if not self.thumbnail_data:
            messagebox.showwarning("Warning", "No thumbnail extracted yet!")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg")],
            initialfile=f"thumbnail_{os.path.basename(self.current_images[self.current_index]).split('.')[0]}.jpg"
        )
        
        if save_path:
            try:
                with open(save_path, 'wb') as f:
                    f.write(self.thumbnail_data)
                self.update_status("Thumbnail saved!")
                messagebox.showinfo("Success", f"Thumbnail saved to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def start_reverse_search(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        engines = []
        if self.search_google.get():
            engines.append("Google")
        if self.search_tineye.get():
            engines.append("TinEye")
        if self.search_yandex.get():
            engines.append("Yandex")
        if self.search_bing.get():
            engines.append("Bing")
        
        if not engines:
            messagebox.showwarning("Warning", "Select at least one search engine!")
            return
        
        self.search_progress.start()
        self.search_btn.config(state=tk.DISABLED, text="⏳ OPENING...")
        self.update_status("Opening search engines...")
        
        self.search_result_text.delete(1.0, tk.END)
        self.search_result_text.insert(1.0, f"🔍 Searching for: {os.path.basename(self.current_images[self.current_index])}\n\n")
        self.search_result_text.insert(1.0, "Opening browsers for:\n")
        
        for engine in engines:
            self.search_result_text.insert(1.0, f"  • {engine}\n")
            url = self._get_search_url(engine.lower())
            if url:
                webbrowser.open(url)
        
        self.search_result_text.insert(1.0, "\n✅ Search browsers opened!\n\n")
        self.search_result_text.insert(1.0, "💡 After browser opens, click 'Upload Image' and select your file.\n")
        
        self.search_progress.stop()
        self.search_btn.config(state=tk.NORMAL, text="🔍 START SEARCH")
        self.update_status("Search browsers opened")
        
    def _get_search_url(self, engine):
        if engine == "google":
            return "https://images.google.com/"
        elif engine == "tineye":
            return "https://tineye.com/"
        elif engine == "yandex":
            return "https://yandex.com/images/"
        elif engine == "bing":
            return "https://www.bing.com/visualsearch"
        return None
        
    def update_deep_gps_state(self):
        if not self.current_images or self.current_index >= len(self.current_images):
            if hasattr(self, 'deep_gps_btn'):
                self.deep_gps_btn.config(state=tk.DISABLED)
                self.open_map_btn.config(state=tk.DISABLED)
                self.deep_gps_coords.config(text="No GPS data found")
            return
            
        meta = self.metadata_cache.get(self.current_images[self.current_index], {})
        gps = meta.get('gps')
        
        if gps:
            self.deep_gps_coords.config(text=f"📍 Latitude: {gps['lat']}°\n📍 Longitude: {gps['lon']}°")
            self.deep_gps_btn.config(state=tk.NORMAL)
            self.open_map_btn.config(state=tk.NORMAL)
        else:
            self.deep_gps_coords.config(text="No GPS data found")
            self.deep_gps_btn.config(state=tk.DISABLED)
            self.open_map_btn.config(state=tk.DISABLED)
            
    def open_gps_maps(self):
        if self.current_images and self.current_index < len(self.current_images):
            meta = self.metadata_cache.get(self.current_images[self.current_index], {})
            gps = meta.get('gps')
            if gps and 'link' in gps:
                webbrowser.open(gps['link'])
                
    def analyze_deep_gps(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        meta = self.metadata_cache.get(self.current_images[self.current_index], {})
        gps = meta.get('gps')
        
        if not gps:
            messagebox.showwarning("Warning", "No GPS data found!")
            return
        
        self.deep_gps_progress.start()
        self.deep_gps_btn.config(state=tk.DISABLED, text="⏳ ANALYZING...")
        self.update_status("Analyzing location...")
        
        thread = threading.Thread(target=self._perform_deep_gps_analysis, args=(gps,), daemon=True)
        thread.start()
        
    def _perform_deep_gps_analysis(self, gps):
        lat = gps['lat']
        lon = gps['lon']
        
        result_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🌍 DEEP GPS ANALYSIS                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📍 COORDINATES:                                            ║
║  Latitude:  {lat}°                                          ║
║  Longitude: {lon}°                                          ║
║                                                              ║
"""
        
        try:
            import json as json_lib
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1&accept-language=en"
            headers = {'User-Agent': 'HexaVision/9.0'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json_lib.loads(response.read().decode('utf-8'))
                
                if 'display_name' in data:
                    result_text += f"""
  📍 FULL ADDRESS:
  {data['display_name']}
"""
                
                if 'address' in data:
                    addr = data['address']
                    result_text += """
  📋 ADDRESS DETAILS:
"""
                    if 'road' in addr:
                        result_text += f"  • Road/Street: {addr['road']}\n"
                    if 'city' in addr:
                        result_text += f"  • City: {addr['city']}\n"
                    if 'state' in addr:
                        result_text += f"  • State: {addr['state']}\n"
                    if 'postcode' in addr:
                        result_text += f"  • Postal Code: {addr['postcode']}\n"
                    if 'country' in addr:
                        result_text += f"  • Country: {addr['country']}\n"
        except Exception as e:
            result_text += f"\n  ❌ Error: {str(e)}\n"
        
        result_text += f"""
  🔗 Google Maps: https://maps.google.com/?q={lat},{lon}
  
  ⚠️ PRIVACY WARNING: This location information is sensitive!
"""
        
        self.root.after(0, lambda: self._update_deep_gps_results(result_text))
        
    def _update_deep_gps_results(self, result_text):
        self.deep_gps_progress.stop()
        self.deep_gps_btn.config(state=tk.NORMAL, text="🌍 ANALYZE LOCATION")
        self.deep_gps_result.delete(1.0, tk.END)
        self.deep_gps_result.insert(1.0, result_text)
        self.update_status("Deep GPS analysis completed")
        
    def generate_timeline(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        self.timeline_progress.start()
        self.timeline_btn.config(state=tk.DISABLED, text="⏳ GENERATING...")
        self.update_status("Generating timeline...")
        
        thread = threading.Thread(target=self._generate_timeline_worker, daemon=True)
        thread.start()
        
    def _generate_timeline_worker(self):
        img_path = self.current_images[self.current_index]
        meta = self.metadata_cache.get(img_path, {})
        
        timeline_events = []
        
        file_stats = meta.get('file_stats', {})
        
        if 'Created' in file_stats:
            try:
                created_date = datetime.strptime(file_stats['Created'], '%Y-%m-%d %H:%M:%S')
                timeline_events.append({'event': '📁 File Created', 'date': created_date})
            except:
                pass
        
        if 'Modified' in file_stats:
            try:
                modified_date = datetime.strptime(file_stats['Modified'], '%Y-%m-%d %H:%M:%S')
                timeline_events.append({'event': '✏️ File Modified', 'date': modified_date})
            except:
                pass
        
        exif_data = meta.get('exif', {})
        if 'EXIFDateTimeOriginal' in exif_data:
            date_str = exif_data['EXIFDateTimeOriginal']
            try:
                taken_date = datetime.strptime(date_str[:19], '%Y:%m:%d %H:%M:%S')
                timeline_events.append({'event': '📷 Photo Taken', 'date': taken_date})
            except:
                pass
        
        events_with_date = [e for e in timeline_events if e.get('date') is not None]
        events_with_date.sort(key=lambda x: x['date'])
        
        result = f"""
╔══════════════════════════════════════════════════════════════╗
║                    📅 TIMELINE ANALYSIS                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
  📊 Total Events Found: {len(events_with_date)}
  ┌────────────────────────────────────────────────────────┐
"""
        for i, event in enumerate(events_with_date):
            date_str = event['date'].strftime('%Y-%m-%d %H:%M:%S')
            result += f"  │  {i+1:2}. {event['event'][:18]} │ {date_str} │\n"
        
        result += """  └────────────────────────────────────────────────────────┘
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
"""
        
        taken_event = None
        modified_event = None
        
        for e in events_with_date:
            if 'Photo Taken' in e['event']:
                taken_event = e
            if 'File Modified' in e['event']:
                modified_event = e
        
        if taken_event:
            result += f"  📸 Photo taken: {taken_event['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        if modified_event:
            result += f"  ✏️ Last modified: {modified_event['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if taken_event and modified_event and modified_event['date'] > taken_event['date']:
            days = (modified_event['date'] - taken_event['date']).days
            result += f"\n  ⚠️ Modified {days} days after being taken!\n"
            result += "  🔴 Image may have been edited.\n"
        
        result += """
╚══════════════════════════════════════════════════════════════╝
"""
        
        self.root.after(0, lambda: self._update_timeline_results(result))
        
    def _update_timeline_results(self, result_text):
        self.timeline_progress.stop()
        self.timeline_btn.config(state=tk.NORMAL, text="📅 GENERATE TIMELINE")
        self.timeline_text.delete(1.0, tk.END)
        self.timeline_text.insert(1.0, result_text)
        self.update_status("Timeline analysis completed")
        
    def run_ela(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        if not PIL_AVAILABLE:
            messagebox.showerror("Error", "PIL not installed!")
            return
        
        if self.ela_running:
            messagebox.showinfo("Info", "ELA already running!")
            return
        
        self.ela_running = True
        self.ela_progress.start()
        self.ela_btn.config(state=tk.DISABLED, text="⏳ ANALYZING...")
        self.ela_image_label.config(text="Processing...")
        self.update_status("Running ELA...")
        
        thread = threading.Thread(target=self._ela_worker, daemon=True)
        thread.start()
        
    def _ela_worker(self):
        img_path = self.current_images[self.current_index]
        quality = self.ela_quality.get()
        
        try:
            original = Image.open(img_path).convert('RGB')
            original.thumbnail((600, 600), Image.Resampling.LANCZOS)
            
            temp_path = "/tmp/ela_temp.jpg"
            original.save(temp_path, 'JPEG', quality=quality)
            compressed = Image.open(temp_path)
            
            diff = ImageChops.difference(original, compressed)
            
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            if max_diff == 0:
                max_diff = 1
            scale = 255.0 / max_diff
            diff = Image.eval(diff, lambda x: x * scale)
            
            if diff.mode != 'RGB':
                diff = diff.convert('RGB')
            
            diff_array = np.array(diff)
            score = np.mean(diff_array) / 255.0 * 100
            
            diff.thumbnail((350, 280), Image.Resampling.LANCZOS)
            ela_photo = ImageTk.PhotoImage(diff)
            
            if score > 30:
                verdict = "🔴 HIGH MANIPULATION!"
                color = self.colors['danger']
            elif score > 15:
                verdict = "🟡 MEDIUM MANIPULATION!"
                color = self.colors['warning']
            elif score > 5:
                verdict = "🟠 LOW MANIPULATION"
                color = self.colors['accent2']
            else:
                verdict = "🟢 LIKELY ORIGINAL"
                color = self.colors['success']
            
            self.root.after(0, lambda: self._update_ela_ui(ela_photo, score, verdict, color))
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        except Exception as e:
            self.root.after(0, lambda: self._ela_error_ui(str(e)))
            
    def _update_ela_ui(self, ela_photo, score, verdict, color):
        self.ela_progress.stop()
        self.ela_btn.config(state=tk.NORMAL, text="🔬 RUN ELA")
        self.ela_image_label.config(image=ela_photo, text="")
        self.ela_image_label.image = ela_photo
        self.ela_score.config(text=f"{score:.1f}% - {verdict}", fg=color)
        self.ela_running = False
        self.update_status(f"ELA Score: {score:.1f}%")
        
    def _ela_error_ui(self, error_msg):
        self.ela_progress.stop()
        self.ela_btn.config(state=tk.NORMAL, text="🔬 RUN ELA")
        self.ela_image_label.config(text=f"Error: {error_msg}", image="")
        self.ela_score.config(text="Error")
        self.ela_running = False
        self.update_status(f"ELA Error: {error_msg}")
        
    def open_maps(self):
        if hasattr(self.gps_text, 'link'):
            webbrowser.open(self.gps_text.link)
            
    def copy_gps(self):
        if hasattr(self.gps_text, 'coords'):
            self.root.clipboard_clear()
            self.root.clipboard_append(self.gps_text.coords)
            self.update_status("GPS copied!")
            messagebox.showinfo("Copied", f"GPS: {self.gps_text.coords}")
            
    def copy_all(self):
        if self.current_images:
            meta = self.metadata_cache.get(self.current_images[self.current_index], {})
            self.root.clipboard_clear()
            self.root.clipboard_append(json.dumps(meta, indent=2, default=str))
            self.update_status("Metadata copied!")
            messagebox.showinfo("Copied", "Metadata copied!")
            
    def save_html(self):
        if not self.current_images:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if path:
            meta = self.metadata_cache.get(self.current_images[self.current_index], {})
            d = self.get_danger(meta)
            html = self.generate_html(meta, d)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            self.update_status("HTML saved!")
            webbrowser.open(path)
            
    def generate_html(self, meta, danger):
        exif_data = meta.get('exif', {})
        gps = meta.get('gps')
        stats = meta.get('file_stats', {})
        hashes = meta.get('hashes', {})
        
        exif_rows = ""
        for tag, val in list(exif_data.items())[:30]:
            exif_rows += f"<tr><td class='tag'><strong>{self.escape_html(tag)}</strong>侧<td class='value'>{self.escape_html(str(val)[:100])}侧</td>"
            
        gps_html = ""
        if gps:
            gps_html = f"<p><strong>Latitude:</strong> {gps['lat']}°</p><p><strong>Longitude:</strong> {gps['lon']}°</p><p><a href='{gps['link']}' target='_blank'>🗺️ View Map</a></p>"
        else:
            gps_html = "<p>No GPS data found</p>"
            
        return f"""<!DOCTYPE html>
<html>
<head><title>HexaVision Report</title>
<style>
body {{ font-family: Arial; background: #0a0e27; color: #fff; padding: 20px; }}
.container {{ max-width: 1000px; margin: 0 auto; background: #131b3c; border-radius: 10px; padding: 20px; }}
h1 {{ color: #00d9ff; }}
.danger {{ background: {'#ff3366' if danger > 40 else '#00ff88'}; padding: 10px; text-align: center; border-radius: 5px; }}
table {{ width: 100%; border-collapse: collapse; }}
td {{ padding: 8px; border-bottom: 1px solid #2d3748; }}
.tag {{ font-weight: bold; width: 30%; }}
</style>
</head>
<body>
<div class="container">
<h1>🔍 HexaVision - Forensics Report</h1>
<p>File: {self.escape_html(meta.get('filename', 'Unknown'))}</p>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<div class="danger">💀 Danger Level: {danger}%</div>
<h2>📷 EXIF Data</h2>
80
<th>Tag</th><th>Value</th>
{exif_rows}
</table>
<h2>📍 GPS Location</h2>
{gps_html}
<h2>📁 File Information</h2>
表
    <tr><td class="tag">Size侧<td>{stats.get('Size', 'N/A')}侧</tr>
    <tr><td class="tag">Created侧<td>{stats.get('Created', 'N/A')}侧</tr>
    </table>
</div>
</body>
</html>"""
        
    def escape_html(self, text):
        if not text:
            return "N/A"
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", "&#39;")
        
    def export_json(self):
        if not self.current_images:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            all_meta = {}
            for img in self.current_images:
                all_meta[os.path.basename(img)] = self.metadata_cache.get(img, {})
            with open(path, 'w') as f:
                json.dump(all_meta, f, indent=2, default=str)
            self.update_status("JSON saved!")
            messagebox.showinfo("Success", "JSON exported!")
            
    def strip_metadata(self):
        if not self.current_images or not PIL_AVAILABLE:
            return
        if messagebox.askyesno("Confirm", "Remove ALL metadata?\nCannot be undone!"):
            try:
                img = Image.open(self.current_images[self.current_index])
                path = filedialog.asksaveasfilename(defaultextension=".jpg")
                if path:
                    img.save(path)
                    self.update_status("Metadata stripped!")
                    messagebox.showinfo("Success", "Metadata stripped!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def hash_analysis(self):
        if not self.current_images:
            return
        meta = self.metadata_cache.get(self.current_images[self.current_index], {})
        h = meta.get('hashes', {})
        msg = f"🔐 HASH ANALYSIS\n\nMD5: {h.get('MD5', 'N/A')}\n\nSHA1: {h.get('SHA1', 'N/A')}"
        messagebox.showinfo("Hash Analysis", msg)
        
    def update_status(self, msg):
        self.status_label.config(text=f"✅ {msg}")
        
    def show_help(self):
        help_text = """🔍 HEXAVISION v9.0 - USER GUIDE

📄 PAGES (14 Pages):
• Page 1-8: Basic Forensics
• Page 9: 🔐 Steganography Detection
• Page 10: ℹ️ Tool Information
• Page 11: 👤 Face Detection
• Page 12: 👥 Face Matching
• Page 13: 📋 About
• Page 14: 🔬 PRNU CAMERA FINGERPRINTING (NEW!)

🔬 PRNU CAMERA FINGERPRINTING (Page 14):
• Every camera has unique sensor noise pattern
• Can identify exact camera device
• Steps:
  1. 'ANALYZE CAMERA NOISE' - See noise pattern
  2. 'EXTRACT AS REFERENCE' - Save as reference
  3. 'COMPARE WITH REFERENCE' - Match another image

👤 FACE DETECTION (Page 11):
• Find faces in images

👥 FACE MATCHING (Page 12):
• Compare two faces

🎮 SHORTCUTS:
• ← → : Change pages
• PgUp/PgDn : Browse images
• Ctrl+O : Open images
• Ctrl+S : Save HTML

⚙️ REQUIREMENTS:
pip install opencv-python pillow exifread numpy pywavelets"""
        messagebox.showinfo("Help", help_text)
        
    def show_about(self):
        about = """HEXAVISION ENTERPRISE v9.0

Professional Image Forensics Suite

Features:
• EXIF Metadata Extraction
• GPS Location Detection
• Error Level Analysis (ELA)
• Thumbnail Extraction
• Reverse Image Search
• Deep GPS Analysis
• Timeline Analysis
• Steganography Detection
• Face Detection
• Face Matching
• 🔬 PRNU Camera Fingerprinting (NEW!)
• HTML/JSON Export

For educational purposes only.

HexaNet Prime - AI Powered. Hacker Driven."""
        messagebox.showinfo("About", about)
        
def main():
    root = tk.Tk()
    app = HexaVision(root)
    root.mainloop()

if __name__ == "__main__":
    main()
