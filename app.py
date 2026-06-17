import os
import tempfile
from flask import Flask, request, jsonify, render_template_string
import pandas as pd

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {'csv'}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>描述性统计服务</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #333;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 30px 40px;
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 40px; }
        .upload-area {
            border: 2px dashed #cbd5e0;
            border-radius: 10px;
            padding: 50px 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: #667eea;
            background: #f7fafc;
        }
        .upload-area svg { width: 60px; height: 60px; margin-bottom: 16px; fill: #a0aec0; }
        .upload-area h3 { color: #2d3748; margin-bottom: 8px; }
        .upload-area p { color: #718096; font-size: 14px; }
        #fileInput { display: none; }
        .file-info {
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            color: #22543d;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102,126,234,0.4);
        }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .result {
            margin-top: 30px;
            display: none;
        }
        .result h2 {
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
        }
        .error {
            background: #fff5f5;
            border: 1px solid #feb2b2;
            color: #742a2a;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 14px;
        }
        th, td {
            padding: 12px 14px;
            text-align: right;
            border-bottom: 1px solid #e2e8f0;
        }
        th:first-child, td:first-child {
            text-align: left;
            font-weight: 600;
        }
        th {
            background: #f7fafc;
            color: #4a5568;
            font-weight: 600;
        }
        tbody tr:hover { background: #f7fafc; }
        .loading {
            text-align: center;
            padding: 40px;
            display: none;
        }
        .spinner {
            border: 3px solid #e2e8f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 描述性统计服务</h1>
            <p>上传 CSV 文件，获取均值、中位数、标准差、最大/最小值、四分位数</p>
        </div>
        <div class="content">
            <div class="error" id="errorBox"></div>
            <label for="fileInput">
                <div class="upload-area" id="uploadArea">
                    <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z"/><path d="M10 12h4v2h-4zM10 16h4v2h-4zM8 14h8v2H8z"/></svg>
                    <h3>点击或拖拽上传 CSV 文件</h3>
                    <p>支持 .csv 格式，最大 100MB</p>
                </div>
            </label>
            <input type="file" id="fileInput" accept=".csv">
            <div class="file-info" id="fileInfo"></div>
            <button id="analyzeBtn" disabled>开始分析</button>
            <div class="loading" id="loading"><div class="spinner"></div><p>正在分析数据...</p></div>
            <div class="result" id="result">
                <h2>📈 统计结果</h2>
                <div id="resultContent"></div>
            </div>
        </div>
    </div>
    <script>
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const fileInfo = document.getElementById('fileInfo');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const resultContent = document.getElementById('resultContent');
        const errorBox = document.getElementById('errorBox');
        let selectedFile = null;

        uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', e => {
            e.preventDefault(); uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
        });
        fileInput.addEventListener('change', e => { if (e.target.files.length) handleFile(e.target.files[0]); });

        function handleFile(file) {
            errorBox.style.display = 'none';
            if (!file.name.toLowerCase().endsWith('.csv')) {
                showError('请上传 CSV 格式的文件');
                return;
            }
            selectedFile = file;
            fileInfo.style.display = 'block';
            fileInfo.textContent = `已选择: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
            analyzeBtn.disabled = false;
        }

        function showError(msg) {
            errorBox.style.display = 'block';
            errorBox.textContent = '❌ ' + msg;
        }

        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            const formData = new FormData();
            formData.append('file', selectedFile);
            loading.style.display = 'block';
            result.style.display = 'none';
            errorBox.style.display = 'none';
            analyzeBtn.disabled = true;
            try {
                const res = await fetch('/api/statistics', { method: 'POST', body: formData });
                const data = await res.json();
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
                if (!res.ok) { showError(data.error || '分析失败'); return; }
                renderResult(data);
            } catch (err) {
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
                showError('网络错误，请重试');
            }
        });

        function renderResult(data) {
            const stats = ['count', 'mean', 'median', 'std', 'min', '25%', '50%', '75%', 'max', 'outliers_low', 'outliers_high', 'outliers_total'];
            const labels = { count: '计数', mean: '均值', median: '中位数', std: '标准差', min: '最小值', '25%': 'Q1 (25%)', '50%': 'Q2 (50%)', '75%': 'Q3 (75%)', max: '最大值', outliers_low: '异常值(<-3σ)', outliers_high: '异常值(>+3σ)', outliers_total: '异常值(合计)' };
            const numericCols = data.numeric_columns;
            let totalOutliers = 0;
            numericCols.forEach(col => {
                totalOutliers += (data.statistics[col]?.outliers_total || 0);
            });
            let html = `<p style="margin-bottom:16px;color:#718096;">共识别 <strong>${numericCols.length}</strong> 个数值列，数据集共 <strong>${data.row_count}</strong> 行`;
            if (totalOutliers > 0) {
                html += `，检测到 <strong style="color:#c53030;">${totalOutliers}</strong> 个异常值（超出均值±3σ）`;
            } else {
                html += `，<strong style="color:#2f855a;">未检测到异常值</strong>`;
            }
            html += '</p>';
            html += '<div style="overflow-x:auto;"><table><thead><tr><th>统计量</th>';
            numericCols.forEach(col => html += `<th>${escapeHtml(col)}</th>`);
            html += '</tr></thead><tbody>';
            stats.forEach(s => {
                const isOutlierRow = s.startsWith('outliers');
                html += `<tr${isOutlierRow ? ' style="background:#fff5f5;"' : ''}><td${isOutlierRow ? ' style="color:#c53030;"' : ''}>${labels[s] || s}</td>`;
                numericCols.forEach(col => {
                    const v = data.statistics[col]?.[s];
                    if (v === undefined || v === null) {
                        html += '<td>-</td>';
                    } else if (isOutlierRow) {
                        const cls = v > 0 ? ' style="color:#c53030;font-weight:600;"' : '';
                        html += `<td${cls}>${v > 0 ? v + ' ⚠️' : 0}</td>`;
                    } else {
                        html += `<td>${Number(v).toLocaleString(undefined, {maximumFractionDigits: 4})}</td>`;
                    }
                });
                html += '</tr>';
            });
            html += '</tbody></table></div>';
            resultContent.innerHTML = html;
            result.style.display = 'block';
        }

        function escapeHtml(s) {
            const div = document.createElement('div');
            div.textContent = s;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def coerce_numeric(df):
    converted = {}
    numeric_cols = []
    for col in df.columns:
        series = pd.to_numeric(df[col], errors='coerce')
        valid_count = series.notna().sum()
        if valid_count > 0 and valid_count / len(series) > 0.5:
            converted[col] = series
            numeric_cols.append(col)
        else:
            converted[col] = df[col]
    return pd.DataFrame(converted), numeric_cols


def compute_statistics(df):
    converted_df, numeric_cols = coerce_numeric(df)
    stats = {}
    for col in numeric_cols:
        series = converted_df[col].dropna()
        if len(series) == 0:
            continue
        mean = series.mean()
        std = series.std()
        if std > 0 and pd.notna(std):
            lower = mean - 3 * std
            upper = mean + 3 * std
            outliers_low = int((series < lower).sum())
            outliers_high = int((series > upper).sum())
        else:
            outliers_low = 0
            outliers_high = 0
        stats[col] = {
            'count': int(series.count()),
            'mean': float(mean),
            'median': float(series.median()),
            'std': float(std),
            'min': float(series.min()),
            '25%': float(series.quantile(0.25)),
            '50%': float(series.quantile(0.50)),
            '75%': float(series.quantile(0.75)),
            'max': float(series.max()),
            'outliers_low': outliers_low,
            'outliers_high': outliers_high,
            'outliers_total': outliers_low + outliers_high,
        }
    return stats, numeric_cols


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/statistics', methods=['POST'])
def statistics():
    if 'file' not in request.files:
        return jsonify({'error': '未找到上传的文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '仅支持 CSV 格式文件'}), 400

    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        tmp_path = tmp.name
        tmp.close()
        file.save(tmp_path)

        try:
            df = pd.read_csv(tmp_path)
        except UnicodeDecodeError:
            df = pd.read_csv(tmp_path, encoding='gbk')
        except Exception as e:
            os.unlink(tmp_path)
            return jsonify({'error': f'CSV 解析失败: {str(e)}'}), 400
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if df.empty:
            return jsonify({'error': 'CSV 文件内容为空'}), 400

        stats, numeric_cols = compute_statistics(df)

        if not numeric_cols:
            return jsonify({'error': '未检测到数值列，无法进行统计'}), 400

        return jsonify({
            'row_count': len(df),
            'column_count': len(df.columns),
            'numeric_columns': numeric_cols,
            'statistics': stats,
        })

    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
