from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

BASE_URL = "https://flash-player-info-v1.vercel.app"

# واجهة الموقع (HTML/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Free Fire Player Info - @FL4SH_FF</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Tajawal', sans-serif; background-color: #0f172a; color: #f8fafc; }</style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-4xl mx-auto">
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-2xl mb-6 text-center">
            <h1 class="text-3xl font-bold text-cyan-400 mb-2">🔥 FREE FIRE PLAYER INFO API 🔥</h1>
            <p class="text-slate-400 text-sm">فحص وطلب كافه بيانات وسيرفرات لاعبين فري فاير تلقائياً</p>
        </div>

        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl mb-6">
            <form id="apiForm" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Auth UID</label>
                        <input type="text" id="authUid" value="6693700603" required class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Auth Password</label>
                        <input type="text" id="authPass" value="FLASH_TR_1OXO1UR3" required class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none">
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">اختر الـ Endpoint</label>
                        <select id="endpoint" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none" onchange="toggleStatsOptions()">
                            <option value="player-info">Player Info (معلومات اللاعب)</option>
                            <option value="bancheck">Ban Check (فحص الحظر)</option>
                            <option value="stats-info">Stats Info (إحصائيات عامة)</option>
                            <option value="STATS">Stats Mode-Wise (إحصائيات حسب النمط)</option>
                            <option value="level">Level (المستوى)</option>
                            <option value="region">Region (المنطقة/السيرفر)</option>
                            <option value="wishlist">Wishlist (قائمة الأمنيات)</option>
                            <option value="workshop-info">Workshop Info (معلومات الورشة)</option>
                            <option value="duo-info">Duo Info (معلومات الثنائي)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">نوع البحث</label>
                        <select id="queryType" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none">
                            <option value="uid">بواسطة UID (الآيدي)</option>
                            <option value="name">بواسطة Name (الاسم)</option>
                        </select>
                    </div>
                </div>

                <div id="statsOptions" class="hidden grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                    <div>
                        <label class="block text-sm font-medium text-cyan-300 mb-1">Match Mode</label>
                        <select id="matchmode" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white">
                            <option value="CAREER">CAREER</option>
                            <option value="RANKED">RANKED</option>
                            <option value="NORMAL">NORMAL</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-cyan-300 mb-1">Game Mode</label>
                        <select id="gamemode" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white">
                            <option value="BR">BR (Battle Royale)</option>
                            <option value="CS">CS (Clash Squad)</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-1">قيمة البحث (UID أو الاسم)</label>
                    <input type="text" id="queryValue" value="3419823759" required class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:border-cyan-500 focus:outline-none">
                </div>

                <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold p-3 rounded-xl transition duration-200 shadow-lg shadow-cyan-600/30">
                    🔍 جلب البيانات فوراً
                </button>
            </form>
        </div>

        <div id="resultBox" class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl hidden">
            <h2 class="text-xl font-bold text-cyan-400 mb-3">📦 الاستجابة (JSON Response):</h2>
            <pre id="jsonOutput" class="bg-slate-900 p-4 rounded-xl text-emerald-400 text-sm overflow-x-auto max-h-96 border border-slate-700"></pre>
        </div>
    </div>

    <script>
        function toggleStatsOptions() {
            const ep = document.getElementById('endpoint').value;
            const statsDiv = document.getElementById('statsOptions');
            statsDiv.classList.toggle('hidden', ep !== 'STATS');
        }

        document.getElementById('apiForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const authUid = document.getElementById('authUid').value.trim();
            const authPass = document.getElementById('authPass').value.trim();
            const endpoint = document.getElementById('endpoint').value;
            const queryType = document.getElementById('queryType').value;
            const queryValue = document.getElementById('queryValue').value.trim();

            let targetUrl = '';
            if (endpoint === 'STATS') {
                const mm = document.getElementById('matchmode').value;
                const gm = document.getElementById('gamemode').value;
                targetUrl = `/api/${authUid}/${authPass}/STATS/${mm}/${gm}?${queryType}=${encodeURIComponent(queryValue)}`;
            } else {
                targetUrl = `/api/${authUid}/${authPass}/${endpoint}?${queryType}=${encodeURIComponent(queryValue)}`;
            }

            const resultBox = document.getElementById('resultBox');
            const jsonOutput = document.getElementById('jsonOutput');
            resultBox.classList.remove('hidden');
            jsonOutput.textContent = '⏳ جاري جلب البيانات...';

            try {
                const res = await fetch(targetUrl);
                const data = await res.json();
                jsonOutput.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                jsonOutput.textContent = '❌ حدث خطأ أثناء الاتصال: ' + err.message;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# مسار STATS التكيفي
@app.route('/api/<auth_uid>/<auth_pass>/STATS/<matchmode>/<gamemode>', methods=['GET', 'POST'])
def proxy_stats(auth_uid, auth_pass, matchmode, gamemode):
    target_url = f"{BASE_URL}/{auth_uid}/{auth_pass}/STATS/{matchmode}/{gamemode}"
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            json=request.get_json(silent=True),
            timeout=30
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

# مسار كافة الـ Endpoints الأخرى
@app.route('/api/<auth_uid>/<auth_pass>/<path:endpoint>', methods=['GET', 'POST'])
def proxy_endpoint(auth_uid, auth_pass, endpoint):
    target_url = f"{BASE_URL}/{auth_uid}/{auth_pass}/{endpoint}"
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            json=request.get_json(silent=True),
            timeout=30
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
