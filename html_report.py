#!/usr/bin/env python3
"""
Professional HTML Report Generator
All GUI data is shown in beautiful HTML format
"""

from datetime import datetime
import os

def generate_html_report(metadata, danger_level, image_path):
    """
    Generate professional HTML report from metadata
    
    Args:
        metadata: Dictionary containing all extracted metadata
        danger_level: Integer 0-100 danger level
        image_path: Path to the original image file
    
    Returns:
        HTML string for the report
    """
    
    # Extract data from metadata
    exif_data = metadata.get('exif', {})
    gps_data = metadata.get('gps')
    file_stats = metadata.get('file_stats', {})
    hashes = metadata.get('hashes', {})
    filename = metadata.get('filename', 'Unknown')
    
    # Determine danger level class and message
    if danger_level >= 70:
        danger_class = "danger-high"
        danger_text = "HIGH RISK"
        danger_message = "⚠️ DO NOT SHARE this image publicly! Contains sensitive location data."
    elif danger_level >= 40:
        danger_class = "danger-medium"
        danger_text = "MEDIUM RISK"
        danger_message = "⚠️ Remove metadata before sharing online."
    else:
        danger_class = "danger-low"
        danger_text = "LOW RISK"
        danger_message = "✅ Safe to share. No major privacy concerns detected."
    
    # Build EXIF table rows
    exif_rows = ""
    for tag, value in list(exif_data.items())[:60]:
        exif_rows += f"""
                        <tr>
                            <td class="tag-cell">{escape_html(tag)}</td>
                            <td class="value-cell">{escape_html(str(value)[:300])}</td>
                        </tr>
                    """
    
    if not exif_rows:
        exif_rows = '<tr><td colspan="2" class="no-data">No EXIF data found</td></tr>'
    
    # Build GPS section
    gps_html = ""
    if gps_data:
        gps_html = f"""
                    <div class="gps-card">
                        <h3>📍 GPS Coordinates Found!</h3>
                        <div class="gps-coords">
                            <div class="coord-row">
                                <span class="coord-label">Latitude (Decimal):</span>
                                <span class="coord-value">{gps_data.get('lat', 'N/A')}°</span>
                            </div>
                            <div class="coord-row">
                                <span class="coord-label">Longitude (Decimal):</span>
                                <span class="coord-value">{gps_data.get('lon', 'N/A')}°</span>
                            </div>
                        </div>
                        <div class="gps-link">
                            <a href="{gps_data.get('link', '#')}" target="_blank" class="map-button">
                                🗺️ View on Google Maps
                            </a>
                        </div>
                        <div class="gps-warning">
                            ⚠️ WARNING: This image contains exact GPS coordinates!
                            Your location privacy is at risk.
                        </div>
                    </div>
                    """
    else:
        gps_html = """
                    <div class="gps-card safe">
                        <h3>📍 GPS Location Status</h3>
                        <p class="safe-text">✅ No GPS coordinates found in this image.</p>
                        <p>Location data is safe. No privacy risk from geolocation.</p>
                    </div>
                    """
    
    # Build file information table
    file_info_rows = f"""
                        <tr>
                            <td class="info-label">Filename</td>
                            <td class="info-value">{escape_html(filename)}</td>
                        </tr>
                        <tr>
                            <td class="info-label">File Size</td>
                            <td class="info-value">{escape_html(file_stats.get('Size', 'N/A'))}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Created</td>
                            <td class="info-value">{escape_html(file_stats.get('Created', 'N/A'))}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Modified</td>
                            <td class="info-value">{escape_html(file_stats.get('Modified', 'N/A'))}</td>
                        </tr>
                        <tr>
                            <td class="info-label">File Path</td>
                            <td class="info-value path-value">{escape_html(image_path)}</td>
                        </tr>
                    """
    
    # Build camera info
    camera_make = exif_data.get('ImageMake', 'Unknown')
    camera_model = exif_data.get('ImageModel', 'Unknown')
    datetime_original = exif_data.get('EXIFDateTimeOriginal', 'Not found')
    exposure_time = exif_data.get('EXIFExposureTime', 'Not found')
    iso = exif_data.get('EXIFISOSpeedRatings', 'Not found')
    focal_length = exif_data.get('EXIFFocalLength', 'Not found')
    aperture = exif_data.get('EXIFApertureValue', 'Not found')
    flash = exif_data.get('EXIFFlash', 'Not found')
    
    # Build hash table
    hash_rows = f"""
                        <tr>
                            <td class="hash-label">MD5</td>
                            <td class="hash-value"><code>{escape_html(hashes.get('MD5', 'N/A'))}</code></td>
                        </tr>
                        <tr>
                            <td class="hash-label">SHA1</td>
                            <td class="hash-value"><code>{escape_html(hashes.get('SHA1', 'N/A'))}</code></td>
                        </tr>
                        <tr>
                            <td class="hash-label">SHA256</td>
                            <td class="hash-value"><code>{escape_html(hashes.get('SHA256', 'N/A'))}</code></td>
                        </tr>
                    """
    
    # Build statistics
    stats_html = f"""
                    <div class="stat-card">
                        <div class="stat-number">{len(exif_data)}</div>
                        <div class="stat-label">EXIF Tags</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{'✓' if gps_data else '✗'}</div>
                        <div class="stat-label">GPS Data</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{file_stats.get('Size_MB', 0):.1f}</div>
                        <div class="stat-label">Size (MB)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{danger_level}</div>
                        <div class="stat-label">Danger Level</div>
                    </div>
                    """
    
    # Build recommendations based on analysis
    recommendations = []
    if gps_data:
        recommendations.append("🔴 Remove GPS metadata using metadata stripper tool")
    else:
        recommendations.append("✅ No GPS data - Good for privacy!")
    
    if camera_make != 'Unknown':
        recommendations.append("🟡 Consider removing camera information for better privacy")
    else:
        recommendations.append("✅ No camera information detected")
    
    if datetime_original != 'Not found':
        recommendations.append("🟡 Timestamp information is available")
    
    if len(exif_data) > 30:
        recommendations.append("🟡 Large amount of metadata detected")
    
    if danger_level > 40:
        recommendations.append("🔴 Use 'Strip Metadata' tool before sharing online")
    else:
        recommendations.append("✅ Current metadata level is acceptable")
    
    recommendations_html = ""
    for rec in recommendations:
        recommendations_html += f"<li>{rec}</li>"
    
    # Complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Metadata Forensics Report - {escape_html(filename)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            padding: 30px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            text-align: center;
            color: white;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }}
        
        .header .subtitle {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .file-info {{
            margin-top: 15px;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            font-size: 13px;
        }}
        
        /* Danger Bar */
        .danger-bar {{
            padding: 20px;
            text-align: center;
            color: white;
        }}
        
        .danger-high {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .danger-medium {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        
        .danger-low {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        
        .danger-level {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .danger-text {{
            font-size: 18px;
            font-weight: 500;
        }}
        
        .danger-message {{
            font-size: 14px;
            margin-top: 10px;
            opacity: 0.95;
        }}
        
        /* Content */
        .content {{
            padding: 30px;
        }}
        
        /* Section Styles */
        .section {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 22px;
        }}
        
        /* Tables */
        .exif-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        
        .exif-table tr {{
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .exif-table tr:hover {{
            background: #f0f0f0;
        }}
        
        .tag-cell {{
            font-weight: 600;
            width: 30%;
            padding: 10px;
            color: #667eea;
            background: #f0f0f0;
        }}
        
        .value-cell {{
            padding: 10px;
            color: #333;
            word-break: break-word;
            font-family: 'Consolas', monospace;
        }}
        
        .no-data {{
            text-align: center;
            padding: 20px;
            color: #999;
        }}
        
        /* GPS Card */
        .gps-card {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .gps-card h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .gps-card.safe {{
            border-left-color: #11998e;
        }}
        
        .gps-coords {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .coord-row {{
            margin: 8px 0;
        }}
        
        .coord-label {{
            font-weight: 600;
            color: #555;
            display: inline-block;
            width: 150px;
        }}
        
        .coord-value {{
            color: #667eea;
            font-weight: 500;
        }}
        
        .gps-link {{
            text-align: center;
            margin: 15px 0;
        }}
        
        .map-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            transition: transform 0.2s;
        }}
        
        .map-button:hover {{
            transform: scale(1.05);
        }}
        
        .gps-warning {{
            background: #fee;
            border-left: 4px solid #f5576c;
            padding: 12px;
            border-radius: 8px;
            color: #c0392b;
            font-weight: 500;
            margin-top: 15px;
        }}
        
        .safe-text {{
            color: #11998e;
            font-weight: 600;
            font-size: 16px;
        }}
        
        /* Info Table */
        .info-table, .hash-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .info-table tr, .hash-table tr {{
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .info-label, .hash-label {{
            font-weight: 600;
            width: 30%;
            padding: 10px;
            color: #555;
        }}
        
        .info-value, .hash-value {{
            padding: 10px;
            color: #333;
        }}
        
        .path-value {{
            font-family: monospace;
            font-size: 11px;
            word-break: break-all;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .stat-card {{
            background: white;
            text-align: center;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
        }}
        
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #888;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Camera Info */
        .camera-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        
        .camera-item {{
            background: white;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .camera-label {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .camera-value {{
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-top: 5px;
        }}
        
        /* Recommendations */
        .recommendations-list {{
            list-style: none;
            padding: 0;
        }}
        
        .recommendations-list li {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}
        
        /* Footer */
        .footer {{
            background: #2d3748;
            color: #a0aec0;
            text-align: center;
            padding: 20px;
            font-size: 12px;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            .content {{
                padding: 15px;
            }}
            .section {{
                padding: 15px;
            }}
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        /* Code styling */
        code {{
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 IMAGE METADATA FORENSICS REPORT</h1>
            <div class="subtitle">Professional Digital Forensics Analysis</div>
            <div class="file-info">
                <div>📄 File: <strong>{escape_html(filename)}</strong></div>
                <div>📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div>🖥️ Analyst: Metadata Extractor Pro v2.0</div>
            </div>
        </div>
        
        <div class="danger-bar {danger_class}">
            <div class="danger-level">💀 DANGER LEVEL: {danger_level}%</div>
            <div class="danger-text">{danger_text}</div>
            <div class="danger-message">{danger_message}</div>
        </div>
        
        <div class="content">
            <!-- Section 1: EXIF Metadata -->
            <div class="section">
                <h2>📷 1. EXIF METADATA</h2>
                <div class="camera-info">
                    <div class="camera-item">
                        <div class="camera-label">📱 Camera Make</div>
                        <div class="camera-value">{escape_html(camera_make)}</div>
                    </div>
                    <div class="camera-item">
                        <div class="camera-label">📷 Camera Model</div>
                        <div class="camera-value">{escape_html(camera_model)}</div>
                    </div>
                    <div class="camera-item">
                        <div class="camera-label">⏰ Date/Time</div>
                        <div class="camera-value">{escape_html(datetime_original)}</div>
                    </div>
                    <div class="camera-item">
                        <div class="camera-label">⚡ ISO</div>
                        <div class="camera-value">{escape_html(iso)}</div>
                    </div>
                    <div class="camera-item">
                        <div class="camera-label">🔭 Exposure</div>
                        <div class="camera-value">{escape_html(exposure_time)}</div>
                    </div>
                    <div class="camera-item">
                        <div class="camera-label">📏 Focal Length</div>
                        <div class="camera-value">{escape_html(focal_length)}</div>
                    </div>
                </div>
                <h3 style="margin: 20px 0 10px 0;">All EXIF Tags ({len(exif_data)} tags):</h3>
                <table class="exif-table">
                    <thead>
                        <tr>
                            <th class="tag-cell">Tag Name</th>
                            <th class="value-cell">Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {exif_rows}
                    </tbody>
                </table>
            </div>
            
            <!-- Section 2: GPS Location -->
            <div class="section">
                <h2>📍 2. GPS LOCATION DATA</h2>
                {gps_html}
            </div>
            
            <!-- Section 3: File Information -->
            <div class="section">
                <h2>📁 3. FILE INFORMATION</h2>
                <table class="info-table">
                    <tbody>
                        {file_info_rows}
                    </tbody>
                </table>
            </div>
            
            <!-- Section 4: Cryptographic Hashes -->
            <div class="section">
                <h2>🔐 4. CRYPTOGRAPHIC HASHES</h2>
                <table class="hash-table">
                    <tbody>
                        {hash_rows}
                    </tbody>
                </table>
                <p style="margin-top: 15px; font-size: 12px; color: #666;">
                    💡 These hashes uniquely identify this file. Use them to verify file integrity, detect duplicates, or for forensic evidence tracking.
                </p>
            </div>
            
            <!-- Section 5: Statistics -->
            <div class="section">
                <h2>📊 5. STATISTICS & METRICS</h2>
                <div class="stats-grid">
                    {stats_html}
                </div>
            </div>
            
            <!-- Section 6: Privacy Recommendations -->
            <div class="section">
                <h2>⚠️ 6. PRIVACY & SECURITY RECOMMENDATIONS</h2>
                <ul class="recommendations-list">
                    {recommendations_html}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by <strong>Image Metadata Extractor Pro v2.0</strong> | Kali Linux Forensics Suite</p>
            <p>This report contains all metadata extracted from the analyzed image file.</p>
            <p>For educational and forensic purposes only. <a href="#">Report Generated on {datetime.now().strftime('%Y-%m-%d')}</a></p>
        </div>
    </div>
</body>
</html>
    """
    
    return html

def escape_html(text):
    """Escape HTML special characters"""
    if not text:
        return "N/A"
    text = str(text)
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    return text
