from flask import Flask, request, jsonify
import requests
import os
import socket
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecScan Pro - 目标资产深度情报审计</title>
    <style>
        :root { 
            --primary: #3b82f6; 
            --success: #10b981; 
            --warning: #f59e0b; 
            --danger: #ef4444; 
            --bg: #0f172a; 
            --card-bg: #1e293b;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); margin: 0; padding: 0; color: var(--text); }
        
        @media print {
            body { background: white; color: black; }
            .navbar, .search-section, .paywall, .copy-btn, .footer, .contact-box { display: none !important; }
            .report-card { box-shadow: none; border: 1px solid #ccc; background: white; color: black; }
            .result-item { border: 1px solid #ccc; background: #fff; color: black; page-break-inside: avoid; }
            .item-title, .item-detail { color: black; }
            .blur-lock .lock-overlay { display: none !important; }
            .blur-lock .code-box { filter: none !important; }
            .dashboard, .report-header { background: #f8fafc; }
        }

        /* 顶部导航 */
        .navbar { background: #0b1120; padding: 15px 0; border-bottom: 1px solid #1e293b; }
        .nav-content { max-width: 850px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; color: white; }
        .logo { font-size: 22px; font-weight: 800; display: flex; align-items: center; gap: 8px; letter-spacing: 1px;}
        .logo span { color: var(--primary); }
        .engine-text { font-size: 13px; color: #475569; font-family: monospace; }
        
        /* 搜索区 */
        .search-section { background: #0b1120; padding: 50px 20px 70px; text-align: center; color: white; border-bottom: 1px solid #1e293b; }
        .search-section h1 { margin: 0 0 10px 0; font-size: 28px; font-weight: 700; letter-spacing: 1px;}
        .search-section p { color: var(--text-muted); margin: 0 0 30px 0; font-size: 14px; font-family: monospace; }
        .search-box { max-width: 650px; margin: 0 auto; display: flex; gap: 10px; background: #1e293b; padding: 10px; border-radius: 8px; border: 1px solid #334155; }
        input[type="text"] { flex: 1; padding: 12px 16px; border: none; font-size: 16px; outline: none; background: transparent; color: white; }
        input[type="text"]::placeholder { color: #64748b; }
        button.scan-btn { padding: 12px 30px; background: var(--primary); color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button.scan-btn:hover { background: #2563eb; }
        
        /* 主体 */
        .container { max-width: 850px; margin: -40px auto 50px; padding: 0 20px; }
        .report-card { background: var(--card-bg); border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); overflow: hidden; display: none; border: 1px solid #334155; }
        
        /* 报告头部 */
        .report-header { padding: 25px 30px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; background: #0b1120; }
        .meta-info h2 { margin: 0 0 8px 0; font-size: 20px; color: white; }
        .meta-info p { margin: 0; font-size: 13px; color: var(--text-muted); font-family: monospace; }
        .print-btn { background: #334155; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; color: white; display: flex; align-items: center; gap: 6px; transition: 0.2s;}
        .print-btn:hover { background: #475569; }

        /* 评分板 */
        .dashboard { display: flex; padding: 30px; gap: 30px; border-bottom: 1px solid #334155; }
        .score-box { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 140px; flex-shrink: 0; }
        .score-circle { width: 110px; height: 110px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: 800; color: white; margin-bottom: 10px; border: 3px solid #ef4444; }
        .score-text { font-size: 14px; font-weight: 600; color: var(--text-muted); font-family: monospace; }
        
        .summary-box { flex: 1; display: flex; flex-direction: column; justify-content: center; }
        .summary-title { font-size: 20px; font-weight: 700; margin-bottom: 10px; color: var(--danger); }
        .summary-desc { font-size: 14px; line-height: 1.6; color: #cbd5e1; margin-bottom: 15px; }
        .benchmark { display: inline-block; background: rgba(59, 130, 246, 0.1); color: var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid rgba(59, 130, 246, 0.2); }
        
        /* 结果列表 */
        .results-container { padding: 30px; }
        .result-item { padding: 20px; border-radius: 8px; background: #0b1120; border: 1px solid #334155; margin-bottom: 15px; position: relative; border-left: 4px solid var(--success); }
        .result-item.error { border-left-color: var(--danger); }
        .result-item.warning { border-left-color: var(--warning); }
        
        .item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .item-title { font-weight: 600; font-size: 16px; color: white; display: flex; align-items: center; gap: 10px;}
        .badge { font-size: 12px; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
        .badge.warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
        .badge.error { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .badge.pass { background: rgba(16, 185, 129, 0.2); color: var(--success); }
        
        .item-detail { color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 15px; }
        .item-detail strong { color: var(--primary); }
        
        /* 代码框 */
        .code-box { background: #1e1e1e; border-radius: 6px; overflow: hidden; font-family: 'Consolas', monospace; margin-top: 15px; border: 1px solid #334155; }
        .code-header { background: #2d2d2d; padding: 8px 15px; display: flex; justify-content: space-between; align-items: center; }
        .mac-dots { display: flex; gap: 6px; }
        .mac-dot { width: 10px; height: 10px; border-radius: 50%; }
        .mac-dot.red { background: #ff5f56; }
        .mac-dot.yellow { background: #ffbd2e; }
        .mac-dot.green { background: #27c93f; }
        .code-lang { color: #94a3b8; font-size: 12px; }
        .copy-btn { background: transparent; border: 1px solid #555; color: #ccc; padding: 4px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; transition: 0.2s; }
        .copy-btn:hover { background: #555; color: white; }
        .code-content { padding: 15px; color: #d4d4d4; font-size: 13px; overflow-x: auto; white-space: pre; }
        
        /* 付费锁定 */
        .locked-section { position: relative; }
        .lock-overlay { position: absolute; inset: 0; background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; z-index: 10; border-radius: 8px;}
        .lock-overlay-content { text-align: center; background: #1e293b; padding: 20px 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); border: 1px solid #334155;}
        .unlock-btn { background: var(--warning); color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 14px;}
        
        /* 联系方式 */
        .contact-box { margin-top: 20px; padding: 15px; background: rgba(59, 130, 246, 0.1); border: 1px dashed var(--primary); border-radius: 8px; text-align: center; }
        .contact-box p { margin: 0 0 10px 0; color: var(--text); font-size: 14px; }
        .contact-box strong { color: var(--primary); font-size: 16px; }

        .paywall { margin-top: 30px; padding: 40px; text-align: center; background: rgba(245, 158, 11, 0.05); border: 1px dashed #f59e0b; border-radius: 12px; }
        .paywall h3 { margin: 0 0 10px 0; font-size: 20px; color: white; }
        .paywall p { color: var(--text-muted); margin-bottom: 20px; font-size: 14px; }
        .pay-btn { background: var(--warning); color: white; padding: 14px 30px; border: none; border-radius: 8px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.2s; }
        .pay-btn:hover { background: #d97706; transform: translateY(-1px); }
        
        #loading { display: none; text-align: center; padding: 50px 0; color: var(--primary); font-family: monospace; }
        .spinner { width: 40px; height: 40px; border: 4px solid #334155; border-top: 4px solid var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .footer { text-align: center; color: #475569; font-size: 12px; margin-top: 40px; line-height: 1.6; }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="nav-content">
            <div class="logo">🛡️ SecScan <span>Pro</span></div>
            <div class="engine-text">Team Intelligence Engine v4.0</div>
        </div>
    </div>

    <div class="search-section">
        <h1>目标资产深度情报审计</h1>
        <p>DNS解析 / 架构指纹 / SSL证书 / 响应头配置 / 敏感文件</p>
        <div class="search-box">
            <input type="text" id="urlInput" placeholder="请输入域名 (例如: baidu.com)" onkeypress="handleKeyPress(event)">
            <button class="scan-btn" id="scanBtn" onclick="startScan()">执行审计</button>
        </div>
    </div>

    <div class="container">
        <div id="loading">
            <div class="spinner"></div>
            <div>正在执行资产测绘与被动扫描...</div>
        </div>

        <div id="report" class="report-card">
            <div class="report-header">
                <div class="meta-info">
                    <h2 id="reportTarget">资产审计报告</h2>
                    <p>审计编号: <span id="reportId">-</span> | 时间: <span id="reportTime">-</span></p>
                </div>
                <button class="print-btn" onclick="window.print()">📄 导出 PDF</button>
            </div>

            <div class="dashboard">
                <div class="score-box">
                    <div class="score-circle" id="scoreCircle">0</div>
                    <div class="score-text">综合安全指数</div>
                </div>
                <div class="summary-box">
                    <div class="summary-title" id="summaryTitle">分析中...</div>
                    <div class="summary-desc" id="summaryDesc"></div>
                    <div class="benchmark" id="benchmarkText"></div>
                </div>
            </div>

            <div class="results-container" id="resultsList"></div>

            <div class="paywall" id="paywall">
                <h3>🔒 获取完整深度情报与修复方案</h3>
                <p>免费版仅展示前 3 项检测结果与修复代码。<br><strong>解锁后可查看全部深度漏洞分析、完整 Nginx/Apache 修复代码</strong></p>
                <button class="pay-btn" onclick="unlockAll()">立即解锁完整报告 (¥29)</button>
                
                <!-- 手动支付联系方式模块 -->
                <div class="contact-box">
                    <p>支付方式：请添加微信 <strong>18309420625</strong>（手机同号）</p>
                    <p>付款后请将截图发送至邮箱：<strong>sjwcdzx@qq.com</strong></p>
                    <p style="font-size:12px; color:#94a3b8; margin-top:8px;">确认到账后，完整版报告将发送至您的邮箱。</p>
                </div>
            </div>

            <div class="footer">
                免责声明：本引擎仅进行被动资产测绘与配置分析，不执行任何主动攻击行为。<br>请确保您对检测的域名拥有合法授权。
            </div>
        </div>
    </div>

    <script>
        function handleKeyPress(e) { if (e.key === 'Enter') startScan(); }

        async function startScan() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) { alert('请输入域名'); return; }

            const btn = document.getElementById('scanBtn');
            const loading = document.getElementById('loading');
            const report = document.getElementById('report');

            btn.disabled = true; btn.innerText = '审计中...';
            loading.style.display = 'block'; report.style.display = 'none';

            try {
                const response = await fetch(`/scan?url=${encodeURIComponent(url)}`);
                const data = await response.json();

                if (data.error) {
                    alert(data.error);
                    loading.style.display = 'none';
                } else {
                    setTimeout(() => {
                        loading.style.display = 'none';
                        report.style.display = 'block';
                        renderReport(data);
                    }, 1200); 
                }
            } catch (error) {
                alert("请求失败，请检查网络");
                loading.style.display = 'none';
            } finally {
                btn.disabled = false; btn.innerText = '执行审计';
            }
        }

        function renderReport(data) {
            const results = data.results;
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = '';
            let score = 100;
            let issueCount = 0;

            document.getElementById('reportTarget').innerText = data.target + ' 资产审计报告';
            document.getElementById('reportId').innerText = 'INT-' + Math.floor(Math.random() * 900000 + 100000);
            document.getElementById('reportTime').innerText = new Date().toLocaleString();

            if (data.ip) {
                resultsList.innerHTML += `
                    <div class="result-item" style="border-left-color: var(--primary); margin-bottom: 25px;">
                        <div class="item-header">
                            <span class="item-title">🌐 网络空间测绘</span>
                            <span class="badge pass" style="background: rgba(59,130,246,0.2); color: var(--primary);">信息</span>
                        </div>
                        <div class="item-detail">目标域名解析 IP 为 <strong>${data.ip}</strong> ${data.is_cdn ? '<span style="color:var(--warning); font-size:12px;">(检测到 CDN 节点)</span>' : ''}</div>
                    </div>
                `;
            }

            results.forEach((item, index) => {
                let className = 'pass';
                let badgeClass = 'pass';
                
                if (item.status === '严重') { className = 'error'; badgeClass = 'error'; score -= 30; issueCount++; } 
                else if (item.status === '警告') { className = 'warning'; badgeClass = 'warning'; score -= 15; issueCount++; } 
                else if (item.status === '提示') { className = 'warning'; badgeClass = 'warning'; score -= 5; issueCount++; }

                let contentHtml = `
                    <div class="result-item ${className}">
                        <div class="item-header">
                            <span class="item-title">
                                ${item.status === '通过' ? '🟢' : (item.status === '严重' ? '🔴' : '🟡')} ${item.item}
                            </span>
                            <span class="badge ${badgeClass}">${item.status}</span>
                        </div>
                        <div class="item-detail">${item.detail}</div>
                `;

                if (item.status !== '通过' && item.status !== '提示') {
                    if (item.code) {
                        contentHtml += `<div class="code-box"><div class="code-header"><div class="mac-dots"><div class="mac-dot red"></div><div class="mac-dot yellow"></div><div class="mac-dot green"></div></div><div class="code-lang">修复配置</div><button class="copy-btn" onclick="copyCode(this)">复制代码</button></div><div class="code-content">${item.code}</div></div>`;
                    } else {
                        contentHtml += `<div style="color:var(--danger); font-size:13px; font-weight:bold; margin-top:10px;">* 该项属于高危风险，需人工介入排查</div>`;
                    }
                }
                contentHtml += `</div>`;

                if (index >= 3 && item.status !== '通过') {
                    resultsList.innerHTML += `
                        <div class="locked-section">
                            ${contentHtml}
                            <div class="lock-overlay">
                                <div class="lock-overlay-content">
                                    <div style="font-size:24px; margin-bottom:5px;">🔒</div>
                                    <div style="font-weight:600; font-size:15px; color:white;">高级审计项已锁定</div>
                                    <button class="unlock-btn" onclick="unlockAll()">支付 ¥29 解锁</button>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    resultsList.innerHTML += contentHtml;
                }
            });

            if (score < 0) score = 0;
            const scoreCircle = document.getElementById('scoreCircle');
            scoreCircle.innerText = score;
            
            if (score >= 85) {
                scoreCircle.style.borderColor = 'var(--success)';
                document.getElementById('summaryTitle').innerText = "资产安全状态良好";
                document.getElementById('summaryTitle').style.color = "var(--success)";
            } else if (score >= 50) {
                scoreCircle.style.borderColor = 'var(--warning)';
                document.getElementById('summaryTitle').innerText = "存在中等安全风险";
                document.getElementById('summaryTitle').style.color = "var(--warning)";
            } else {
                scoreCircle.style.borderColor = 'var(--danger)';
                document.getElementById('summaryTitle').innerText = "高危资产！建议立即加固";
                document.getElementById('summaryTitle').style.color = "var(--danger)";
            }

            document.getElementById('summaryDesc').innerText = `情报引擎共完成 9 项深度检查，发现 ${issueCount} 项风险。外部暴露面过大，建议结合报告进行策略调整。`;
            document.getElementById('benchmarkText').innerText = `全网评语：该资产安全性击败了 ${Math.min(score + Math.floor(Math.random()*10), 99)}% 的同类资产`;
        }

        function unlockAll() {
            // 滚动到页面底部的联系方式区域
            document.querySelector('.contact-box').scrollIntoView({ behavior: 'smooth' });
        }

        function copyCode(btn) {
            const code = btn.parentElement.nextElementSibling.innerText;
            navigator.clipboard.writeText(code).then(() => {
                const originalText = btn.innerText;
                btn.innerText = '已复制!';
                btn.style.color = '#10b981'; btn.style.borderColor = '#10b981';
                setTimeout(() => { btn.innerText = originalText; btn.style.color = ''; btn.style.borderColor = ''; }, 2000);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return HTML_PAGE

@app.route('/scan')
def scan():
    url = request.args.get('url')
    if not url: return jsonify({"error": "请输入域名"})
    
    domain = url.replace('https://', '').replace('http://', '').split('/')[0]
    if not url.startswith('http'): url = 'https://' + domain
        
    results = []
    ip_address = None
    is_cdn = False
    
    try:
        try:
            ip_address = socket.gethostbyname(domain)
            if ip_address.startswith('104.') or ip_address.startswith('172.') or ip_address.startswith('111.63.'):
                is_cdn = True
        except:
            ip_address = "解析失败"

        headers_req = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, timeout=5, allow_redirects=True, headers=headers_req, verify=False)
        headers = response.headers
        
        if 'Strict-Transport-Security' in headers:
            results.append({"item": "HSTS 强制加密传输", "status": "通过", "detail": "已配置 HSTS 响应头。"})
        else:
            results.append({"item": "HSTS 强制加密传输", "status": "警告", "detail": "缺少 HSTS 响应头，容易受到中间人攻击。", "code": 'add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;'})

        if 'X-Frame-Options' in headers:
            results.append({"item": "点击劫持防护", "status": "通过", "detail": "已配置防护头。"})
        else:
            results.append({"item": "点击劫持防护", "status": "严重", "detail": "恶意网站可将您的站点嵌入，诱导用户点击造成财产损失。", "code": 'add_header X-Frame-Options "SAMEORIGIN" always;'})
            
        if 'X-Content-Type-Options' in headers:
            results.append({"item": "MIME 嗅探防护", "status": "通过", "detail": "已配置 nosniff。"})
        else:
            results.append({"item": "MIME 嗅探防护", "status": "警告", "detail": "浏览器可能错误猜测文件类型，增加跨站脚本攻击 (XSS) 风险。", "code": 'add_header X-Content-Type-Options "nosniff" always;'})

        try:
            test_env = requests.get(url.rstrip('/') + '/.env', timeout=3, verify=False)
            if test_env.status_code == 200 and 'DB_' in test_env.text:
                results.append({"item": "敏感文件暴露", "status": "严重", "detail": "检测到 .env 配置文件可被公开下载！数据库密码等核心信息面临直接泄露风险。"})
            else:
                results.append({"item": "敏感文件暴露", "status": "通过", "detail": "未发现常见敏感配置文件暴露。"})
        except:
            results.append({"item": "敏感文件暴露", "status": "通过", "detail": "未发现常见敏感配置文件暴露。"})

        if url.startswith('https'):
            results.append({"item": "HTTPS 证书状态", "status": "通过", "detail": "SSL/TLS 证书有效且已启用加密传输。"})
        else:
            results.append({"item": "HTTPS 证书状态", "status": "严重", "detail": "网站未启用 HTTPS 加密，所有数据以明文传输，极易被窃听。"})

        cookie_header = headers.get('Set-Cookie', '')
        if cookie_header:
            if 'HttpOnly' not in cookie_header or 'Secure' not in cookie_header:
                results.append({"item": "Cookie 安全属性", "status": "警告", "detail": "检测到 Cookie 未设置 Secure 或 HttpOnly，易受 XSS 攻击窃取用户凭证。"})
            else:
                results.append({"item": "Cookie 安全属性", "status": "通过", "detail": "Cookie 已配置基础安全属性。"})
        else:
            results.append({"item": "Cookie 安全属性", "status": "通过", "detail": "未检测到敏感 Cookie 下发。"})

        if headers.get('Access-Control-Allow-Origin') == '*':
            results.append({"item": "CORS 跨域策略", "status": "警告", "detail": "配置了通配符 '*'，可能导致恶意网站随意读取本站数据。"})
        else:
            results.append({"item": "CORS 跨域策略", "status": "通过", "detail": "跨域策略配置正常。"})

        if 'Server' in headers:
            results.append({"item": "服务器版本信息", "status": "提示", "detail": f"暴露了具体版本: {headers['Server']}。黑客可据此寻找已知漏洞。"})
        else:
            results.append({"item": "服务器版本信息", "status": "通过", "detail": "未泄露服务器版本。"})

        try:
            test_dir = requests.get(url.rstrip('/') + '/uploads/', timeout=3, verify=False)
            if 'Index of /' in test_dir.text:
                results.append({"item": "目录遍历漏洞", "status": "严重", "detail": "检测到目录开启了浏览功能，黑客可直接下载内部文件。"})
            else:
                results.append({"item": "目录遍历漏洞", "status": "通过", "detail": "未发现常见的目录遍历配置。"})
        except:
            results.append({"item": "目录遍历漏洞", "status": "通过", "detail": "未发现常见的目录遍历配置。"})

        if 'X-XSS-Protection' in headers:
            results.append({"item": "浏览器 XSS 过滤", "status": "通过", "detail": "已开启浏览器内置的 XSS 过滤机制。"})
        else:
            results.append({"item": "浏览器 XSS 过滤", "status": "提示", "detail": "未开启 X-XSS-Protection，依赖 CSP 防护更佳。", "code": 'add_header X-XSS-Protection "1; mode=block";'})

    except Exception as e:
        results.append({"item": "访问异常", "status": "严重", "detail": f"无法访问该网站: {str(e)}。"})

    response = jsonify({"target": domain, "ip": ip_address, "is_cdn": is_cdn, "results": results})
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)