import platform, subprocess, re, socket, statistics, time
from datetime import datetime

DEFAULT_TARGETS = ['8.8.8.8', '1.1.1.1']

def _run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors='replace')
        return p.stdout + p.stderr
    except Exception as e:
        return str(e)

def get_wifi_info():
    info = {'SSID':'Not detected', 'Wi-Fi signal':'Not detected', 'IPv4':'Not detected', 'Gateway':'Not detected', 'Interface':'Not detected'}
    if platform.system() == 'Windows':
        out = _run(['netsh','wlan','show','interfaces'])
        for key, pattern in [('SSID',r'^\s*SSID\s*:\s*(.*)$'), ('Wi-Fi signal',r'^\s*Signal\s*:\s*(.*)$'), ('Interface',r'^\s*Name\s*:\s*(.*)$')]:
            m=re.search(pattern,out,re.M|re.I)
            if m and key=='SSID' and m.group(1).strip() and m.group(1).strip()!='': info[key]=m.group(1).strip()
            elif m and key!='SSID': info[key]=m.group(1).strip()
        ipout=_run(['ipconfig'])
        # Capture IPv4 and default gateway from active/first relevant section
        ips=re.findall(r'IPv4[^:]*:\s*([\d.]+)',ipout)
        gws=re.findall(r'Default Gateway[^:]*:\s*([\d.]+)',ipout)
        if ips: info['IPv4']=ips[0]
        if gws: info['Gateway']=gws[0]
    else:
        info['IPv4']=socket.gethostbyname(socket.gethostname())
        info['Interface']=platform.platform()
    return info

def ping_target(target, samples=10):
    system=platform.system().lower()
    cmd=['ping','-n',str(samples),target] if system=='windows' else ['ping','-c',str(samples),target]
    raw=_run(cmd, timeout=max(15,samples*2+5))
    times=[float(x) for x in re.findall(r'time[=<]\s*(\d+(?:\.\d+)?)\s*ms',raw,re.I)]
    if system=='windows':
        sent_match=re.search(r'Packets\s*:\s*Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)',raw,re.I)
    else:
        sent_match=re.search(r'(\d+) packets transmitted,\s*(\d+) (?:packets )?received',raw,re.I)
    sent=int(sent_match.group(1)) if sent_match else samples
    received=int(sent_match.group(2)) if sent_match else len(times)
    if system=='windows' and sent_match: lost=int(sent_match.group(3))
    else: lost=max(0,sent-received)
    avg=statistics.mean(times) if times else None
    result={'target':target,'sent':sent,'received':received,'packet_loss_pct':round(100*lost/sent,2) if sent else None,
            'avg_latency_ms':round(avg,2) if avg is not None else None,'min_latency_ms':min(times) if times else None,
            'max_latency_ms':max(times) if times else None,'raw':raw}
    return result

def run_speed_test():
    try:
        import speedtest
        st=speedtest.Speedtest(timeout=12)
        st.get_best_server(); down=st.download()/1_000_000; up=st.upload()/1_000_000
        return {'download_mbps':round(down,2),'upload_mbps':round(up,2),'speed_status':'Success'}
    except Exception as e:
        return {'download_mbps':None,'upload_mbps':None,'speed_status':f'Unavailable: {e}'}

def diagnose(results, speed):
    tips=[]
    good=[r for r in results if r.get('avg_latency_ms') is not None]
    if not good:
        tips.append('Ping responses were not received. Check Wi-Fi connection, router, internet access, firewall, or whether the target blocks ICMP.')
    for r in results:
        if r.get('received',0)==0:
            tips.append(f'{r["target"]}: no ping replies. It may be unreachable or may block ICMP; compare with another target.')
        elif r.get('packet_loss_pct',0)>=5:
            tips.append(f'{r["target"]}: packet loss is {r["packet_loss_pct"]}%. Repeat the test; check signal strength, congestion, router and ISP.')
        elif r.get('packet_loss_pct',0)>0:
            tips.append(f'{r["target"]}: some packet loss observed ({r["packet_loss_pct"]}%). Repeat under stable conditions and inspect Wi-Fi signal.')
        if r.get('avg_latency_ms') is not None and r['avg_latency_ms']>=100:
            tips.append(f'{r["target"]}: high average latency ({r["avg_latency_ms"]} ms). Try closer router placement, less congestion, or Ethernet for comparison.')
        elif r.get('avg_latency_ms') is not None and r['avg_latency_ms']>=50:
            tips.append(f'{r["target"]}: latency is moderate ({r["avg_latency_ms"]} ms); compare with a wired test or nearer router location.')
    if speed.get('download_mbps') is None:
        tips.append('Speed test did not complete. Install speedtest-cli and ensure internet access; ping results are still useful independently.')
    else:
        if speed['download_mbps']<5: tips.append(f'Download speed is low in this test ({speed["download_mbps"]} Mbps). Check other devices, Wi-Fi band, router placement and ISP plan.')
        if speed['upload_mbps']<2: tips.append(f'Upload speed is low in this test ({speed["upload_mbps"]} Mbps). Check background uploads, signal and ISP plan.')
        tips.append('Speed-test results vary by server, time, ISP load and device; run again to establish a baseline.')
    tips.append('Change only one factor at a time (position, band, or router setting), then run another test to compare.')
    return list(dict.fromkeys(tips))

def run_suite(targets, samples):
    wifi=get_wifi_info(); ping_results=[]
    for t in targets: ping_results.append(ping_target(t.strip(),samples))
    speed=run_speed_test()
    tips=diagnose(ping_results,speed)
    return {'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'wifi':wifi,'pings':ping_results,'speed':speed,'diagnosis':tips}
