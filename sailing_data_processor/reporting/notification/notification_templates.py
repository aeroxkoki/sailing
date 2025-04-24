# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.notification.notification_templates

通知テンプレートの管理と処理を行うモジュール
"""

import logging
import datetime
import json
from typing import Dict, List, Optional, Union, Any, Callable

# ロガーの設定
logger = logging.getLogger(__name__)

class NotificationTemplate:
    """
    通知テンプレートクラス
    
    イベントタイプに対応した通知テンプレートの定義と処理を行います。
    """
    
    def __init__(self, template_id: str, title_template: str, body_template: str, 
                 event_type: str, channels: List[str] = None, 
                 formatter: Callable = None):
        """
        初期化
        
        Parameters
        ----------
        template_id : str
            テンプレートID
        title_template : str
            タイトルテンプレート文字列（変数置換可能）
        body_template : str
            本文テンプレート文字列（変数置換可能）
        event_type : str
            対応するイベントタイプ
        channels : List[str], optional
            デフォルトの通知チャネル, by default None
        formatter : Callable, optional
            カスタムフォーマッタ関数, by default None
        """
        self.template_id = template_id
        self.title_template = title_template
        self.body_template = body_template
        self.event_type = event_type
        self.channels = channels or ["app"]
        self.formatter = formatter
    
    def format_notification(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        通知を書式設定
        
        Parameters
        ----------
        event_data : Dict[str, Any]
            イベントデータ
            
        Returns
        -------
        Dict[str, str]
            書式設定された通知 {"title": str, "body": str}
        """
        # カスタムフォーマッタがある場合は使用
        if self.formatter:
            return self.formatter(self.title_template, self.body_template, event_data)
        
        # デフォルトの変数置換処理
        try:
            title = self._replace_variables(self.title_template, event_data)
            body = self._replace_variables(self.body_template, event_data)
            
            return {
                "title": title,
                "body": body
            }
        except Exception as e:
            logger.error(f"Failed to format notification: {str(e)}")
            return {
                "title": "通知",
                "body": "詳細を確認してください。"
            }
    
    def _replace_variables(self, template: str, data: Dict[str, Any]) -> str:
        """
        テンプレート内の変数を置換
        
        Parameters
        ----------
        template : str
            テンプレート文字列
        data : Dict[str, Any]
            置換データ
            
        Returns
        -------
        str
            置換後の文字列
        """
        result = template
        
        # 単純な変数置換（{variable_name}形式）
        for key, value in data.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                # 値が辞書や配列の場合は文字列化
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, (datetime.date, datetime.datetime)):
                    value_str = value.isoformat()
                else:
                    value_str = str(value)
                
                result = result.replace(placeholder, value_str)
        
        return result


class NotificationTemplateManager:
    """
    通知テンプレート管理クラス
    
    通知テンプレートの登録、検索、書式設定を行います。
    """
    
    def __init__(self, storage_manager=None):
        """
        初期化
        
        Parameters
        ----------
        storage_manager : object, optional
            ストレージ管理オブジェクト, by default None
        """
        self.storage_manager = storage_manager
        
        # テンプレートストレージ
        self._templates = {}  # {template_id: NotificationTemplate}
        
        # イベントタイプマッピング
        self._event_type_templates = {}  # {event_type: [template_ids]}
        
        # 標準テンプレートの登録
        self._register_standard_templates()
        
        logger.info("NotificationTemplateManager initialized")
    
    def _register_standard_templates(self):
        """標準テンプレートを登録"""
        # レポート共有テンプレート
        self.register_template(
            "report_shared",
            "{user_name}がレポートを共有しました",
            "{user_name}があなたとレポート「{report_name}」を共有しました。",
            "report_shared",
            ["app", "email"]
        )
        
        # 戦略ポイント検出テンプレート
        self.register_template(
            "strategy_point_detected",
            "新しい戦略ポイントが検出されました",
            "セッション「{session_name}」で新しい戦略ポイント（{point_type}）が検出されました。",
            "strategy_point_detected",
            ["app"]
        )
        
        # コメント追加テンプレート
        self.register_template(
            "comment_added",
            "コメントが追加されました",
            "{user_name}が{item_type}「{item_name}」にコメントを追加しました: \"{comment_text}\"",
            "comment_added",
            ["app", "email"]
        )
        
        # レポート更新テンプレート
        self.register_template(
            "report_updated",
            "レポートが更新されました",
            "{user_name}がレポート「{report_name}」を更新しました。",
            "report_updated",
            ["app"]
        )
        
        # チーム招待テンプレート
        self.register_template(
            "team_invitation",
            "チームに招待されました",
            "{user_name}があなたをチーム「{team_name}」に招待しました。",
            "team_invitation",
            ["app", "email"]
        )
        
        # 分析完了テンプレート
        self.register_template(
            "analysis_completed",
            "分析が完了しました",
            "セッション「{session_name}」の分析が完了しました。重要な発見: {findings}",
            "analysis_completed",
            ["app"]
        )
    
    def register_template(self, template_id: str, title_template: str, 
                         body_template: str, event_type: str, 
                         channels: List[str] = None, formatter: Callable = None) -> bool:
        """
        テンプレートを登録
        
        Parameters
        ----------
        template_id : str
            テンプレートID
        title_template : str
            タイトルテンプレート
        body_template : str
            本文テンプレート
        event_type : str
            対応するイベントタイプ
        channels : List[str], optional
            デフォルトの通知チャネル, by default None
        formatter : Callable, optional
            カスタムフォーマッタ関数, by default None
            
        Returns
        -------
        bool
            登録成功したかどうか
        """
        try:
            template = NotificationTemplate(
                template_id=template_id,
                title_template=title_template,
                body_template=body_template,
                event_type=event_type,
                channels=channels,
                formatter=formatter
            )
            
            # テンプレート保存
            self._templates[template_id] = template
            
            # イベントタイプマッピング更新
            if event_type not in self._event_type_templates:
                self._event_type_templates[event_type] = []
            
            if template_id not in self._event_type_templates[event_type]:
                self._event_type_templates[event_type].append(template_id)
            
            # ストレージマネージャーがある場合は永続化
            if self.storage_manager:
                try:
                    self.storage_manager.save_notification_template(template_id, {
                        "template_id": template_id,
                        "title_template": title_template,
                        "body_template": body_template,
                        "event_type": event_type,
                        "channels": channels
                    })
                    logger.info(f"Template {template_id} saved to storage")
                except Exception as e:
                    logger.error(f"Failed to save template: {str(e)}")
            
            logger.info(f"Template '{template_id}' registered for event type '{event_type}'")
            return True
        
        except Exception as e:
            logger.error(f"Failed to register template: {str(e)}")
            return False
    
    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """
        テンプレートを取得
        
        Parameters
        ----------
        template_id : str
            テンプレートID
            
        Returns
        -------
        Optional[NotificationTemplate]
            通知テンプレート
        """
        return self._templates.get(template_id)
    
    def get_templates_for_event(self, event_type: str) -> List[NotificationTemplate]:
        """
        イベントタイプに対応するテンプレートを取得
        
        Parameters
        ----------
        event_type : str
            イベントタイプ
            
        Returns
        -------
        List[NotificationTemplate]
            通知テンプレートのリスト
        """
        template_ids = self._event_type_templates.get(event_type, [])
        templates = []
        
        for template_id in template_ids:
            template = self.get_template(template_id)
            if template:
                templates.append(template)
        
        return templates
    
    def format_notification(self, event_type: str, event_data: Dict[str, Any], 
                          template_id: str = None) -> Dict[str, str]:
        """
        通知を書式設定
        
        Parameters
        ----------
        event_type : str
            イベントタイプ
        event_data : Dict[str, Any]
            イベントデータ
        template_id : str, optional
            テンプレートID（指定がない場合はイベントタイプから検索）, by default None
            
        Returns
        -------
        Dict[str, str]
            書式設定された通知 {"title": str, "body": str}
        """
        # テンプレートを取得
        template = None
        
        if template_id:
            template = self.get_template(template_id)
        else:
            templates = self.get_templates_for_event(event_type)
            if templates:
                template = templates[0]  # 最初のテンプレートを使用
        
        # テンプレートがない場合はデフォルト通知を返す
        if not template:
            return {
                "title": f"{event_type.replace('_', ' ').title()}",
                "body": "通知の詳細を確認してください。"
            }
        
        # テンプレートで書式設定
        return template.format_notification(event_data)
    
    def delete_template(self, template_id: str) -> bool:
        """
        テンプレートを削除
        
        Parameters
        ----------
        template_id : str
            テンプレートID
            
        Returns
        -------
        bool
            削除成功したかどうか
        """
        if template_id not in self._templates:
            logger.warning(f"Template {template_id} not found")
            return False
        
        template = self._templates[template_id]
        event_type = template.event_type
        
        # テンプレート削除
        del self._templates[template_id]
        
        # イベントタイプマッピング更新
        if event_type in self._event_type_templates and template_id in self._event_type_templates[event_type]:
            self._event_type_templates[event_type].remove(template_id)
            
            # リストが空になった場合はキー削除
            if not self._event_type_templates[event_type]:
                del self._event_type_templates[event_type]
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.delete_notification_template(template_id)
                logger.info(f"Template {template_id} removed from storage")
            except Exception as e:
                logger.error(f"Failed to delete template: {str(e)}")
        
        logger.info(f"Template '{template_id}' deleted")
        return True
