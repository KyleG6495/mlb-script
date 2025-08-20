@echo off
echo 🏆 LAUNCHING ELITE MLB DASHBOARD 🏆
echo ==========================================
echo Professional-grade dashboard for tonight's 7:15 PM slate
echo ==========================================

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo 🚀 Starting Streamlit server...
streamlit run ELITE_MLB_DASHBOARD.py --server.port 8501 --server.address localhost

pause
