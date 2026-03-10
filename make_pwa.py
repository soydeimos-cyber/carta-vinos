import json
import os
import zipfile
import urllib.request

def create_pwa_files(base_dir):
    # 1. Crear manifest.json
    manifest = {
      "name": "Clandestina Vinos",
      "short_name": "Clandestina",
      "start_url": "./index.html",
      "display": "standalone",
      "background_color": "#ffffff",
      "theme_color": "#2c1e16",
      "description": "Tu recomendador personal de vinos",
      "icons": [
        {
          "src": "icon-192x192.png",
          "sizes": "192x192",
          "type": "image/png"
        },
        {
          "src": "icon-512x512.png",
          "sizes": "512x512",
          "type": "image/png"
        }
      ]
    }
    
    with open(os.path.join(base_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    # 2. Add manifest.json to index.html
    index_path = os.path.join(base_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    if '<link rel="manifest"' not in html:
        html = html.replace('</head>', '    <link rel="manifest" href="manifest.json">\n</head>')
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
            
    # 3. Create a dummy SW just for installability
    sw = """
self.addEventListener('fetch', function(event) {
    // Just a dummy pass-through
});
"""
    with open(os.path.join(base_dir, "sw.js"), "w", encoding="utf-8") as f:
        f.write(sw)
        
    if '<script>if(' not in html:
        loader = """
    <script>if('serviceWorker' in navigator) { window.addEventListener('load', () => { navigator.serviceWorker.register('sw.js'); }); }</script>
</body>"""
        html = html.replace("</body>", loader)
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
            
    # 4. Generate dummy icons
    # Emulate 1x1 black pixel for icon if they dont exist
    pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    for size in ['192x192', '512x512']:
        icon_path = os.path.join(base_dir, f"icon-{size}.png")
        if not os.path.exists(icon_path):
            with open(icon_path, "wb") as f:
                f.write(pixel)
    
if __name__ == "__main__":
    import sys
    base_dir = os.path.dirname(os.path.abspath(__file__))
    create_pwa_files(base_dir)
    print("PWA files created successfully. The app is now installable as an Android App.")
