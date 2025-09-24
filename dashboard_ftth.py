import streamlit as st
import time
import threading
from datetime import datetime
from icmplib import ping
import pandas as pd
import plotly.express as px

# Configurações
HOST_IPS = ['192.168.1.1', '192.168.1.100', '8.8.8.8']  # Edite: IPs do roteador, ONT, Google DNS (teste externo)
PING_COUNT = 4  # Pings por teste
UPDATE_INTERVAL = 5  # Segundos entre atualizações
HOSTNAMES = {ip: f'Equip_{i+1}' for i, ip in enumerate(HOST_IPS)}  # Nomes amigáveis (edite)

# Armazenamento em memória (histórico de 100 medições)
@st.cache_data(ttl=UPDATE_INTERVAL)
def get_status():
    data = []
    for ip in HOST_IPS:
        try:
            result = ping(ip, count=PING_COUNT, timeout=2, privileged=False)
            status = 'Online' if result.is_alive else 'Offline'
            avg_rtt = result.avg_rtt if result.is_alive else float('inf')
            data.append({'IP': ip, 'Hostname': HOSTNAMES.get(ip, ip), 'Status': status, 
                         'Latência (ms)': round(avg_rtt, 2), 'Timestamp': datetime.now().strftime('%H:%M:%S')})
        except Exception as e:
            data.append({'IP': ip, 'Hostname': HOSTNAMES.get(ip, ip), 'Status': 'Erro', 
                         'Latência (ms)': 'N/A', 'Timestamp': datetime.now().strftime('%H:%M:%S')})
    return pd.DataFrame(data)

# Função para auto-atualização
def auto_update():
    while True:
        time.sleep(UPDATE_INTERVAL)
        st.rerun()

# Dashboard
st.set_page_config(page_title='Dashboard FTTH Monitor', layout='wide')
st.title('🛡️ Dashboard de Monitoramento Rede FTTH')

# Sidebar: Configs
st.sidebar.header('Configurações')
new_ips = st.sidebar.text_area('IPs a Monitorar (um por linha)', value='\n'.join(HOST_IPS), height=100)
if st.sidebar.button('Atualizar IPs'):
    global HOST_IPS
    HOST_IPS = [ip.strip() for ip in new_ips.split('\n') if ip.strip()]
    st.sidebar.success('IPs atualizados! Recarregue a página.')

# Auto-update toggle
if st.sidebar.checkbox('Auto-atualizar a cada 5s', value=True):
    threading.Thread(target=auto_update, daemon=True).start()

# Métricas principais
df = get_status()
col1, col2, col3 = st.columns(3)
online_count = len(df[df['Status'] == 'Online'])
offline_count = len(df[df['Status'] == 'Offline'])
st.metric('Equipamentos Online', online_count)
st.metric('Offline/Erros', offline_count)
st.metric('Latência Média', f"{df['Latência (ms)'].mean():.1f} ms" if not df['Latência (ms)'].isna().all() else 'N/A')

# Tabela de Status
st.subheader('Status dos Equipamentos')
st.dataframe(df.style.apply(lambda row: ['background-color: lightgreen' if row['Status'] == 'Online' else 'background-color: lightcoral' if 'Offline' in row['Status'] else 'background-color: lightyellow'], axis=1))

# Gráfico de Latência (histórico simulado; expanda com lista global para real)
if len(df) > 1:
    fig = px.line(df, x='Timestamp', y='Latência (ms)', color='Status', title='Latência Histórica (Última Verificação)')
    st.plotly_chart(fig, use_container_width=True)

# Alertas
offline_eq = df[df['Status'] != 'Online']
if not offline_eq.empty:
    st.error(f"🚨 {len(offline_eq)} equipamentos offline: {', '.join(offline_eq['Hostname'].tolist())}")

# Rodapé
st.info(f"Atualizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Rede Intranet FTTH | Acesse via Wi-Fi local.")
