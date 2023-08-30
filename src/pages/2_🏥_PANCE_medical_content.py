import streamlit as st
import streamlit.components.v1 as components
from streamlit_pills import pills
import numpy as np
import ktrain
from lime import lime_text
import pandas as pd
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
from utils import add_logo, hide_footer, is_Authenticated, page_config
from auth import save_prediction
import sys
import os

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
page_config()
# add_logo()
is_Authenticated()


@st.cache_resource
def load_model():
    return ktrain.load_predictor('models/pance_med')


def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


with st.sidebar:
    uploaded_file = st.file_uploader("Upload .csv, .xlsx files not exceeding 50 MB",
                                     accept_multiple_files=False,key="med_file")
    test_dataset = st.checkbox('Load test Dataset',key="avma_check")
    # if uploaded_file is not None:
    #     st.write('Modes of Operation')
    #     minimal = st.checkbox('Do you want minimal report ?')
    # display_mode = st.radio('Display mode:',
    #                         options=('Primary', 'Dark', 'Orange'))
    # if display_mode == 'Dark':
    #     dark_mode = True
    #     orange_mode = False
    # elif display_mode == 'Orange':
    #     dark_mode = False
    #     orange_mode = True
    # else:
    #     dark_mode = False
    #     orange_mode = False


def make_predictions(text):
    return pance_med_model.predict(text, return_proba=True)


def get_filesize(file):
    size_bytes = sys.getsizeof(file)
    size_mb = size_bytes / (1024**2)
    return size_mb


def validate_file(file):
    filename = file.name
    name, ext = os.path.splitext(filename)
    if ext in ('.csv', '.xlsx'):
        return ext
    else:
        return False


def generate_report(df, model, text_col="clean_text"):
    """_summary_

    Args:
        df (_type_): pandas dataframe
        model (_type_): ktrain model
        text_col (str, optional): column to be fed into the ML model. Defaults to "clean_text".
    """
    with st.spinner('Generating Report...'):
        df.dropna(subset=[text_col], inplace=True)
        pred = model.predict(df[text_col].to_numpy())
        df[f'predicted_category'] = pred
        pr = ProfileReport(df, minimal=False)

    st.header("Dataframe")
    st.dataframe(df)
    csv = convert_df(df)
    st.sidebar.download_button("Download CSV", csv, "pance_med_processed.csv", "text/csv",
                               key='download-csv')
    st_profile_report(pr)



with st.spinner('loading Model...'):
    pance_med_model = load_model()
    labels = pance_med_model.get_classes()
    explainer = lime_text.LimeTextExplainer(class_names=labels, verbose=True)

st.title("PANCE Blueprint Medical Content classifier")
hide_footer()
col1, col2 = st.columns(2)
with col1:
    with st.form(key='med_form'):
        text_input = st.text_area('Text to analyze')
        submit_button = st.form_submit_button(label='Submit')

with col2:
    pills("Available Categories", labels, index=None)

if submit_button and text_input:
    with st.spinner('calculating...'):
        p = pance_med_model.predict(text_input, return_proba=True)
        pred = labels[np.argmax(p)]
    save_prediction("pance_medical_content",text_input,pred)
    st.success(pred, icon="✅")
    st.divider()
    with st.spinner('calculating...'):
        explanation = explainer.explain_instance(
            text_input, classifier_fn=make_predictions, top_labels=1, num_samples=200)
    components.html(explanation.as_html(), height=400)

if test_dataset:
    df = pd.read_csv("src/test_df.csv")
    generate_report(df, pance_med_model)

if uploaded_file is not None:
    ext = validate_file(uploaded_file)
    if ext:
        filesize = get_filesize(uploaded_file)
        if filesize <= 10:
            if ext == '.csv':
                # time being let load csv
                df = pd.read_csv(uploaded_file)
            else:
                xl_file = pd.ExcelFile(uploaded_file)
                sheet_tuple = tuple(xl_file.sheet_names)
                sheet_name = st.sidebar.selectbox(
                    'Select the sheet', sheet_tuple)
                df = xl_file.parse(sheet_name)

            text_col = st.sidebar.selectbox('Select text Column',
                                            tuple(["<select>"]+list(df.columns)))

            if text_col != "<select>":
                # generate report
                generate_report(df, pance_med_model, text_col)
        else:
            st.error(
                f'Maximum allowed filesize is 10 MB. But received {filesize} MB')

    else:
        st.error('Kindly upload only .csv or .xlsx file')

else:
    st.subheader('Data Profiler')
    st.info(
        'Upload your data in the left sidebar, select text column to generate profiling')
