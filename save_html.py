#!/usr/bin/env python3
"""
HTML Save Module - Professional Design
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import webbrowser
import os

def save_metadata_as_html(root, metadata, danger_level):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        initialfile=f"{metadata.get('filename', 'metadata_report')}.html"
    )
    if not save_path:
        return
        
    html_content = generate_html_report(metadata, danger_level)
    
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        messagebox.showinfo("Success", f"HTML Report saved!\n{save_path}")
        webbrowser.open(save_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def generate_html_report(metadata, danger_level):
    exif_data = metadata.get('exif', {})
    gps_data = metadata.get('gps')
    file_stats = metadata.get('file_stats', {})
    hashes = metadata.get('hashes', {})
    
    if danger_level >= 70:
        risk_color = "#ff3366"
        risk_text = "HIGH RISK"
    elif danger_level >= 40:
        risk_color = "#ffaa00"
        risk_text = "MEDIUM RISK"
    else:
        risk_color = "#00ff88"
        risk_text = "LOW RISK"
        
    exif_rows = ""
    for tag, value in list(exif_data.items())[:50]:
        exif_rows += f"<tr><td class='tag'>{escape_html(tag)}</td><td class='value'>{escape_html(str(value)[:200])}</td></tr>"
        
    gps_html = ""
    if gps_data:
        gps_html = f"""
        <div class="gps-card">
            <h3>📍 GPS Coordinates Found!</h3>
            <p><strong>Latitude:</strong> {gps_data.get('lat', 'N/A')}°</p>
            <p><strong>Longitude:</strong> {gps_data.get('lon', 'N/A')}°</p>
            <p><strong>DMS Latitude:</strong> {gps_data.get('dms_lat', 'N/A')}</p>
            <p><strong>DMS Longitude:</strong> {gps_data.get('dms_lon', 'N/A')}</p>
            <p><a href="{gps_data.get('link', '#')}" target="_blank" class="map-link">🗺️ View on Google Maps</a></p>
            <div class="warning">⚠️ WARNING: Your exact location is exposed!</div>
        </div>
        """
    else:
        gps_html = '<div class="gps-card"><h3>📍 GPS Location</h3><p class="safe">✅ No GPS coordinates found. Location data is safe.</p></div>'
        
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Metadata Report - {escape_html(metadata.get('filename', 'Report'))}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #131b3c 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #0f1535;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #00d9ff 0%, #7000ff 100%);
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ color: white; font-size: 28px; margin-bottom: 10px; }}
        .header p {{ color: rgba(255,255,255,0.9); font-size: 14px; }}
        .danger-bar {{ background: {risk_color}; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; color: white; }}
        .content {{ padding: 30px; }}
        .section {{
            background: #1a2350;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        .section h2 {{
            color: #00d9ff;
            border-bottom: 2px solid #00d9ff;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #2d3748; }}
        th {{ background: #00d9ff; color: #0a0e27; }}
        .tag {{ font-weight: bold; width: 30%; background: #0f1535; color: #00d9ff; }}
        .value {{ width: 70%; font-family: monospace; color: #fff; }}
        .gps-card {{
            background: #0f1535;
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .gps-card h3 {{ color: #00d9ff; margin-bottom: 15px; }}
        .gps-card p {{ margin: 8px 0; color: #fff; }}
        .map-link {{
            display: inline-block;
            background: #00d9ff;
            color: #0a0e27;
            padding: 8px 15px;
            border-radius: 5px;
            text-decoration: none;
            margin-top: 10px;
        }}
        .warning {{
            background: #ff3366;
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
            color: white;
            text-align: center;
        }}
        .safe {{ color: #00ff88; font-weight: bold; }}
        .footer {{
            background: #0a0e27;
            text-align: center;
            padding: 20px;
            color: #718096;
            font-size: 12px;
        }}
        @media (max-width: 768px) {{
            .container {{ margin: 10px; }}
            .content {{ padding: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📸 IMAGE METADATA FORENSICS REPORT</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>File: <strong>{escape_html(metadata.get('filename', 'Unknown'))}</strong></p>
        </div>
        
        <div class="danger-bar">
            💀 DANGER LEVEL: {danger_level}% - {risk_text}
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📷 EXIF METADATA</h2>
                <table>
                    <tr><th>Tag</th><th>Value</th></tr>
                    {exif_rows}
                </table>
            </div>
            
            <div class="section">
                <h2>📍 GPS LOCATION</h2>
                {gps_html}
            </div>
            
            <div class="section">
                <h2>📁 FILE INFORMATION</h2>
                <table>
                    <tr><td class="tag">File Size</td><td>{file_stats.get('Size', 'N/A')}</td></tr>
                    <tr><td class="tag">Created</td><td>{file_stats.get('Created', 'N/A')}</td></tr>
                    <tr><td class="tag">Modified</td><td>{file_stats.get('Modified', 'N/A')}</td></tr>
                    <tr><td class="tag">MD5</td><td class="value">{hashes.get('MD5', 'N/A')}</td></tr>
                    <tr><td class="tag">SHA1</td><td class="value">{hashes.get('SHA1', 'N/A')}</td></tr>
                    <tr><td class="tag">SHA256</td><td class="value">{hashes.get('SHA256', 'N/A')}</td></tr>
                    <tr><td class="tag">Camera Make</td><td>{metadata.get('exif', {}).get('ImageMake', 'Unknown')}</td></tr>
                    <tr><td class="tag">Camera Model</td><td>{metadata.get('exif', {}).get('ImageModel', 'Unknown')}</td></tr>
                    <tr><td class="tag">Total EXIF Tags</td><td>{len(metadata.get('exif', {}))}</td></tr>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Professional Image Metadata Extractor Pro v5.0</p>
            <p>For educational and forensic purposes only</p>
        </div>
    </div>
</body>
</html>
    """
    return html

def escape_html(text):
    if not text:
        return "N/A"
    text = str(text)
    replacements = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    return text
