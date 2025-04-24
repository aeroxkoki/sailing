# -*- coding: utf-8 -*-
"""
ui.components.reporting.timeline.playback_panel

���ï6�(nStreamlit UI������ȒЛY�����gY
"""

import streamlit as st
from typing import Dict, Any, Optional, Callable, List, Union
import json

def playback_panel(playback_control, on_change=None, key_prefix=""):
    """
    ���ï6����h:
    
    Parameters
    ----------
    playback_control : PlaybackControl
        ���ï6��ָ���
    on_change : Optional[Callable[[Dict[str, Any]], None]], optional
        	�Bn����ï, by default None
    key_prefix : str, optional
        ���-�, by default ""
        
    Returns
    -------
    Dict[str, Any]
        	�U�_���ƣ�1
    """
    st.markdown("### ���ï6�")
    
    changes = {}
    
    # �������
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("�", key=f"{key_prefix}_rewind"):
            playback_control.stop()
            changes["action"] = "rewind"
    
    with col2:
        if playback_control._playing:
            if st.button("�", key=f"{key_prefix}_pause"):
                playback_control.pause()
                changes["action"] = "pause"
        else:
            if st.button("�", key=f"{key_prefix}_play"):
                playback_control.play()
                changes["action"] = "play"
    
    with col3:
        if st.button("�", key=f"{key_prefix}_stop"):
            playback_control.stop()
            changes["action"] = "stop"
    
    with col4:
        if st.button("�", key=f"{key_prefix}_forward"):
            # !n������x��
            changes["action"] = "forward"
    
    with col5:
        loop = st.checkbox("=", value=playback_control._options["loop"], key=f"{key_prefix}_loop")
        if loop != playback_control._options["loop"]:
            playback_control._options["loop"] = loop
            changes["loop"] = loop
    
    # ������
    current_time = st.slider(
        "�Mn",
        min_value=float(playback_control._start_time),
        max_value=float(playback_control._end_time),
        value=float(playback_control._current_time),
        key=f"{key_prefix}_time_slider"
    )
    
    if current_time != playback_control._current_time:
        playback_control.set_current_time(current_time)
        changes["current_time"] = current_time
    
    # ��
    speed_options = {
        0.1: "0.1
",
        0.25: "0.25
",
        0.5: "0.5
", 
        1.0: "1
",
        2.0: "2
",
        5.0: "5
",
        10.0: "10
"
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("��:")
    
    with col2:
        speed = st.selectbox(
            "",
            options=list(speed_options.keys()),
            format_func=lambda x: speed_options[x],
            index=list(speed_options.keys()).index(playback_control._options["playback_speed"]),
            key=f"{key_prefix}_speed"
        )
        
        if speed != playback_control._options["playback_speed"]:
            playback_control._options["playback_speed"] = speed
            changes["playback_speed"] = speed
    
    # ������
    if playback_control._keyframes:
        st.markdown("#### ������")
        keyframe_labels = [kf["label"] for kf in playback_control._keyframes]
        selected_keyframe = st.selectbox(
            "��������",
            options=range(len(keyframe_labels)),
            format_func=lambda i: keyframe_labels[i],
            key=f"{key_prefix}_keyframe"
        )
        
        if st.button("��", key=f"{key_prefix}_goto_keyframe"):
            keyframe_time = playback_control._keyframes[selected_keyframe]["time"]
            playback_control.set_current_time(keyframe_time)
            changes["current_time"] = keyframe_time
            changes["action"] = "goto_keyframe"
    
    # ��������_�
    st.markdown("#### ��������")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keyframe_label = st.text_input("���", key=f"{key_prefix}_add_keyframe_label")
    
    with col2:
        if st.button("�(Mn���", key=f"{key_prefix}_add_keyframe"):
            if keyframe_label:
                new_keyframe = playback_control.add_keyframe(
                    time=playback_control._current_time,
                    label=keyframe_label,
                    details={"added_time": playback_control._current_time}
                )
                changes["added_keyframe"] = new_keyframe
    
    # B���-�
    st.markdown("#### B���-�")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_time = st.number_input(
            "��B�",
            value=float(playback_control._start_time),
            key=f"{key_prefix}_start_time"
        )
    
    with col2:
        end_time = st.number_input(
            "B�B�",
            value=float(playback_control._end_time),
            key=f"{key_prefix}_end_time"
        )
    
    if (start_time != playback_control._start_time or 
        end_time != playback_control._end_time):
        if start_time < end_time:
            playback_control.set_time_range(start_time, end_time)
            changes["time_range"] = (start_time, end_time)
        else:
            st.error("��B�oB�B���Mk-�WfO`UD")
    
    # -���ׄ�����hn#:	
    st.markdown("#### -�")
    
    sync_options = {
        "map": "���h:",
        "timeline": "�����",
        "parameter": "��������"
    }
    
    selected_sync = st.multiselect(
        "Y����",
        options=list(sync_options.keys()),
        format_func=lambda x: sync_options[x],
        default=[],
        key=f"{key_prefix}_sync"
    )
    
    if "selected_sync" not in st.session_state:
        st.session_state["selected_sync"] = []
    
    if selected_sync != st.session_state["selected_sync"]:
        changes["sync_targets"] = selected_sync
        st.session_state["selected_sync"] = selected_sync
    
    # ����ï|s�W
    if changes and on_change:
        on_change(changes)
    
    return changes

def playback_mini_panel(playback_control, on_change=None, key_prefix=""):
    """
    ��ѯ�j���ï6����h:
    
    Parameters
    ----------
    playback_control : PlaybackControl
        ���ï6��ָ���
    on_change : Optional[Callable[[Dict[str, Any]], None]], optional
        	�Bn����ï, by default None
    key_prefix : str, optional
        ���-�, by default ""
        
    Returns
    -------
    Dict[str, Any]
        	�U�_���ƣ�1
    """
    changes = {}
    
    # ��ѯ�줢��
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 4, 1, 1])
    
    with col1:
        if st.button("�", key=f"{key_prefix}_mini_rewind"):
            playback_control.stop()
            changes["action"] = "rewind"
    
    with col2:
        if playback_control._playing:
            if st.button("�", key=f"{key_prefix}_mini_pause"):
                playback_control.pause()
                changes["action"] = "pause"
        else:
            if st.button("�", key=f"{key_prefix}_mini_play"):
                playback_control.play()
                changes["action"] = "play"
    
    with col3:
        if st.button("�", key=f"{key_prefix}_mini_stop"):
            playback_control.stop()
            changes["action"] = "stop"
    
    with col4:
        current_time = st.slider(
            "",
            min_value=float(playback_control._start_time),
            max_value=float(playback_control._end_time),
            value=float(playback_control._current_time),
            key=f"{key_prefix}_mini_time_slider",
            label_visibility="collapsed"
        )
        
        if current_time != playback_control._current_time:
            playback_control.set_current_time(current_time)
            changes["current_time"] = current_time
    
    with col5:
        if st.button("�", key=f"{key_prefix}_mini_forward"):
            # !n������x��
            changes["action"] = "forward"
    
    with col6:
        loop = st.checkbox("=", value=playback_control._options["loop"], key=f"{key_prefix}_mini_loop", label_visibility="collapsed")
        if loop != playback_control._options["loop"]:
            playback_control._options["loop"] = loop
            changes["loop"] = loop
    
    # �(nB��h:
    current_time_sec = int(playback_control._current_time)
    hours = current_time_sec // 3600
    minutes = (current_time_sec % 3600) // 60
    seconds = current_time_sec % 60
    
    time_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    st.caption(f"Time: {time_display}")
    
    # ����ï|s�W
    if changes and on_change:
        on_change(changes)
    
    return changes

def playback_settings_panel(playback_control, on_change=None, key_prefix=""):
    """
    ���ïs0-����h:
    
    Parameters
    ----------
    playback_control : PlaybackControl
        ���ï6��ָ���
    on_change : Optional[Callable[[Dict[str, Any]], None]], optional
        	�Bn����ï, by default None
    key_prefix : str, optional
        ���-�, by default ""
        
    Returns
    -------
    Dict[str, Any]
        	�U�_���ƣ�1
    """
    st.markdown("### ���ï-�")
    
    changes = {}
    
    # h:�׷��
    st.markdown("#### h:�׷��")
    
    col1, col2 = st.columns(2)
    
    with col1:
        show_timeline = st.checkbox(
            "�����h:",
            value=playback_control._options["show_timeline"],
            key=f"{key_prefix}_show_timeline"
        )
        
        if show_timeline != playback_control._options["show_timeline"]:
            playback_control._options["show_timeline"] = show_timeline
            changes["show_timeline"] = show_timeline
        
        show_time_display = st.checkbox(
            "B�h:",
            value=playback_control._options["show_time_display"],
            key=f"{key_prefix}_show_time_display"
        )
        
        if show_time_display != playback_control._options["show_time_display"]:
            playback_control._options["show_time_display"] = show_time_display
            changes["show_time_display"] = show_time_display
    
    with col2:
        show_controls = st.checkbox(
            "������h:",
            value=playback_control._options["show_controls"],
            key=f"{key_prefix}_show_controls"
        )
        
        if show_controls != playback_control._options["show_controls"]:
            playback_control._options["show_controls"] = show_controls
            changes["show_controls"] = show_controls
        
        auto_fit = st.checkbox(
            "B���n�տt",
            value=playback_control._options["auto_fit_time_range"],
            key=f"{key_prefix}_auto_fit"
        )
        
        if auto_fit != playback_control._options["auto_fit_time_range"]:
            playback_control._options["auto_fit_time_range"] = auto_fit
            changes["auto_fit_time_range"] = auto_fit
    
    # �����뵤�hMn
    st.markdown("#### ������-�")
    
    col1, col2 = st.columns(2)
    
    with col1:
        size_options = {
            "small": "",
            "medium": "-",
            "large": "'"
        }
        
        size = st.selectbox(
            "�����뵤�",
            options=list(size_options.keys()),
            format_func=lambda x: size_options[x],
            index=list(size_options.keys()).index(playback_control._options["control_size"]),
            key=f"{key_prefix}_control_size"
        )
        
        if size != playback_control._options["control_size"]:
            playback_control._options["control_size"] = size
            changes["control_size"] = size
    
    with col2:
        position_options = {
            "top": "
",
            "bottom": ""
        }
        
        position = st.selectbox(
            "������Mn",
            options=list(position_options.keys()),
            format_func=lambda x: position_options[x],
            index=list(position_options.keys()).index(playback_control._options["position"]),
            key=f"{key_prefix}_position"
        )
        
        if position != playback_control._options["position"]:
            playback_control._options["position"] = position
            changes["position"] = position
    
    # ������
    if playback_control._keyframes:
        st.markdown("#### ������")
        
        keyframe_table_data = []
        for i, kf in enumerate(playback_control._keyframes):
            keyframe_table_data.append({
                "No": i + 1,
                "���": kf["label"],
                "B�": kf["time"]
            })
        
        st.dataframe(keyframe_table_data)
        
        # ������nJd
        col1, col2 = st.columns(2)
        
        with col1:
            keyframe_to_delete = st.selectbox(
                "JdY�������",
                options=range(len(playback_control._keyframes)),
                format_func=lambda i: playback_control._keyframes[i]["label"],
                key=f"{key_prefix}_delete_keyframe_select"
            )
        
        with col2:
            if st.button("Jd", key=f"{key_prefix}_delete_keyframe_button"):
                kf_id = playback_control._keyframes[keyframe_to_delete].get("id")
                if playback_control.remove_keyframe(kf_id):
                    changes["removed_keyframe"] = keyframe_to_delete
                    st.success("�������JdW~W_")
    
    # ����ï|s�W
    if changes and on_change:
        on_change(changes)
    
    return changes
