#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ÑÃÁ¹¯ê×È: ¿Ã¯¹âÛ	X%í¸Ã¯nîc

Sn¹¯ê×Èo¿Ã¯$ší¸Ã¯nOL’îcW~Y
wS„ko¨hGn¹nøşÒ¦—LcWOj‹ˆFk¿tW~Y
"""

import os
import sys
from pathlib import Path

# Ñ¹nı 
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

def fix_tack_identification():
    """¿Ã¯$ší¸Ã¯nîc"""
    file_path = os.path.join(project_root, 'sailing_data_processor', 'strategy', 'strategy_detector_utils.py')
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # determine_tack_type ¢pnîc
    old_function = """def determine_tack_type(bearing: float, wind_direction: float) -> str:
    \"\"\"
    ¿Ã¯.^’$š
    
    Parameters:
    -----------
    bearing : float
        2L¹Ò¦¦	
    wind_direction : float
        ¨Ò¦¦’0hWfBŞŠ	
        
    Returns:
    --------
    str
        ¿Ã¯ ('port'~_o'starboard')
    \"\"\"
    # ¨h2L¹nÒ¦î
    # ¹Mnc
    bearing_norm = bearing % 360
    wind_norm = wind_direction % 360
    
    # Gn2L¹kşWf¨Lia‰K‰e‹K’$šY‹
    # ¨K‰Gn¹M’DfBŞŠnî	360¦grc_YŠ’B
    # ]n$L0180¦j‰ótstarboard	K‰¨LefD‹
    # 180360¦j‰ætport	K‰¨LefD‹
    wind_rel = (wind_norm - bearing_norm) % 360
    
    # 0-180¦n“j‰ó7K‰¨ ’ starboard tack
    # 180-360¦n“j‰æ7K‰¨ ’ port tack
    return 'starboard' if 0 <= wind_rel <= 180 else 'port'"""
    
    new_function = """def determine_tack_type(bearing: float, wind_direction: float) -> str:
    \"\"\"
    ¿Ã¯.^’$š
    
    Parameters:
    -----------
    bearing : float
        2L¹Ò¦¦	
    wind_direction : float
        ¨Ò¦¦’0hWfBŞŠ	
        
    Returns:
    --------
    str
        ¿Ã¯ ('port'~_o'starboard')
    \"\"\"
    # ¨h2L¹nÒ¦î
    # ¹Mnc
    bearing_norm = bearing % 360
    wind_norm = wind_direction % 360
    
    # Gn2L¹kşWf¨Lia‰K‰e‹K’$šY‹
    # Gn¹MK‰¨’DfBŞŠnî	360¦grc_YŠ’B
    # ]n$L0180¦j‰ó7K‰¨ ’ starboard tack
    # 180360¦j‰æ7K‰¨ ’ port tack
    # ;è: ¨o¨Le‹¹’:WGn¹MoGL2€¹’:Y
    wind_rel = (bearing_norm - wind_norm) % 360
    
    # 0-180¦n“j‰ó7K‰¨ ’ starboard tack
    # 180-360¦n“j‰æ7K‰¨ ’ port tack
    return 'port' if 0 <= wind_rel <= 180 else 'starboard'"""
    
    # ³üÉ’nÛ
    updated_content = content.replace(old_function, new_function)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
        
    print(f"[] ¿Ã¯$ší¸Ã¯’îcW~W_: {file_path}")
    return True

if __name__ == "__main__":
    print("ÑÃÁ¹¯ê×È: ¿Ã¯$ší¸Ã¯nîc’‹ËW~Y")
    fix_tack_identification()
    print("ÑÃÁ¹¯ê×È: îcŒ†")
