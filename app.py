from flask import Flask, request, jsonify, render_template_string
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

app = Flask(__name__)

BASE_URL = "https://flash-guild-management.vercel.app"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Free Fire Guild Management - @FL4SH_FF</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Tajawal', sans-serif; background-color: #0b0f19; color: #f8fafc; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-5xl mx-auto space-y-6">
        
        <!-- Header -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center shadow-2xl relative overflow-hidden">
            <div class="absolute -top-12 -left-12 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl"></div>
            <div class="absolute -bottom-12 -right-12 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl"></div>
            <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 mb-2">
                🔥 FREE FIRE GUILD MANAGEMENT 🔥
            </h1>
            <p class="text-slate-400 text-sm">لوحة تحكم وإدارة الكانات الجماعية للحسابات المتعددة — بواسطة @FL4SH_FF</p>
        </div>

        <!-- Form Box -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            
            <!-- Accounts Input -->
            <div>
                <div class="flex justify-between items-center mb-2">
                    <label class="block text-sm font-semibold text-slate-300">
                        📋 الحسابات (أضف حسابات كثيرة بنفس الوقت)
                    </label>
                    <span class="text-xs text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-2.5 py-1 rounded-full">
                        يدعم صيغة id:pw أو pw:id
                    </span>
                </div>
                <textarea id="accountsInput" rows="6" placeholder="ضع الحسابات هنا، كل حساب في سطر منفصل:
123456789:password123
password456:987654321
4555614971:S7LXPOMEKAEI-S1X_TEAM" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-cyan-300 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-mono"></textarea>
            </div>

            <!-- Settings Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-semibold text-slate-300 mb-1.5">🆔 Clan ID (آيدي الكلان)</label>
                    <input type="text" id="clanId" placeholder="أدخل Clan ID هنا" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none">
                </div>

                <div>
                    <label class="block text-sm font-semibold text-slate-300 mb-1.5">⚡ اختر العملية المطلوب تنفيذها</label>
                    <select id="actionType" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none">
                        <option value="request_clan">➕ Request Clan (طلب انضمام للكلان)</option>
                        <option value="quit_clan">🚪 Quit Clan (مغادرة الكلان)</option>
                        <option value="clan_info">🛡️ Clan Info (معلومات الكلان)</option>
                        <option value="token">🔑 Get Token (استخراج التوكن فقط)</option>
                    </select>
                </div>
            </div>

            <!-- Action Button -->
            <button onclick="processBatch()" class="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold p-3.5 rounded-xl transition-all shadow-lg shadow-cyan-600/20 active:scale-[0.99] flex justify-center items-center gap-2">
                <span>🚀 تنفيذ العملية على كافة الحسابات</span>
            </button>
        </div>

        <!-- Progress and Status Header -->
        <div id="statusHeader" class="hidden bg-slate-900 border border-slate-800 rounded-2xl p-4 flex justify-between items-center text-sm font-bold">
            <span class="text-slate-300">حالة التنفيذ:</span>
            <div class="flex gap-4">
                <span class="text-emerald-400">ناجح: <span id="successCount">0</span></span>
                <span class="text-rose-400">فشل: <span id="failCount">0</span></span>
                <span class="text-slate-400">الإجمالي: <span id="totalCount">0</span></span>
            </div>
        </div>

        <!-- Results Display Box -->
        <div id="resultBox" class="hidden bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
            <h2 class="text-lg font-bold text-cyan-400 border-b border-slate-800 pb-2">📦 سجل الاستجابات المباشرة:</h2>
            <div id="resultsList" class="space-y-3 max-h-[500px] overflow-y-auto pr-1"></div>
        </div>

    </div>

    <script>
        async function processBatch() {
            const rawText = document.getElementById('accountsInput').value.trim();
            const clanId = document.getElementById('clanId').value.trim();
            const action = document.getElementById('actionType').value;

            if (!rawText) {
                alert('الرجاء إدخال الحسابات أولاً!');
                return;
            }

            if (action !== 'token' && !clanId) {
                alert('الرجاء أدخل Clan ID لتنفيذ العملية!');
                return;
            }

            const lines = rawText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);

            const resultBox = document.getElementById('resultBox');
            const resultsList = document.getElementById('resultsList');
            const statusHeader = document.getElementById('statusHeader');
            
            resultBox.classList.remove('hidden');
            statusHeader.classList.remove('hidden');
            resultsList.innerHTML = '<div class="text-cyan-400 text-sm animate-pulse">⏳ جاري معالجة وتمرير الحسابات...</div>';

            let successCount = 0;
            let failCount = 0;
            document.getElementById('totalCount').textContent = lines.length;
            document.getElementById('successCount').textContent = '0';
            document.getElementById('failCount').textContent = '0';

            try {
                const response = await fetch('/api/batch_process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        accounts: lines,
                        clan_id: clanId,
                        action: action
                    })
                });

                const data = await response.json();
                resultsList.innerHTML = '';

                data.results.forEach((res, idx) => {
                    if (res.success) successCount++;
                    else failCount++;

                    const card = document.createElement('div');
                    card.className = `p-4 rounded-xl border text-xs font-mono transition-all ${
                        res.success 
                        ? 'bg-emerald-950/20 border-emerald-800/60 text-emerald-300' 
                        : 'bg-rose-950/20 border-rose-800/60 text-rose-300'
                    }`;

                    card.innerHTML = `
                        <div class="flex justify-between items-center mb-1 border-b border-slate-800/50 pb-1 font-sans">
                            <span class="font-bold">الحساب #${idx + 1} (${res.account})</span>
                            <span class="px-2 py-0.5 rounded text-[10px] ${res.success ? 'bg-emerald-900/50 text-emerald-400' : 'bg-rose-900/50 text-rose-400'}">
                                ${res.success ? 'ناجح ✅' : 'فشل ❌'}
                            </span>
                        </div>
                        <pre class="overflow-x-auto whitespace-pre-wrap mt-2">${JSON.stringify(res.data, null, 2)}</pre>
                    `;
                    resultsList.appendChild(card);
                });

                document.getElementById('successCount').textContent = successCount;
                document.getElementById('failCount').textContent = failCount;

            } catch (err) {
                resultsList.innerHTML = `<div class="text-rose-400 text-sm">❌ حدث خطأ في الاتصال بالسيرفر: ${err.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""

def parse_line(line):
    """التعرف التلقائي الذكي على تفاصيل الحساب سواء id:pw أو pw:id"""
    line = line.strip()
    if not line:
        return None, None
    
    parts = re.split(r'[:|,\s]+', line)
    if len(parts) >= 2:
        p1, p2 = parts[0].strip(), parts[1].strip()
        # إذا كان الأول يحتوي أرقام فقط فهو الـ ID
        if p1.isdigit():
            return p1, p2
        elif p2.isdigit():
            return p2, p1
        else:
            return p1, p2
    return line, None

def execute_single_account(acc_line, clan_id, action):
    uid, pwd = parse_line(acc_line)
    
    if not uid:
        return {"account": acc_line, "success": False, "data": {"error": "صيغة الحساب غير صحيحة"}}

    params = {}
    if action != 'token':
        params['clan_id'] = clan_id

    # ربط المعاملات
    if pwd:
        params['uid'] = uid
        params['password'] = pwd
    else:
        # لو دخل التوكن المباشر
        if acc_line.startswith("eyJ"):
            params['jwt'] = acc_line
        else:
            params['access_token'] = acc_line

    target_url = f"{BASE_URL}/{action}"

    try:
        resp = requests.get(target_url, params=params, timeout=25)
        res_json = resp.json()
        
        # التقاط النجاح أو الخطأ
        is_success = resp.status_code == 200 and not res_json.get("error") and res_json.get("status") != "error"
        return {
            "account": f"UID: {uid}",
            "success": is_success,
            "data": res_json
        }
    except Exception as e:
        return {
            "account": f"UID: {uid}",
            "success": False,
            "data": {"error": str(e)}
        }

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/batch_process', methods=['POST'])
def batch_process():
    req_data = request.get_json(silent=True) or {}
    accounts = req_data.get('accounts', [])
    clan_id = req_data.get('clan_id', '')
    action = req_data.get('action', 'request_clan')

    results = []
    # التنفيذ بالتوازي لخمس حسابات معاً لضمان السرعة
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(execute_single_account, acc, clan_id, action) for acc in accounts]
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True)
