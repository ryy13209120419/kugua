#!/usr/bin/env python3
"""TradeLens Pro v3.2 - Binance/OKX | AI分析 | 多设备同步"""
import os
import sys
import socket
import webbrowser
import hashlib
import hmac
import base64
import time
import json
import ssl
from urllib.parse import urlencode
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

dir_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(dir_path)

DATA_FILE = os.path.join(dir_path, 'trades_data.json')
CONFIG_FILE = os.path.join(dir_path, 'server_config.json')

# ===== Server-side config (proxy etc.) =====
def load_server_config():
    """Load server config from file, return dict"""
    default = {'proxy': ''}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                default.update(cfg)
        except:
            pass
    return default

def save_server_config(cfg):
    """Save server config to file"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_server_proxy():
    """Get the proxy URL saved on server side"""
    cfg = load_server_config()
    return cfg.get('proxy', '') or None

try:
    from flask import Flask, send_from_directory, request, jsonify
    from flask_cors import CORS
    import requests as req_lib
except ImportError:
    print("Installing required packages...")
    os.system(f'{sys.executable} -m pip install -r requirements.txt')
    from flask import Flask, send_from_directory, request, jsonify
    from flask_cors import CORS
    import requests as req_lib

app = Flask(__name__, static_folder=dir_path, static_url_path='')
CORS(app)

# ===== File Download Route =====
@app.route('/download/<path:filename>')
def download_file(filename):
    from flask import send_file, abort
    file_path = os.path.join(dir_path, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path, mimetype='application/zip', as_attachment=True, download_name=filename)
    abort(404)

# ===== HTTP Client with retry & proxy support =====
def create_http_session(proxy_url=None):
    """Create a requests session with retry, proxy support, and DNS fallback"""
    session = req_lib.Session()
    retry = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.trust_env = True
    # Set proxy if provided
    if proxy_url:
        proxy_url = proxy_url.strip()
        if not proxy_url.startswith("http://") and not proxy_url.startswith("socks"):
            proxy_url = "http://" + proxy_url
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
    return session

def safe_request(method, url, headers=None, json_data=None, params=None, proxy=None):
    """Safe HTTP request with proxy support and proper error handling"""
    session = create_http_session(proxy)
    try:
        if method.upper() == 'GET':
            resp = session.get(url, headers=headers, params=params, timeout=(10, 15))
        else:
            resp = session.post(url, headers=headers, json=json_data, timeout=(10, 15))
        return resp
    except req_lib.exceptions.ConnectionError as e:
        err_str = str(e)
        if 'NameResolutionError' in err_str or 'getaddrinfo' in err_str:
            raise Exception(f"DNS解析失败，无法连接服务器。请检查网络或配置代理：\n{err_str[:200]}")
        elif 'Connection refused' in err_str:
            raise Exception(f"连接被拒绝，请确认API地址是否正确：\n{err_str[:200]}")
        else:
            raise Exception(f"网络连接失败：\n{err_str[:200]}")
    except req_lib.exceptions.Timeout:
        raise Exception("请求超时，请检查网络连接或稍后重试")
    except req_lib.exceptions.SSLError as e:
        raise Exception(f"SSL证书验证失败：{str(e)[:200]}")
    except Exception as e:
        raise Exception(f"请求异常：{str(e)[:200]}")

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory(dir_path, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(dir_path, path)):
        return send_from_directory(dir_path, path)
    return send_from_directory(dir_path, 'index.html')

# API Proxy
@app.route('/api/proxy', methods=['GET', 'POST', 'OPTIONS'])
def api_proxy():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    target = request.args.get('url', '')
    if not target:
        return jsonify({'error': 'Missing url parameter'}), 400
    try:
        if request.method == 'POST':
            resp = safe_request('POST', target, headers={'User-Agent': 'TradeLensPro/1.0'}, json_data=request.get_json(silent=True) or {})
        else:
            resp = safe_request('GET', target, headers={'User-Agent': 'TradeLensPro/1.0'})
        return jsonify({'status': resp.status_code, 'data': resp.json() if resp.text else {}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Chat API
@app.route('/api/ai/chat', methods=['POST', 'OPTIONS'])
def ai_chat():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json(force=True)
    api_type = data.get('api_type', 'deepseek')
    api_key = data.get('api_key', '')
    model = data.get('model', '')
    custom_url = data.get('custom_url', '')
    messages = data.get('messages', [])

    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    if api_type == 'deepseek':
        url = 'https://api.deepseek.com/chat/completions'
        model = model or 'deepseek-chat'
    elif api_type == 'openai':
        url = 'https://api.openai.com/v1/chat/completions'
        model = model or 'gpt-4o-mini'
    elif api_type == 'custom':
        url = custom_url
        model = model or 'gpt-3.5-turbo'
    else:
        return jsonify({'error': 'Unsupported API type'}), 400

    try:
        ai_headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        proxy = get_server_proxy()
        resp = safe_request('POST', url, headers=ai_headers, json_data={
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }, proxy=proxy)
        result = resp.json()
        return jsonify({'status': 'success' if 'choices' in result else 'error', 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== Server Proxy Settings API =====
@app.route('/api/settings/proxy', methods=['GET', 'POST', 'OPTIONS'])
def settings_proxy():
    """Save/load proxy settings on the server side.
    This is crucial: the proxy runs on the SERVER machine (where start_server.py runs),
    NOT on the client browser. So mobile users' proxy config is saved server-side."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    if request.method == 'GET':
        cfg = load_server_config()
        return jsonify({'status': 'success', 'proxy': cfg.get('proxy', '')})
    # POST - save proxy
    data = request.get_json(force=True)
    proxy = data.get('proxy', '')
    cfg = load_server_config()
    cfg['proxy'] = proxy
    save_server_config(cfg)
    return jsonify({'status': 'success', 'message': f'代理已保存到服务器端: {proxy or "(直连)"}'})

# ===== Diagnostics API =====
@app.route('/api/diagnostics', methods=['GET'])
def diagnostics():
    """服务器诊断 - 显示代理状态、网络连接情况"""
    import platform
    cfg = load_server_config()
    proxy_url = cfg.get('proxy', '')
    common_ports = [7890, 10809, 10808, 1080, 8080, 3128, 8888, 10800, 7891, 9090]
    found_proxies = []
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                found_proxies.append(f'http://127.0.0.1:{port}')
            sock.close()
        except: pass
    proxy_reachable = False
    if proxy_url:
        try:
            p = proxy_url.replace('http://','').replace('https://','').split(':')
            host, port = p[0], int(p[1]) if len(p)>1 else 80
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0: proxy_reachable = True
            sock.close()
        except: pass
    domains = {'Binance':'api.binance.com','Binance-F':'fapi.binance.com','OKX':'www.okx.com','DeepSeek':'api.deepseek.com'}
    dns_results = {}
    for name, domain in domains.items():
        try:
            ips = socket.getaddrinfo(domain, 443)
            dns_results[name] = {'resolved':True, 'ips':list(set(a[4][0] for a in ips))}
        except Exception as e:
            dns_results[name] = {'resolved':False, 'error':str(e)}
    return jsonify({
        'status':'success','server_version':'3.2',
        'platform':platform.platform(),'python_version':sys.version,
        'proxy':{'configured':bool(proxy_url),'url':proxy_url or '(未配置)','reachable':proxy_reachable,'auto_detected':found_proxies,'hint':'设置页填写代理地址(http://127.0.0.1:7890)'},
        'dns_check':dns_results
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok', 'message': 'TradeLens Pro Server Running', 'version': '3.0'})


@app.route('/api/exchange/dns-check', methods=['GET'])
def exchange_dns_check():
    results = []
    for ep in [{'n':'Binance现货','d':'api.binance.com'},{'n':'Binance合约','d':'fapi.binance.com'},{'n':'OKX','d':'www.okx.com'}]:
        dns_ok=False;ips=[]
        try:
            a=socket.getaddrinfo(ep['d'],443)
            ips=list(set(x[4][0] for x in a));dns_ok=True
        except:pass
        tcp_ok=False
        if dns_ok:
            try:
                s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(3)
                s.connect((ips[0],443));s.close();tcp_ok=True
            except:pass
        results.append({'name':ep['n'],'domain':ep['d'],'dns_ok':dns_ok,'ips':ips[:3],'tcp_ok':tcp_ok})
    return jsonify({'status':'success','results':results})

@app.route('/api/exchange/auto-detect-proxy', methods=['GET'])
def auto_detect_proxy():
    ports=[(7890,'Clash'),(10809,'V2Ray'),(1080,'SS'),(8080,'HTTP'),(7891,'Clash2'),(10808,'V2Ray-S')]
    found=[]
    for p,n in ports:
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(0.2)
            if s.connect_ex(('127.0.0.1',p))==0:found.append({'url':f'http://127.0.0.1:{p}','port':p,'name':n})
            s.close()
        except:pass
    return jsonify({'status':'success','found':found,'count':len(found)})

# ===== Data Persistence (sync across devices) =====
@app.route('/api/data/save', methods=['POST', 'OPTIONS'])
def data_save():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        data = request.get_json(force=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/data/load', methods=['GET'])
def data_load():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({'status': 'success', 'data': data})
        return jsonify({'status': 'success', 'data': {'trades': [], 'settings': {}}})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== Exchange API Helpers =====
def binance_auth(api_key, api_secret, method, endpoint, params=None):
    """Sign a Binance API request"""
    timestamp = int(time.time() * 1000)
    query_str = urlencode(params or {})
    query_str += f"&timestamp={timestamp}&recvWindow=5000"
    signature = hmac.new(api_secret.encode(), query_str.encode(), hashlib.sha256).hexdigest()
    query_str += f"&signature={signature}"
    url = f"https://api.binance.com{endpoint}?{query_str}"
    headers = {'X-MBX-APIKEY': api_key, 'User-Agent': 'TradeLensPro/1.0'}
    return url, headers

def okx_auth(api_key, api_secret, passphrase, method, endpoint, params=None):
    """Sign an OKX API request"""
    timestamp = str(int(time.time()))
    body = json.dumps(params) if params else ''
    msg = timestamp + method.upper() + endpoint + body
    signature = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    url = f"https://www.okx.com{endpoint}"
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    return url, headers


@app.route('/api/exchange/proxy-test', methods=['GET'])
def exchange_proxy_test():
    """检测代理是否真正工作，显示出口 IP"""
    proxy = get_server_proxy()
    result = {'proxy_configured': bool(proxy), 'proxy_url': proxy or '(无)'}
    if not proxy:
        return jsonify({'status': 'error', 'error': '未配置代理', **result})
    import requests as req_lib
    session = create_http_session(proxy)
    # 尝试多个服务检测出口IP
    ip = '检测失败'
    ip_services = [
        'https://httpbin.org/ip',
        'https://api.ipify.org?format=json',
        'https://ip-api.com/json/'
    ]
    for svc in ip_services:
        try:
            r = session.get(svc, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if 'origin' in data:
                    ip = data['origin'].split(',')[0].strip()
                elif 'ip' in data:
                    ip = data['ip']
                elif 'query' in data:
                    ip = data['query']
                break
        except:
            continue
    result['exit_ip'] = ip
    
    # 用 ip-api.com 查 IP 地理位置
    location = '未知'
    try:
        r = session.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if r.status_code == 200:
            d = r.json()
            location = f"{d.get('country','')} {d.get('city','')} {d.get('isp','')}"
    except:
        pass
    result['location'] = location.strip() or '未知'
    
    # 检查是否是中国IP
    is_china = any(k in location for k in ['中国','China','电信','联通','移动','深圳','上海','北京'])
    result['in_china'] = is_china
    
    # 测试 Binance ping
    binance_ok = False
    try:
        r = session.get('https://api.binance.com/api/v3/ping', timeout=8)
        binance_ok = (r.status_code == 200)
        result['binance_status'] = r.status_code
    except Exception as e:
        result['binance_status'] = str(e)
    result['binance_reachable'] = binance_ok
    
    if is_china:
        result['advice'] = '代理在运行，但流量仍在国内（Clash 可能是 Rule 或 Direct 模式）。请打开 Clash 面板，切换到 Global 模式，并确认选中一个延迟正常的海外节点。'
    elif binance_ok:
        result['advice'] = '代理正常，出口IP在海外，Binance可连接！'
    else:
        result['advice'] = '出口IP在海外但Binance仍拒绝，可能该IP段也被Binance限制，换节点试试。'
    
    return jsonify({'status': 'success', **result})

@app.route('/api/exchange/test', methods=['POST', 'OPTIONS'])
def exchange_test():
    """测试交易所 API 连接"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json(force=True)
    ex_type = data.get('type', 'binance')
    api_key = data.get('apiKey', '')
    api_secret = data.get('apiSecret', '')
    passphrase = data.get('passphrase', '')
    proxy = get_server_proxy() or data.get('proxy', '') or None

    if not api_key or not api_secret:
        return jsonify({'status': 'error', 'error': 'Missing API Key or Secret'}), 400

    try:
        if ex_type == 'binance':
            url, headers = binance_auth(api_key, api_secret, 'GET', '/fapi/v1/account')
            resp = safe_request('GET', url, headers=headers, proxy=proxy)
            if resp.status_code == 200:
                info = resp.json()
                bal = float(info.get('totalWalletBalance',0))
                return jsonify({'status':'success','accountName':f'Binance合约(余额:)'})
            url, headers = binance_auth(api_key, api_secret, 'GET', '/api/v3/account')
            resp = safe_request('GET', url, headers=headers, proxy=proxy)
            if resp.status_code == 200:
                return jsonify({'status':'success','accountName':'Binance现货'})
            err = '连接失败'
            try:
                err_data = resp.json()
                err = err_data.get('msg', str(err_data)[:200])
                if 'restricted location' in err or resp.status_code == 451:
                    proxy_ip = '未知'
                    try:
                        ps = create_http_session(proxy)
                        pr = ps.get('https://httpbin.org/ip', timeout=5)
                        if pr.status_code == 200:
                            proxy_ip = pr.json().get('origin', '未知').split(',')[0].strip()
                    except: pass
                    err += '\nBinance限制了中国IP访问。当前出口IP: ' + proxy_ip
                    err += '\n请用代理诊断检查，确认Clash在Global模式并使用海外节点。'
            except:
                err = resp.text[:200] if resp.text else '连接失败'
            return jsonify({'status':'error','error':f'Binance: {err}'}), 400

        elif ex_type == 'okx':
            url, headers = okx_auth(api_key, api_secret, passphrase, 'GET', '/api/v5/account/config')
            resp = safe_request('GET', url, headers=headers, proxy=proxy)
            if resp.status_code == 200:
                data_r = resp.json()
                if data_r.get('code') == '0':
                    level = data_r.get('data', [{}])[0].get('level', '')
                    return jsonify({'status': 'success', 'accountName': f'OKX (级别:{level})'})
                return jsonify({'status': 'error', 'error': f"OKX: {data_r.get('msg', '未知')}"}), 400
            return jsonify({'status': 'error', 'error': f'HTTP {resp.status_code}'}), 400

        return jsonify({'status': 'error', 'error': f'不支持的交易所: {ex_type}'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# Exchange Sync - 同步历史交易
@app.route('/api/exchange/sync', methods=['POST', 'OPTIONS'])
def exchange_sync():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json(force=True)
    ex_type = data.get('type', 'binance')
    api_key = data.get('apiKey', '')
    api_secret = data.get('apiSecret', '')
    passphrase = data.get('passphrase', '')
    last_sync = data.get('lastSyncTime', '')
    # Use server-side proxy as primary; frontend proxy as fallback
    proxy = get_server_proxy() or data.get('proxy', '') or None

    if not api_key or not api_secret:
        return jsonify({'status': 'error', 'error': 'Missing API Key or Secret'}), 400

    try:
        trades = []

        if ex_type == 'binance':
            url, headers = binance_auth(api_key, api_secret, 'GET', '/fapi/v1/income', {'limit': 100, 'incomeType': 'REALIZED_PNL'})
            resp = safe_request('GET', url, headers=headers, proxy=proxy)
            if resp.status_code == 200:
                items = resp.json()
                t_map = {}
                tu, th = binance_auth(api_key, api_secret, 'GET', '/fapi/v1/userTrades', {'limit': 100})
                tr = safe_request('GET', tu, headers=th, proxy=proxy)
                if tr.status_code == 200:
                    for ft in tr.json():
                        oid = ft.get('orderId', 0)
                        if oid not in t_map: t_map[oid] = []
                        t_map[oid].append(ft)
                for item in items:
                    pnl = float(item.get('income', 0))
                    if abs(pnl) < 0.01: continue
                    symbol = item.get('symbol', '').upper()
                    income_ts = item.get('time', 0)
                    ct = datetime.fromtimestamp(income_ts / 1000).strftime('%Y-%m-%d %H:%M:%S') if income_ts else ''
                    exit_price = 0; qty = 0
                    for oid, fills in t_map.items():
                        for f in fills:
                            rp = float(f.get('realizedPnl', 0))
                            if abs(rp - pnl) < 0.1:
                                exit_price = float(f.get('price', 0))
                                qty = abs(float(f.get('qty', 0)))
                                break
                        if exit_price > 0: break
                    trades.append({
                        'symbol': symbol,
                        'direction': 'Long' if pnl>=0 else 'Short',
                        'entryPrice': exit_price,
                        'exitPrice': exit_price,
                        'qty': qty or 0.01,
                        'pnl': round(pnl, 2),
                        'exchange': 'Binance',
                        'product': '永续合约',
                        'openDate': '',
                        'closeDate': ct,
                        'notes': f"自动同步 #{item.get('tradeId','')}",
                        'reviewStatus': 'pending',
                        'signals': []
                    })

        elif ex_type == 'okx':
            # OKX: 获取成交历史
            params = {'limit': '100', 'instType': 'SWAP'}
            url, headers = okx_auth(api_key, api_secret, passphrase, 'GET', '/api/v5/trade/fills-history', params)
            resp = safe_request('GET', url, headers=headers, proxy=proxy)
            if resp.status_code == 200:
                data_r = resp.json()
                if data_r.get('code') == '0':
                    for item in data_r.get('data', []):
                        pnl_val = float(item.get('pnl', 0))
                        if abs(pnl_val) < 0.001:
                            continue
                        side = item.get('side', 'buy')
                        direction = 'Short' if side in ('sell', 'short') else 'Long'
                        ts_str = item.get('fillTime', '0')
                        close_time = ''
                        try:
                            close_time = datetime.fromtimestamp(int(ts_str) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                        trades.append({
                            'symbol': item.get('instId', '').upper().replace('-SWAP', '').replace('-USDT', 'USDT'),
                            'direction': direction,
                            'entryPrice': float(item.get('px', 0)),
                            'exitPrice': float(item.get('px', 0)),
                            'qty': abs(float(item.get('sz', 0))),
                            'pnl': round(pnl_val, 2),
                            'exchange': 'OKX',
                            'product': '永续合约',
                            'openDate': '',
                            'closeDate': close_time,
                            'notes': f"自动同步 #{item.get('tradeId', '')}",
                            'signals': []
                        })

        return jsonify({'status': 'success', 'trades': trades, 'count': len(trades)})

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    port = 5000
    hostname = socket.gethostname()
    local_ip = '127.0.0.1'
    try:
        # Try to get the actual local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = '127.0.0.1'

    print(f"\n{'='*50}")
    print(f"  TradeLens Pro Server v3.2")
    print(f"{'='*50}")
    print(f"  📱 使用方式")
    print(f"  {'='*30}")
    print(f"  路径一：本机使用")
    print(f"    Local:    http://localhost:{port}")
    print(f"    或直接双击打开 index.html（纯网页模式）")
    print(f"  {'='*30}")
    print(f"  路径二：手机/其他设备访问（需同一WiFi）")
    print(f"    Network:  http://{local_ip}:{port}")
    print(f"    手机浏览器打开上方地址，添加到主屏幕")
    print(f"  {'='*30}")
    print(f"  🔌 支持交易所: Binance / OKX")
    print(f"  🤖 AI 分析: DeepSeek / OpenAI")
    print(f"{'='*50}")
    print(f"  Press Ctrl+C to stop\n")
    
    try:
        webbrowser.open(f'http://localhost:{port}')
    except:
        pass
    
    app.run(host='0.0.0.0', port=port, debug=False)

