"""
Run this after: python -m pygbag --build --disable-sound-format-error .
Replaces the generated build/web/index.html body with the custom loading screen,
while keeping all pygbag required scripts intact.
"""

import re

with open("build/web/index.html", "r", encoding="utf-8") as f:
    generated = f.read()

# ── Extract everything pygbag needs to keep ──────────────────────────────────

# 1. The main pygbag loader <script> tag (big one at top with python code inside)
main_script_match = re.search(r'(<script src="https://pygame-web\.github\.io[^>]+>.*?</script>)', generated, re.DOTALL)
main_script = main_script_match.group(1) if main_script_match else ""

# 2. The config <script> block
config_match = re.search(r'(<script type="application/javascript">\s*// END BLOCK.*?</script>)', generated, re.DOTALL)
config_script = config_match.group(1) if config_match else ""

# 3. browserfs script tag
browserfs_match = re.search(r'(<script src="https://pygame-web\.github\.io[^"]*browserfs[^"]*"></script>)', generated)
browserfs_script = browserfs_match.group(1) if browserfs_match else ""

# 4. The bottom custom_onload/custom_prerun script block
bottom_script_match = re.search(r'(<script type="application/javascript">\s*\n\s*globalThis\.__canvas_resized.*?</script>)', generated, re.DOTALL)
bottom_script = bottom_script_match.group(1) if bottom_script_match else ""

# Report what was found
print(f"main_script found: {bool(main_script)}")
print(f"config_script found: {bool(config_script)}")
print(f"browserfs_script found: {bool(browserfs_script)}")
print(f"bottom_script found: {bool(bottom_script)}")

# ── Build the new index.html ─────────────────────────────────────────────────

custom_html = f"""<!DOCTYPE html>
<html lang="en">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9HBFQC6S69"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-9HBFQC6S69');
</script>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Breadboard Simulator</title>

    {main_script}

    {config_script}

    {browserfs_script}

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }}

        canvas.emscripten {{
            border: 0px none;
            background-color: transparent;
            width: 100%;
            height: 100%;
            z-index: 5;
            padding: 0;
            margin: 0 auto;
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
        }}

        #loading-screen {{
            position: fixed;
            inset: 0;
            background: #f8f9fa;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 32px;
            z-index: 100;
            transition: opacity 0.4s ease;
        }}

        #loading-screen.hidden {{
            opacity: 0;
            pointer-events: none;
        }}

        .logo-area {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }}

        .board-icon {{
            width: 80px;
            height: 80px;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            letter-spacing: -0.5px;
        }}

        p.subtitle {{
            font-size: 1rem;
            color: #64748b;
            margin-top: -24px;
        }}

        .progress-container {{
            width: 320px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }}

        .progress-bar-bg {{
            width: 100%;
            height: 6px;
            background: #e2e8f0;
            border-radius: 999px;
            overflow: hidden;
        }}

        .progress-bar-fill {{
            height: 100%;
            width: 0%;
            background: #3b82f6;
            border-radius: 999px;
            transition: width 0.3s ease;
        }}

        #status-text {{
            font-size: 0.85rem;
            color: #94a3b8;
        }}

        #click-prompt {{
            display: none;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }}

        #start-btn {{
            padding: 14px 40px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s ease, transform 0.1s ease;
        }}

        #start-btn:hover {{
            background: #2563eb;
            transform: translateY(-1px);
        }}

        #start-btn:active {{
            transform: translateY(0);
        }}

        #click-prompt p {{
            font-size: 0.8rem;
            color: #94a3b8;
        }}

        #author {{
            position: fixed;
            bottom: 12px;
            left: 16px;
            font-size: 0.7rem;
            color: #94a3b8;
            letter-spacing: 0.2px;
        }}

        #copyright {{
            position: fixed;
            bottom: 8px;
            left: 12px;
            font-size: 0.65rem;
            color: rgba(255, 255, 255, 0.35);
            letter-spacing: 0.2px;
            z-index: 10;
            pointer-events: none;
            display: none;
        }}

        /* Hide pygbag's default UI elements */
        #infobox {{ display: none !important; }}
        #transfer {{ display: none !important; }}
        #pyconsole {{ display: none !important; }}
    </style>
</head>

<body>

    <div id="loading-screen">
        <div class="logo-area">
            <svg class="board-icon" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="80" height="80" rx="10" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
                <rect x="8" y="12" width="64" height="56" rx="6" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1.5" />
                <g fill="#475569">
                    <circle cx="18" cy="24" r="2.5" /><circle cx="26" cy="24" r="2.5" /><circle cx="34" cy="24" r="2.5" />
                    <circle cx="42" cy="24" r="2.5" /><circle cx="50" cy="24" r="2.5" /><circle cx="58" cy="24" r="2.5" />
                    <circle cx="18" cy="34" r="2.5" /><circle cx="26" cy="34" r="2.5" /><circle cx="34" cy="34" r="2.5" />
                    <circle cx="42" cy="34" r="2.5" /><circle cx="50" cy="34" r="2.5" /><circle cx="58" cy="34" r="2.5" />
                    <circle cx="18" cy="50" r="2.5" /><circle cx="26" cy="50" r="2.5" /><circle cx="34" cy="50" r="2.5" />
                    <circle cx="42" cy="50" r="2.5" /><circle cx="50" cy="50" r="2.5" /><circle cx="58" cy="50" r="2.5" />
                    <circle cx="18" cy="60" r="2.5" /><circle cx="26" cy="60" r="2.5" /><circle cx="34" cy="60" r="2.5" />
                    <circle cx="42" cy="60" r="2.5" /><circle cx="50" cy="60" r="2.5" /><circle cx="58" cy="60" r="2.5" />
                </g>
                <line x1="26" y1="34" x2="26" y2="50" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" />
                <rect x="38" y="31" width="12" height="6" rx="2" fill="#d97706" />
            </svg>

            <h1>Breadboard Simulator</h1>
            <p class="subtitle">Interactive circuit simulation</p>
        </div>

        <div class="progress-container" id="progress-area">
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progress-fill"></div>
            </div>
            <span id="status-text">Loading Python runtime…</span>
        </div>

        <div id="click-prompt">
            <button id="start-btn" onclick="startApp()">Launch Simulator</button>
            <p>Click to begin</p>
        </div>

        <div id="author">© 2026 Anay Gokhale | Licensed under Apache 2.0</div>
    </div>

    <div id="copyright">© 2026 Anay Gokhale | Licensed under Apache 2.0</div>

    <!-- pygbag required elements (hidden, but must exist in DOM) -->
    <canvas class="emscripten" id="canvas" width="1px" height="1px"
        oncontextmenu="event.preventDefault()" tabindex=1></canvas>
    <canvas class="emscripten" id="canvas3d" width="1280px" height="720px"
        oncontextmenu="event.preventDefault()" tabindex=1 hidden></canvas>
    <div id="infobox">Loading...</div>
    <div id="transfer" hidden></div>
    <div id="pyconsole"><div id="terminal" tabIndex=1 align="left"></div></div>
    <div id="html"></div>
    <div id="info"></div>
    <div id="crt"></div>
    <div id="box" hidden></div>
    <div id="dlg" hidden>
        <input type="file" id="dlg_multifile" multiple accept="image/*">
    </div>
    <div id="system" hidden></div>

    <script>
        var _progress = 0;
        var _interval = null;

        function setStatus(text) {{
            var el = document.getElementById('status-text');
            if (el) el.textContent = text;
        }}

        function setProgress(pct) {{
            _progress = pct;
            var fill = document.getElementById('progress-fill');
            if (fill) fill.style.width = pct + '%';
            if (pct >= 100) showStartButton();
        }}

        function showStartButton() {{
            document.getElementById('progress-area').style.display = 'none';
            document.getElementById('click-prompt').style.display = 'flex';
        }}

        function startApp() {{
            var c = document.getElementById('canvas');
            if (c) c.click();
            document.getElementById('loading-screen').classList.add('hidden');
            document.getElementById('copyright').style.display = 'block';
            setTimeout(function () {{
                var s = document.getElementById('loading-screen');
                if (s) s.remove();
            }}, 500);
        }}

        // Fake progress bar while loading
        _interval = setInterval(function () {{
            _progress += Math.random() * 3;
            if (_progress >= 90) {{ _progress = 90; clearInterval(_interval); }}
            var fill = document.getElementById('progress-fill');
            if (fill) fill.style.width = _progress + '%';
        }}, 250);

        // Watch pygbag's infobox for "Ready" signal
        window.addEventListener('load', function () {{
            var infobox = document.getElementById('infobox');
            if (infobox) {{
                var observer = new MutationObserver(function () {{
                    if (infobox.innerText.indexOf('Ready') >= 0) {{
                        clearInterval(_interval);
                        observer.disconnect();
                        setProgress(100);
                        setStatus('Ready!');
                    }}
                }});
                observer.observe(infobox, {{ childList: true, characterData: true, subtree: true }});
            }}
        }});

        function show_infobox() {{}}
    </script>

    {bottom_script}

</body>
</html>"""

with open("build/web/index.html", "w", encoding="utf-8") as f:
    f.write(custom_html)

print("Done! build/web/index.html patched successfully.")