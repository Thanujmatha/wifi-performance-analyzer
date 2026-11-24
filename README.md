# Wi-Fi TestLab
**Automated Wi-Fi Network Performance Testing, Troubleshooting & Optimization Validation Framework**

## Features
- Wi-Fi details (SSID, signal, interface where supported), local IPv4 and gateway on Windows
- Multiple ping targets and selectable request counts
- Ping latency statistics and packet-loss measurements
- Speedtest-cli download/upload (optional; requires internet)
- Rule-based troubleshooting suggestions
- Locally saved test history and before/after comparison
- CSV exports and generated PDF report

## Run on Windows (VS Code)
1. Extract this project ZIP and open the `WiFi_TestLab_Pro` folder in VS Code.
2. In VS Code Terminal (PowerShell), run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```
   Using the venv Python directly avoids PowerShell execution-policy issues with activating the environment.
3. Open the URL printed by Streamlit, typically `http://localhost:8501`.
4. Run a test. Use a label such as `Before moving router`, then run again with `After moving router` for comparison.

## Notes
- Windows-focused Wi-Fi info extraction. Other OSes may show partial details.
- Ping targets that filter ICMP can appear unavailable even if web access works.
- Speed test can take time and may fail if blocked or offline; ping testing and reporting remain available.
- Test history is saved locally in `reports/history.json`. Avoid running tests against targets without permission.
