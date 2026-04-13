"""
Run this after: python -m pygbag --build --disable-sound-format-error .
It patches build/web/index.html to use the custom loading screen.
"""

with open("build/web/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# ── 1. Fix the grey page background in the Python loader block ───────────────
content = content.replace(
    'platform.document.body.style.background = "#7f7f7f"',
    'platform.document.body.style.background = "#f8f9fa"'
)

# ── 2. Hide the infobox completely (we replace it with our own UI) ───────────
content = content.replace(
    'platform.window.infobox.innerText = msg',
    'platform.window.infobox.style.display = "none"; platform.window.infobox.innerText = msg'
)
content = content.replace(
    'platform.window.infobox.innerText = f"installing {pkg}"',
    'pass  # platform.window.infobox.innerText = f"installing {pkg}"'
)

# ── 3. Replace the infobox CSS with invisible styles ────────────────────────
old_infobox_css = """        #infobox {
            position: fixed; /* center relative to viewport */
            background: green;
            color: blue;
            font-weight: bold;
            padding: 12px 24px;
 /*           display: none; */
            z-index: 999999;
        }"""

new_infobox_css = """        #infobox {
            display: none !important;
        }"""

content = content.replace(old_infobox_css, new_infobox_css)

# ── 4. Replace the body background ──────────────────────────────────────────
content = content.replace(
    "background-color:powderblue;",
    "background-color: #f8f9fa;"
)

# ── 5. Inject custom loading screen HTML + CSS just before </body> ───────────
custom_html = """
<style>
    * { box-sizing: border-box; }

    #custom-loading {
        position: fixed;
        inset: 0;
        background: #f8f9fa;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 32px;
        z-index: 99999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: opacity 0.4s ease;
    }

    #custom-loading.hidden {
        opacity: 0;
        pointer-events: none;
    }

    .cl-logo {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
    }

    .cl-logo h1 {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.5px;
        margin: 0;
    }

    .cl-logo p {
        font-size: 1rem;
        color: #64748b;
        margin: -16px 0 0 0;
    }

    .cl-progress-wrap {
        width: 320px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        align-items: center;
    }

    .cl-bar-bg {
        width: 100%;
        height: 6px;
        background: #e2e8f0;
        border-radius: 999px;
        overflow: hidden;
    }

    #cl-bar-fill {
        height: 100%;
        width: 0%;
        background: #3b82f6;
        border-radius: 999px;
        transition: width 0.3s ease;
    }

    #cl-status {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    #cl-start-wrap {
        display: none;
        flex-direction: column;
        align-items: center;
        gap: 12px;
    }

    #cl-start-btn {
        padding: 14px 40px;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.15s ease, transform 0.1s ease;
        font-family: inherit;
    }

    #cl-start-btn:hover { background: #2563eb; transform: translateY(-1px); }
    #cl-start-btn:active { transform: translateY(0px); }

    #cl-start-wrap p {
        font-size: 0.8rem;
        color: #94a3b8;
        margin: 0;
    }

    #cl-author {
        position: fixed;
        bottom: 20px;
        left: 24px;
        font-size: 0.8rem;
        color: #94a3b8;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        z-index: 99999;
    }

    #cl-author strong {
        color: #475569;
        font-weight: 600;
    }
</style>

<div id="custom-loading">
    <div class="cl-logo">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="80" height="80" rx="10" fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>
            <rect x="8" y="12" width="64" height="56" rx="6" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1.5"/>
            <g fill="#475569">
                <circle cx="18" cy="24" r="2.5"/><circle cx="26" cy="24" r="2.5"/><circle cx="34" cy="24" r="2.5"/>
                <circle cx="42" cy="24" r="2.5"/><circle cx="50" cy="24" r="2.5"/><circle cx="58" cy="24" r="2.5"/>
                <circle cx="18" cy="34" r="2.5"/><circle cx="26" cy="34" r="2.5"/><circle cx="34" cy="34" r="2.5"/>
                <circle cx="42" cy="34" r="2.5"/><circle cx="50" cy="34" r="2.5"/><circle cx="58" cy="34" r="2.5"/>
                <circle cx="18" cy="50" r="2.5"/><circle cx="26" cy="50" r="2.5"/><circle cx="34" cy="50" r="2.5"/>
                <circle cx="42" cy="50" r="2.5"/><circle cx="50" cy="50" r="2.5"/><circle cx="58" cy="50" r="2.5"/>
                <circle cx="18" cy="60" r="2.5"/><circle cx="26" cy="60" r="2.5"/><circle cx="34" cy="60" r="2.5"/>
                <circle cx="42" cy="60" r="2.5"/><circle cx="50" cy="60" r="2.5"/><circle cx="58" cy="60" r="2.5"/>
            </g>
            <line x1="26" y1="34" x2="26" y2="50" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round"/>
            <rect x="38" y="31" width="12" height="6" rx="2" fill="#d97706"/>
        </svg>
        <h1>Breadboard Simulator</h1>
        <p>Interactive circuit simulation</p>
    </div>

    <div class="cl-progress-wrap" id="cl-progress-area">
        <div class="cl-bar-bg">
            <div id="cl-bar-fill"></div>
        </div>
        <span id="cl-status">Loading Python runtime…</span>
    </div>

    <div id="cl-start-wrap">
        <button id="cl-start-btn" onclick="clStart()">Launch Simulator</button>
        <p>Click to begin</p>
    </div>
</div>

<div id="cl-author">Made by <strong>Anay Gokhale</strong></div>

<script>
    var _clProgress = 0;
    var _clInterval = null;

    // Animate the progress bar up to 90% while loading
    _clInterval = setInterval(function() {
        _clProgress += Math.random() * 3;
        if (_clProgress >= 90) {
            _clProgress = 90;
            clearInterval(_clInterval);
        }
        document.getElementById('cl-bar-fill').style.width = _clProgress + '%';
    }, 250);

    // Watch for pygbag's infobox changing to "Ready to start"
    // That's our signal that loading is complete
    var _clObserver = new MutationObserver(function() {
        var infobox = document.getElementById('infobox');
        if (infobox && infobox.innerText.indexOf('Ready') >= 0) {
            clReady();
        }
    });

    window.addEventListener('load', function() {
        var infobox = document.getElementById('infobox');
        if (infobox) {
            _clObserver.observe(infobox, { childList: true, characterData: true, subtree: true });
        }
    });

    function clReady() {
        clearInterval(_clInterval);
        _clObserver.disconnect();
        document.getElementById('cl-bar-fill').style.width = '100%';
        document.getElementById('cl-status').textContent = 'Ready!';
        setTimeout(function() {
            document.getElementById('cl-progress-area').style.display = 'none';
            document.getElementById('cl-start-wrap').style.display = 'flex';
        }, 400);
    }

    function clStart() {
        // Simulate the click that pygbag needs to unlock audio
        document.getElementById('canvas').click();
        document.getElementById('custom-loading').classList.add('hidden');
        document.getElementById('cl-author').style.display = 'none';
        setTimeout(function() {
            var el = document.getElementById('custom-loading');
            if (el) el.remove();
        }, 500);
    }
</script>
"""

content = content.replace("</body>", custom_html + "\n</body>")

with open("build/web/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Done! build/web/index.html patched successfully.")