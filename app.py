import os
import requests
import time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

def login_instagram(username, password):
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "X-CSRFToken": "missing",
        "Referer": "https://www.instagram.com/accounts/login/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.instagram.com",
    }

    try:
        r1 = session.get("https://www.instagram.com/accounts/login/", headers=headers, timeout=15)
        csrf_token = r1.cookies.get_dict().get("csrftoken", "")
        if not csrf_token:
            return {"success": False, "error": "CSRF token fetch nahi hua. Instagram server se connection issue."}

        headers["X-CSRFToken"] = csrf_token

        payload = {
            "username": username,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
            "queryParams": "{}",
            "optIntoOneTap": "false",
        }

        r2 = session.post(login_url, data=payload, headers=headers, timeout=15)

        try:
            resp = r2.json()
        except Exception:
            return {"success": False, "error": f"Instagram ne unexpected response diya: {r2.text[:200]}"}

        if resp.get("authenticated"):
            cookies = session.cookies.get_dict()
            sessionid = cookies.get("sessionid", "")
            ds_user_id = cookies.get("ds_user_id", "")
            return {
                "success": True,
                "sessionid": sessionid,
                "ds_user_id": ds_user_id,
                "username": username,
            }
        elif resp.get("two_factor_required"):
            return {"success": False, "error": "Two-Factor Authentication ON hai. Instagram app mein 2FA band karo phir try karo."}
        elif resp.get("checkpoint_url"):
            return {"success": False, "error": "Instagram ne checkpoint maanga hai. App kholkar verify karo phir retry karo."}
        elif resp.get("user") is False:
            return {"success": False, "error": "Username exist nahi karta. Check karo."}
        elif resp.get("authenticated") is False:
            return {"success": False, "error": "Password galat hai. Check karo."}
        else:
            return {"success": False, "error": f"Login failed. Response: {r2.text[:300]}"}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout ho gaya. Internet check karo aur retry karo."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error. Instagram server tak reach nahi hua."}
    except Exception as e:
        return {"success": False, "error": str(e)}


PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YKTI — Instagram Token Extractor</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #050508;
  --surface: rgba(255,255,255,0.03);
  --border: rgba(255,255,255,0.08);
  --gold: #f5c842;
  --gold2: #e8a020;
  --pink: #ff4fa3;
  --cyan: #00ffe0;
  --text: #e8e8f0;
  --muted: rgba(232,232,240,0.45);
  --success: #39ff9a;
  --error: #ff4f6a;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Syne', sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
  overflow-x: hidden;
  position: relative;
}
.bg-mesh { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.bg-mesh::before {
  content: ''; position: absolute; width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(245,200,66,0.07) 0%, transparent 70%);
  top: -200px; left: -200px;
  animation: driftA 12s ease-in-out infinite alternate;
}
.bg-mesh::after {
  content: ''; position: absolute; width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(255,79,163,0.07) 0%, transparent 70%);
  bottom: -150px; right: -150px;
  animation: driftB 15s ease-in-out infinite alternate;
}
@keyframes driftA { from{transform:translate(0,0) scale(1)} to{transform:translate(80px,60px) scale(1.15)} }
@keyframes driftB { from{transform:translate(0,0) scale(1)} to{transform:translate(-60px,-80px) scale(1.1)} }
.grid-overlay {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image: linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 60px 60px;
}
.particles { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
.particle { position: absolute; border-radius: 50%; opacity: 0; animation: float-particle linear infinite; }
@keyframes float-particle {
  0%{opacity:0;transform:translateY(100vh) scale(0)} 10%{opacity:0.6} 90%{opacity:0.3} 100%{opacity:0;transform:translateY(-100px) scale(1)}
}
.wrapper { position: relative; z-index: 10; width: 100%; max-width: 500px; }
.header { text-align: center; margin-bottom: 36px; animation: slideDown 0.8s cubic-bezier(0.16,1,0.3,1) both; }
@keyframes slideDown { from{opacity:0;transform:translateY(-30px)} to{opacity:1;transform:translateY(0)} }
.logo-badge {
  display: inline-flex; align-items: center; gap: 10px;
  background: linear-gradient(135deg, rgba(245,200,66,0.12), rgba(255,79,163,0.08));
  border: 1px solid rgba(245,200,66,0.25); border-radius: 100px; padding: 7px 18px; margin-bottom: 22px;
  animation: pulse-badge 3s ease-in-out infinite;
}
@keyframes pulse-badge {
  0%,100%{box-shadow:0 0 20px rgba(245,200,66,0.15)} 50%{box-shadow:0 0 35px rgba(245,200,66,0.35)}
}
.logo-badge span { font-size: 10px; font-weight: 700; letter-spacing: 3px; color: var(--gold); text-transform: uppercase; }
.logo-dot { width: 6px; height: 6px; background: var(--gold); border-radius: 50%; animation: blink 1.5s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(0.7)} }
.main-title { font-size: clamp(26px,6vw,42px); font-weight: 800; line-height: 1.1; letter-spacing: -1px; margin-bottom: 12px; }
.main-title .g { background: linear-gradient(135deg, var(--gold), var(--pink)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.subtitle { font-size: 13px; color: var(--muted); letter-spacing: 0.5px; }
.status-row {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin-bottom: 26px; font-size: 10px; color: var(--muted); letter-spacing: 2px; text-transform: uppercase;
  animation: slideDown 0.8s 0.15s cubic-bezier(0.16,1,0.3,1) both;
}
.status-dot { width: 7px; height: 7px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); animation: blink 2s ease-in-out infinite; }
.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 24px; padding: 34px;
  backdrop-filter: blur(20px); animation: slideUp 0.8s 0.2s cubic-bezier(0.16,1,0.3,1) both;
  position: relative; overflow: hidden;
}
@keyframes slideUp { from{opacity:0;transform:translateY(40px)} to{opacity:1;transform:translateY(0)} }
.card::before {
  content: ''; position: absolute; inset: 0; border-radius: 24px; padding: 1px;
  background: linear-gradient(135deg, rgba(245,200,66,0.18), transparent 50%, rgba(255,79,163,0.12));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
}
.field { margin-bottom: 18px; }
.field label { display: block; font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
.input-wrap { position: relative; }
.input-wrap .ico { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); font-size: 15px; pointer-events: none; }
.input-wrap input {
  width: 100%; padding: 15px 15px 15px 44px;
  background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: 12px;
  color: var(--text); font-size: 14px; font-family: 'Syne', sans-serif; outline: none; transition: all 0.3s;
}
.input-wrap input:focus { border-color: rgba(245,200,66,0.45); background: rgba(245,200,66,0.03); box-shadow: 0 0 0 3px rgba(245,200,66,0.07); }
.input-wrap input::placeholder { color: rgba(255,255,255,0.18); }
.toggle-pw {
  position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--muted); cursor: pointer; font-size: 15px; transition: color 0.2s;
}
.toggle-pw:hover { color: var(--gold); }
.warn-box {
  background: rgba(245,200,66,0.04); border: 1px solid rgba(245,200,66,0.12);
  border-radius: 10px; padding: 12px 14px; font-size: 11px; color: rgba(245,200,66,0.65); line-height: 1.7; margin-bottom: 18px;
}
.warn-box strong { color: var(--gold); }
.btn-extract {
  width: 100%; padding: 17px; border: none; border-radius: 12px;
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  color: #080600; font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase; cursor: pointer;
  position: relative; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s;
}
.btn-extract:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(245,200,66,0.4); }
.btn-extract:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-shine {
  position: absolute; inset: 0;
  background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.28) 50%, transparent 70%);
  transform: translateX(-100%);
}
.btn-extract:hover:not(:disabled) .btn-shine { animation: shine 0.55s ease forwards; }
@keyframes shine { to{transform:translateX(100%)} }
.spinner { display: none; width: 18px; height: 18px; border: 2px solid rgba(8,6,0,0.25); border-top-color: #080600; border-radius: 50%; animation: spin 0.7s linear infinite; margin: 0 auto; }
@keyframes spin { to{transform:rotate(360deg)} }
.result-panel { margin-top: 22px; border-radius: 14px; overflow: hidden; display: none; animation: fadeIn 0.45s ease; }
@keyframes fadeIn { from{opacity:0;transform:scale(0.97)} to{opacity:1;transform:scale(1)} }
.res-success { background: linear-gradient(135deg, rgba(57,255,154,0.07), rgba(0,255,224,0.04)); border: 1px solid rgba(57,255,154,0.2); padding: 22px; }
.res-error { background: linear-gradient(135deg, rgba(255,79,106,0.09), rgba(255,79,163,0.04)); border: 1px solid rgba(255,79,106,0.25); padding: 22px; }
.res-title { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; font-weight: 700; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }
.res-title.ok { color: var(--success); }
.res-title.fail { color: var(--error); }
.token-row { margin-bottom: 12px; }
.token-label { font-size: 9px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 5px; }
.token-box { display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.07); border-radius: 9px; padding: 10px 12px; }
.token-value { flex: 1; font-family: 'DM Mono', monospace; font-size: 11px; color: var(--cyan); word-break: break-all; line-height: 1.5; }
.copy-btn {
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.09); border-radius: 7px;
  color: var(--muted); cursor: pointer; padding: 5px 10px; font-size: 10px;
  font-family: 'Syne', sans-serif; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; transition: all 0.2s; white-space: nowrap;
}
.copy-btn:hover { background: rgba(245,200,66,0.12); border-color: rgba(245,200,66,0.25); color: var(--gold); }
.copy-btn.copied { background: rgba(57,255,154,0.12); border-color: rgba(57,255,154,0.25); color: var(--success); }
.error-msg { font-size: 13px; color: var(--error); line-height: 1.6; }
.footer { text-align: center; margin-top: 26px; animation: slideUp 0.8s 0.4s cubic-bezier(0.16,1,0.3,1) both; }
.footer-brand { font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); }
.footer-brand span { color: var(--gold); }
.footer-link { display: inline-flex; align-items: center; gap: 5px; margin-top: 6px; font-size: 11px; color: rgba(255,255,255,0.2); text-decoration: none; transition: color 0.2s; }
.footer-link:hover { color: var(--pink); }
@media (max-width: 540px) { .card{padding:22px 18px} .main-title{font-size:26px} }
</style>
</head>
<body>
<div class="bg-mesh"></div>
<div class="grid-overlay"></div>
<div class="particles" id="particles"></div>

<div class="wrapper">
  <div class="header">
    <div class="logo-badge">
      <div class="logo-dot"></div>
      <span>YK Tricks India</span>
      <div class="logo-dot"></div>
    </div>
    <h1 class="main-title">Instagram<br><span class="g">Token Extractor</span></h1>
    <p class="subtitle">Session ID &amp; User Token — Instant Extract</p>
  </div>

  <div class="status-row">
    <div class="status-dot"></div>
    System Online &amp; Ready
  </div>

  <div class="card">
    <div class="field">
      <label>Instagram Username</label>
      <div class="input-wrap">
        <span class="ico">👤</span>
        <input type="text" id="username" placeholder="your_username" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
      </div>
    </div>
    <div class="field">
      <label>Password</label>
      <div class="input-wrap">
        <span class="ico">🔑</span>
        <input type="password" id="password" placeholder="••••••••••••" autocomplete="current-password">
        <button class="toggle-pw" onclick="togglePw()">👁</button>
      </div>
    </div>
    <div class="warn-box">
      <strong>⚠️ Note:</strong> Data sirf Instagram ke official servers pe bheja jaata hai. Koi bhi credentials store nahi hote. Apna personal account use karo.
    </div>
    <button class="btn-extract" id="extractBtn" onclick="extractToken()">
      <span class="btn-shine"></span>
      <span id="btnText">⚡ Extract Token</span>
      <div class="spinner" id="spinner"></div>
    </button>

    <div class="result-panel" id="resultPanel">
      <div class="res-success" id="successResult" style="display:none">
        <div class="res-title ok"><span>✅</span> Token Extracted Successfully</div>
        <div class="token-row">
          <div class="token-label">Session ID (Token)</div>
          <div class="token-box">
            <div class="token-value" id="sessionidVal">—</div>
            <button class="copy-btn" onclick="copyVal('sessionidVal',this)">Copy</button>
          </div>
        </div>
        <div class="token-row">
          <div class="token-label">DS User ID</div>
          <div class="token-box">
            <div class="token-value" id="dsuseridVal">—</div>
            <button class="copy-btn" onclick="copyVal('dsuseridVal',this)">Copy</button>
          </div>
        </div>
        <div class="token-row">
          <div class="token-label">Username</div>
          <div class="token-box">
            <div class="token-value" id="usernameVal">—</div>
            <button class="copy-btn" onclick="copyVal('usernameVal',this)">Copy</button>
          </div>
        </div>
      </div>
      <div class="res-error" id="errorResult" style="display:none">
        <div class="res-title fail"><span>❌</span> Login Failed</div>
        <div class="error-msg" id="errorMsg">—</div>
      </div>
    </div>
  </div>

  <div class="footer">
    <div class="footer-brand">Powered by <span>YKTI</span> — YK Tricks India</div>
    <a class="footer-link" href="https://wa.me/918115048433" target="_blank">📲 WhatsApp: +91 8115048433</a>
  </div>
</div>

<script>
(function(){
  const c = document.getElementById('particles');
  const cols = ['#f5c842','#ff4fa3','#00ffe0','rgba(255,255,255,0.8)'];
  for(let i=0;i<28;i++){
    const p = document.createElement('div');
    p.className = 'particle';
    const s = Math.random()*2.5+1;
    p.style.cssText = `width:${s}px;height:${s}px;background:${cols[Math.floor(Math.random()*cols.length)]};left:${Math.random()*100}%;animation-duration:${Math.random()*18+8}s;animation-delay:${Math.random()*12}s;`;
    c.appendChild(p);
  }
})();

function togglePw(){
  const pw = document.getElementById('password');
  pw.type = pw.type==='password' ? 'text' : 'password';
}

async function extractToken(){
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();
  if(!username||!password){ showErr('Username aur Password dono required hain!'); return; }

  const btn = document.getElementById('extractBtn');
  btn.disabled = true;
  document.getElementById('btnText').style.display = 'none';
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('resultPanel').style.display = 'none';
  document.getElementById('successResult').style.display = 'none';
  document.getElementById('errorResult').style.display = 'none';

  try {
    const fd = new FormData();
    fd.append('username', username);
    fd.append('password', password);
    const res = await fetch('/extract', {method:'POST', body:fd});
    const data = await res.json();
    document.getElementById('resultPanel').style.display = 'block';
    if(data.success){
      document.getElementById('sessionidVal').textContent = data.sessionid || '(empty)';
      document.getElementById('dsuseridVal').textContent = data.ds_user_id || '(empty)';
      document.getElementById('usernameVal').textContent = data.username || username;
      document.getElementById('successResult').style.display = 'block';
    } else {
      showErr(data.error || 'Unknown error');
    }
  } catch(err) {
    showErr('Network error: ' + err.message);
  }

  btn.disabled = false;
  document.getElementById('btnText').style.display = 'inline';
  document.getElementById('spinner').style.display = 'none';
}

function showErr(msg){
  document.getElementById('resultPanel').style.display = 'block';
  document.getElementById('errorMsg').textContent = msg;
  document.getElementById('errorResult').style.display = 'block';
}

function copyVal(elId, btn){
  const text = document.getElementById(elId).textContent;
  navigator.clipboard.writeText(text).then(()=>{
    btn.textContent='✅ Copied!'; btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy'; btn.classList.remove('copied');}, 2000);
  }).catch(()=>{
    const el=document.getElementById(elId);
    const r=document.createRange(); r.selectNode(el);
    window.getSelection().removeAllRanges(); window.getSelection().addRange(r);
    document.execCommand('copy'); window.getSelection().removeAllRanges();
    btn.textContent='✅ Copied!'; btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy'; btn.classList.remove('copied');}, 2000);
  });
}

document.addEventListener('keydown', e=>{ if(e.key==='Enter') extractToken(); });
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE_HTML)

@app.route("/extract", methods=["POST"])
def extract():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "error": "Username aur Password dono required hain."})
    result = login_instagram(username, password)
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 YKTI Instagram Token Extractor running on http://0.0.0.0:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
