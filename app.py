import streamlit as st, pandas as pd, json, os
from datetime import datetime
from network_tests import DEFAULT_TARGETS, get_wifi_info, run_suite
from src.report_utils import create_pdf

st.set_page_config(page_title='Wi-Fi TestLab',page_icon='📶',layout='wide')
BASE=os.path.dirname(__file__); REPORT_DIR=os.path.join(BASE,'reports'); os.makedirs(REPORT_DIR,exist_ok=True)
HISTORY=os.path.join(REPORT_DIR,'history.json')

def load_history():
    if os.path.exists(HISTORY):
        try:
            with open(HISTORY,encoding='utf-8') as f: return json.load(f)
        except Exception: return []
    return []
def save_history(items):
    with open(HISTORY,'w',encoding='utf-8') as f: json.dump(items,f,indent=2)

def flatten(run):
    rows=[]
    for p in run['pings']:
        rows.append({'timestamp':run['timestamp'],'SSID':run['wifi'].get('SSID'),'IPv4':run['wifi'].get('IPv4'),'gateway':run['wifi'].get('Gateway'),
          'target':p['target'],'sent':p['sent'],'received':p['received'],'packet_loss_pct':p['packet_loss_pct'],'avg_latency_ms':p['avg_latency_ms'],
          'min_latency_ms':p['min_latency_ms'],'max_latency_ms':p['max_latency_ms'],'download_mbps':run['speed'].get('download_mbps'),
          'upload_mbps':run['speed'].get('upload_mbps'),'speed_status':run['speed'].get('speed_status'),'label':run.get('label','')})
    return rows

st.title('📶 Wi-Fi TestLab')
st.caption('Automated Wi-Fi Network Performance Testing, Troubleshooting & Optimization Validation Framework')
st.write('Run repeatable connectivity and performance tests, review measured results, and export a report for before/after validation.')
with st.sidebar:
    st.header('Test settings')
    target_text=st.text_input('Ping targets (comma-separated)',','.join(DEFAULT_TARGETS))
    samples=st.slider('Ping samples per target',3,30,10)
    label=st.text_input('Test label (e.g. Before router repositioning)','Baseline')
    st.caption('Targets that block ICMP may show no replies even when internet browsing works.')
    run_btn=st.button('▶ Run network tests',type='primary',use_container_width=True)

if 'latest' not in st.session_state: st.session_state.latest=None
if run_btn:
    targets=[x.strip() for x in target_text.split(',') if x.strip()]
    if not targets: st.error('Enter at least one ping target.')
    else:
        with st.spinner('Testing connection… Ping and speed tests may take a little while.'):
            run=run_suite(targets,samples); run['label']=label
        st.session_state.latest=run
        hist=load_history(); hist.append(run); save_history(hist)
        st.success('Test finished. Results are saved locally in the project reports folder.')

latest=st.session_state.latest
if latest:
    st.subheader('Wi-Fi / network details')
    st.json(latest['wifi'])
    st.subheader('Latest results')
    speed=latest['speed']
    cols=st.columns(4)
    all_avgs=[p['avg_latency_ms'] for p in latest['pings'] if p['avg_latency_ms'] is not None]
    all_losses=[p['packet_loss_pct'] for p in latest['pings'] if p['packet_loss_pct'] is not None]
    cols[0].metric('Average latency (targets)',f'{round(sum(all_avgs)/len(all_avgs),2)} ms' if all_avgs else 'N/A')
    cols[1].metric('Avg. packet loss',f'{round(sum(all_losses)/len(all_losses),2)}%' if all_losses else 'N/A')
    cols[2].metric('Download',f'{speed["download_mbps"]} Mbps' if speed['download_mbps'] is not None else 'N/A')
    cols[3].metric('Upload',f'{speed["upload_mbps"]} Mbps' if speed['upload_mbps'] is not None else 'N/A')
    st.dataframe(pd.DataFrame([{k:v for k,v in p.items() if k!='raw'} for p in latest['pings']]),use_container_width=True)
    st.subheader('Troubleshooting suggestions')
    for i,tip in enumerate(latest['diagnosis'],1): st.markdown(f'{i}. {tip}')
    st.caption(f'Test run: {latest["timestamp"]} | Label: {latest.get("label","-")}')
    rows=flatten(latest); df=pd.DataFrame(rows)
    st.download_button('⬇ Download latest results (CSV)',df.to_csv(index=False).encode('utf-8'),file_name='wifi_test_results.csv',mime='text/csv')
    pdf=create_pdf(latest)
    st.download_button('⬇ Download latest report (PDF)',pdf,file_name='wifi_test_report.pdf',mime='application/pdf')

st.subheader('Test history / before-after comparison')
history=load_history()
if history:
    hist_rows=[]
    for r in history: hist_rows.extend(flatten(r))
    hist_df=pd.DataFrame(hist_rows)
    st.dataframe(hist_df,use_container_width=True)
    st.download_button('⬇ Download all test history (CSV)',hist_df.to_csv(index=False).encode('utf-8'),file_name='wifi_test_history.csv',mime='text/csv')
    labels=[r.get('label',r['timestamp']) for r in history]
    if len(history)>=2:
        chosen=st.selectbox('Select two test runs to compare',options=list(range(len(history))),format_func=lambda i:f'{i+1}: {labels[i]} — {history[i]["timestamp"]}')
        other=st.selectbox('Compare against',options=[i for i in range(len(history)) if i!=chosen],format_func=lambda i:f'{i+1}: {labels[i]} — {history[i]["timestamp"]}')
        def summary(run):
            lat=[p['avg_latency_ms'] for p in run['pings'] if p['avg_latency_ms'] is not None]
            loss=[p['packet_loss_pct'] for p in run['pings'] if p['packet_loss_pct'] is not None]
            return {'Average latency (ms)':sum(lat)/len(lat) if lat else None,'Average packet loss (%)':sum(loss)/len(loss) if loss else None,
                    'Download (Mbps)':run['speed'].get('download_mbps'),'Upload (Mbps)':run['speed'].get('upload_mbps')}
        a,b=summary(history[chosen]),summary(history[other])
        comp=pd.DataFrame({'Selected run':a,'Comparison run':b})
        st.write('Comparison (measurement values; lower latency/loss and higher speed are generally preferable):')
        st.dataframe(comp,use_container_width=True)
else: st.info('No saved test history yet. Run a test to populate history and compare later.')

st.caption('Note: speed test depends on the speedtest-cli package and internet access. Ping results may be affected by ICMP filtering. This tool is a small validation aid, not a certified Wi-Fi analyzer.')
