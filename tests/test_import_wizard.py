#!/usr/bin/env python3
"""
����Ȧ����nƹ�(�����

Sn�����go
1. ����nGPS����WfCSVhGPXk�X
2. ����Ȧ���ɒcf���������
3. �����P��h:
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# ������n���ǣ���ѹk��
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ui.components.forms.import_wizard import ImportWizard, EnhancedImportWizard, BatchImportUI
from sailing_data_processor.data_model.container import GPSDataContainer


def generate_sample_gps_csv(file_path, num_points=100):
    """
    ����nGPS����WfCSVk�X
    
    Parameters
    ----------
    file_path : str
        �XHnա��ѹ
    num_points : int, optional
        Y����ݤ��p, by default 100
        
    Returns
    -------
    pd.DataFrame
        W_GPS���nDataFrame
    """
    # ��Mnq�~	
    base_lat = 35.6234
    base_lon = 139.7732
    
    # B�-�
    start_time = datetime.now() - timedelta(hours=2)
    times = [start_time + timedelta(seconds=i*30) for i in range(num_points)]
    
    # Mn���n����j�M	
    lats = [base_lat + np.random.normal(0, 0.001) + i * 0.0001 for i in range(num_points)]
    lons = [base_lon + np.random.normal(0, 0.001) + i * 0.0001 for i in range(num_points)]
    
    # ����n���XM38���g����	�	
    speeds = [5 + np.sin(i/10) * 2 + np.random.normal(0, 0.5) for i in range(num_points)]
    
    # ���2L�	n�p0360�	
    courses = [(45 + np.sin(i/15) * 30 + np.random.normal(0, 5)) % 360 for i in range(num_points)]
    
    # DataFramen\
    df = pd.DataFrame({
        'timestamp': times,
        'latitude': lats,
        'longitude': lons,
        'speed': speeds,
        'course': courses,
        'elevation': [0 for _ in range(num_points)]  # wb
��
    })
    
    # CSVk�X
    df.to_csv(file_path, index=False)
    print(f"��������{file_path}k�XW~W_{num_points}ݤ��	")
    
    return df


def generate_sample_gpx(file_path, num_points=100):
    """
    ����nGPS����GPXk�X
    
    Parameters
    ----------
    file_path : str
        �XHnա��ѹ
    num_points : int, optional
        Y����ݤ��p, by default 100
        
    Returns
    -------
    pd.DataFrame
        W_GPS���nDataFrame
    """
    # DataFrame�
    df = generate_sample_gps_csv(file_path + ".temp.csv", num_points)
    
    # GPXա��n\
    gpx = ET.Element('gpx', version="1.1", 
                     attrib={'creator': 'Sailing Strategy Analyzer Test Script',
                             'xmlns': 'http://www.topografix.com/GPX/1/1'})
    
    # ����
    metadata = ET.SubElement(gpx, 'metadata')
    ET.SubElement(metadata, 'name').text = 'Sample GPX Track'
    ET.SubElement(metadata, 'desc').text = 'Generated for testing purposes'
    ET.SubElement(metadata, 'time').text = datetime.now().isoformat()
    
    # ��ïn\
    trk = ET.SubElement(gpx, 'trk')
    ET.SubElement(trk, 'name').text = 'Sample Track'
    trkseg = ET.SubElement(trk, 'trkseg')
    
    # ��ïݤ��n��
    for _, row in df.iterrows():
        trkpt = ET.SubElement(trkseg, 'trkpt', lat=str(row['latitude']), lon=str(row['longitude']))
        ET.SubElement(trkpt, 'ele').text = str(row['elevation'])
        ET.SubElement(trkpt, 'time').text = row['timestamp'].isoformat()
        
        # �5���
        extensions = ET.SubElement(trkpt, 'extensions')
        speed_element = ET.SubElement(extensions, 'speed')
        speed_element.text = str(row['speed'])
        course_element = ET.SubElement(extensions, 'course')
        course_element.text = str(row['course'])
    
    # XML���n\h�X
    tree = ET.ElementTree(gpx)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    print(f"GPX����{file_path}k�XW~W_{num_points}ݤ��	")
    
    #  Bա��nJd
    if os.path.exists(file_path + ".temp.csv"):
        os.remove(file_path + ".temp.csv")
    
    return df


def import_wizard_test_app():
    """
    ����Ȧ����nƹ�(Streamlit���
    """
    # ���-�
    st.set_page_config(
        page_title="����Ȧ����ƹ�",
        page_icon="=�",
        layout="wide",
    )
    
    # ����
    st.title("����Ȧ����ƹ�")
    
    # �������
    if 'sample_files' not in st.session_state:
        st.session_state['sample_files'] = {}
        
        # CSVա��
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            csv_path = tmp.name
            generate_sample_gps_csv(csv_path, 200)
            st.session_state['sample_files']['csv'] = csv_path
        
        # GPXա��
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gpx') as tmp:
            gpx_path = tmp.name
            generate_sample_gpx(gpx_path, 200)
            st.session_state['sample_files']['gpx'] = gpx_path
    
    # �������h:
    st.write("### �������n")
    
    csv_path = st.session_state['sample_files'].get('csv')
    gpx_path = st.session_state['sample_files'].get('gpx')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if csv_path and os.path.exists(csv_path):
            st.success(f"CSV��������W~W_: {csv_path}")
            
            # �������n�����
            try:
                sample_df = pd.read_csv(csv_path)
                st.write("CSV�����")
                st.dataframe(sample_df.head())
            except Exception as e:
                st.error(f"CSVn��k1WW~W_: {e}")
        else:
            st.error("CSV�������nk1WW~W_")
    
    with col2:
        if gpx_path and os.path.exists(gpx_path):
            st.success(f"GPX��������W~W_: {gpx_path}")
            
            # GPXա��n��h:
            try:
                with open(gpx_path, 'r') as f:
                    gpx_content = f.read(1000)  #  n1000�W`Qh:
                
                st.write("GPX�����")
                st.code(gpx_content + "...", language="xml")
            except Exception as e:
                st.error(f"GPXn��k1WW~W_: {e}")
        else:
            st.error("GPX�������nk1WW~W_")
    
    # ��g����Ȧ���ɒh:
    tab1, tab2, tab3 = st.tabs(["�,����Ȧ����", "�5����Ȧ����", "��������"])
    
    def on_import_complete(container):
        """����Ȍ�Bn����ï"""
        st.session_state["imported_data"] = container
        st.success("���n�����L��W~W_")
    
    with tab1:
        st.header("�,����Ȧ����")
        wizard = ImportWizard(
            key="test_import_wizard",
            on_import_complete=on_import_complete
        )
        wizard.render()
    
    with tab2:
        st.header("�5����Ȧ����")
        enhanced_wizard = EnhancedImportWizard(
            key="test_enhanced_wizard",
            on_import_complete=on_import_complete
        )
        enhanced_wizard.render()
    
    with tab3:
        st.header("��������")
        batch_import = BatchImportUI(
            key="test_batch_import",
            on_import_complete=on_import_complete
        )
        batch_import.render()
    
    # �����U�_���nh:
    if "imported_data" in st.session_state and st.session_state["imported_data"]:
        st.write("---")
        st.header("�����U�_���")
        
        container = st.session_state["imported_data"]
        
        if isinstance(container, GPSDataContainer):
            # ����nh:
            st.write("### ����")
            st.json(container.metadata)
            
            # ���nh:
            st.write("### ���")
            st.dataframe(container.data)
            
            # ���h:
            st.write("### Mn������")
            map_data = container.data[["latitude", "longitude"]]
            st.map(map_data)
        else:
            st.write("�����U�_���nbLgY")


if __name__ == "__main__":
    import_wizard_test_app()
