#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
��������: �ï���	X%�ïn�c

Sn�����o�ï$��ïnOL��cW~Y
wS�ko�hGn�n��Ҧ�LcWOj��Fk�tW~Y
"""

import os
import sys
from pathlib import Path

# ѹn��
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

def fix_tack_identification():
    """�ï$��ïn�c"""
    file_path = os.path.join(project_root, 'sailing_data_processor', 'strategy', 'strategy_detector_utils.py')
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # determine_tack_type �pn�c
    old_function = """def determine_tack_type(bearing: float, wind_direction: float) -> str:
    \"\"\"
    �ï.^�$�
    
    Parameters:
    -----------
    bearing : float
        2L�Ҧ�	
    wind_direction : float
        �Ҧ��0hWfBފ	
        
    Returns:
    --------
    str
        �ï ('port'~_o'starboard')
    \"\"\"
    # �h2L�nҦ�
    # �Mnc�
    bearing_norm = bearing % 360
    wind_norm = wind_direction % 360
    
    # Gn2L�k�Wf�Lia�K�e�K�$�Y�
    # �K�Gn�M�DfBފn�	360�grc_Y��B�
    # ]n$L0180�j��tstarboard	K��LefD�
    # 180360�j��tport	K��LefD�
    wind_rel = (wind_norm - bearing_norm) % 360
    
    # 0-180�n�j��7K�� � starboard tack
    # 180-360�n�j��7K�� � port tack
    return 'starboard' if 0 <= wind_rel <= 180 else 'port'"""
    
    new_function = """def determine_tack_type(bearing: float, wind_direction: float) -> str:
    \"\"\"
    �ï.^�$�
    
    Parameters:
    -----------
    bearing : float
        2L�Ҧ�	
    wind_direction : float
        �Ҧ��0hWfBފ	
        
    Returns:
    --------
    str
        �ï ('port'~_o'starboard')
    \"\"\"
    # �h2L�nҦ�
    # �Mnc�
    bearing_norm = bearing % 360
    wind_norm = wind_direction % 360
    
    # Gn2L�k�Wf�Lia�K�e�K�$�Y�
    # Gn�MK���DfBފn�	360�grc_Y��B�
    # ]n$L0180�j��7K�� � starboard tack
    # 180360�j��7K�� � port tack
    # ;�: �o�Le���:WGn�MoGL2���:Y
    wind_rel = (bearing_norm - wind_norm) % 360
    
    # 0-180�n�j��7K�� � starboard tack
    # 180-360�n�j��7K�� � port tack
    return 'port' if 0 <= wind_rel <= 180 else 'starboard'"""
    
    # ��ɒn�
    updated_content = content.replace(old_function, new_function)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
        
    print(f"[] �ï$��ï��cW~W_: {file_path}")
    return True

if __name__ == "__main__":
    print("��������: �ï$��ïn�c���W~Y")
    fix_tack_identification()
    print("��������: �c��")
