echo PORT $PORT
streamlit run --server.enableCORS false --server.port $PORT src/App.py
