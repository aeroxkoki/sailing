# -*- coding: utf-8 -*-
"""
修正済みの_normalize_to_timestamp関数。
unhashable type: 'dict'エラーを修正するためのパッチです。
"""

def _normalize_to_timestamp(self, t) -> float:
    """
    様々な時間表現から統一したUNIXタイムスタンプを作成
    
    Parameters:
    -----------
    t : any
        様々な時間表現(datetime, timedelta, int, float等)
        
    Returns:
    --------
    float
        UNIXタイムスタンプ形式の値
    """
    if isinstance(t, datetime):
        # datetimeをUNIXタイムスタンプに変換
        return t.timestamp()
    elif isinstance(t, timedelta):
        # timedeltaを秒に変換
        return t.total_seconds()
    elif isinstance(t, (int, float)):
        # 数値はそのままfloatで返す
        return float(t)
    elif isinstance(t, dict):
        # 辞書型の場合
        if 'timestamp' in t:
            # timestampキーを持つ辞書の場合
            return float(t['timestamp'])
        else:
            # timestampキーがない辞書の場合はエラー防止のため無限大を返す
            return float('inf')
    elif isinstance(t, str):
        try:
            # 数値文字列の場合は数値に変換
            return float(t)
        except ValueError:
            try:
                # ISO形式の日時文字列
                dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                return dt.timestamp()
            except ValueError:
                # 変換できない場合は無限大
                return float('inf')
    else:
        # その他の型は文字列に変換してから数値化
        try:
            return float(str(t))
        except ValueError:
            # 変換できない場合は無限大（対応する順序）
            return float('inf')
