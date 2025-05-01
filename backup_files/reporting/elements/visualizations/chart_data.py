# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import copy
import numpy as np
import pandas as pd
from datetime import datetime


class ChartData:
    """
                                  
    
                                                                                                          
    """
    
    def __init__(self, data: Any = None):
        """
                 
        
        Parameters
        ----------
        data : Any, optional
                           , by default None
        """
        self.data = data
        self.transformations = []
    
    def from_context(self, context: Dict[str, Any], data_source: str) -> 'ChartData':
        """
                                                  
        
        Parameters
        ----------
        context : Dict[str, Any]
                                       
        data_source : str
                                 
            
        Returns
        -------
        ChartData
                                                                              
        """
        if not data_source or data_source not in context:
            self.data = None
            return self
        
        self.data = context[data_source]
        return self
    
    def select_fields(self, fields: List[str]) -> 'ChartData':
        """
                                         
        
        Parameters
        ----------
        fields : List[str]
                                                      
            
        Returns
        -------
        ChartData
                                                                  
        """
        if self.data is None:
            return self
        
        #                                     
        if isinstance(self.data, list) and all(isinstance(item, dict) for item in self.data):
            result = []
            for item in self.data:
                new_item = {}
                for field in fields:
                    if field in item:
                        new_item[field] = item[field]
                result.append(new_item)
            
            self.data = result
        
        #                                  
        elif isinstance(self.data, dict):
            result = {}
            for field in fields:
                if field in self.data:
                    result[field] = self.data[field]
            
            self.data = result
        
        return self
    
    def filter(self, condition: Callable[[Any], bool]) -> 'ChartData':
        """
                                                              
        
        Parameters
        ----------
        condition : Callable[[Any], bool]
                                                                                       
            
        Returns
        -------
        ChartData
                                                                                 
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        self.data = [item for item in self.data if condition(item)]
        return self
    
    def map(self, transform: Callable[[Any], Any]) -> 'ChartData':
        """
                                                  
        
        Parameters
        ----------
        transform : Callable[[Any], Any]
                        
            
        Returns
        -------
        ChartData
                                                                  
        """
        if self.data is None:
            return self
        
        if isinstance(self.data, list):
            self.data = [transform(item) for item in self.data]
        else:
            self.data = transform(self.data)
        
        return self
    
    def sort(self, key: Optional[str] = None, reverse: bool = False) -> 'ChartData':
        """
                                
        
        Parameters
        ----------
        key : Optional[str], optional
                                                         , by default None
        reverse : bool, optional
                                       , by default False
            
        Returns
        -------
        ChartData
                                                                        
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if key is None:
            self.data = sorted(self.data, reverse=reverse)
        elif all(isinstance(item, dict) and key in item for item in self.data):
            self.data = sorted(self.data, key=lambda x: x[key], reverse=reverse)
        
        return self
    
    def limit(self, count: int) -> 'ChartData':
        """
                                
        
        Parameters
        ----------
        count : int
                              
            
        Returns
        -------
        ChartData
                                                                  
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        self.data = self.data[:count]
        return self
    
    def group_by(self, key: str, aggregation: Dict[str, str]) -> 'ChartData':
        """
                                               
        
        Parameters
        ----------
        key : str
                                                   
        aggregation : Dict[str, str]
                                             :                   
            
        Returns
        -------
        ChartData
                                                                           
        """
        if self.data is None or not isinstance(self.data, list) or len(self.data) == 0:
            return self
        
        if not all(isinstance(item, dict) and key in item for item in self.data):
            return self
        
        #                               
        df = pd.DataFrame(self.data)
        
        #                         
        agg_funcs = {}
        for field, func_name in aggregation.items():
            if field in df.columns:
                agg_funcs[field] = func_name
        
        if not agg_funcs:
            return self
        
        grouped = df.groupby(key).agg(agg_funcs).reset_index()
        
        #                            
        self.data = grouped.to_dict(orient='records')
        
        return self
    
    def to_time_series(self, time_key: str, value_key: str, time_format: Optional[str] = None) -> 'ChartData':
        """
                                            
        
        Parameters
        ----------
        time_key : str
                                                
        value_key : str
                                             
        time_format : Optional[str], optional
                                       , by default None
            
        Returns
        -------
        ChartData
                                                                                    
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and time_key in item and value_key in item for item in self.data):
            return self
        
        #                         
        result = []
        for item in self.data:
            time_val = item[time_key]
            
            #                                  
            if time_format and isinstance(time_val, str):
                try:
                    dt = datetime.strptime(time_val, time_format)
                    time_val = dt.isoformat()
                except ValueError:
                    pass
            
            result.append({
                "x": time_val,
                "y": item[value_key]
            })
        
        self.data = result
        return self
    
    def to_pie_data(self, label_key: str, value_key: str) -> 'ChartData':
        """
                                               
        
        Parameters
        ----------
        label_key : str
                                                   
        value_key : str
                                             
            
        Returns
        -------
        ChartData
                                                                                       
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and label_key in item and value_key in item for item in self.data):
            return self
        
        labels = [item[label_key] for item in self.data]
        values = [item[value_key] for item in self.data]
        
        self.data = {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": self._generate_colors(len(values))
            }]
        }
        
        return self
    
    def to_bar_data(self, label_key: str, value_key: str, series_key: Optional[str] = None) -> 'ChartData':
        """
                                               
        
        Parameters
        ----------
        label_key : str
                                                   
        value_key : str
                                             
        series_key : Optional[str], optional
                                                , by default None
            
        Returns
        -------
        ChartData
                                                                                       
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and label_key in item and value_key in item for item in self.data):
            return self
        
        #                      
        if series_key is None:
            labels = [item[label_key] for item in self.data]
            values = [item[value_key] for item in self.data]
            
            self.data = {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": self._generate_colors(1)[0],
                    "borderColor": self._generate_border_colors(1)[0],
                    "borderWidth": 1
                }]
            }
        else:
            #                      
            if not all(series_key in item for item in self.data):
                return self
            
            #                                                 
            labels = list(set(item[label_key] for item in self.data))
            series = list(set(item[series_key] for item in self.data))
            
            #                                           
            datasets = []
            colors = self._generate_colors(len(series))
            border_colors = self._generate_border_colors(len(series))
            
            for i, s in enumerate(series):
                #                                  
                series_data = {item[label_key]: item[value_key] for item in self.data if item[series_key] == s}
                
                #                                              
                values = [series_data.get(label, 0) for label in labels]
                
                datasets.append({
                    "label": str(s),
                    "data": values,
                    "backgroundColor": colors[i],
                    "borderColor": border_colors[i],
                    "borderWidth": 1
                })
            
            self.data = {
                "labels": labels,
                "datasets": datasets
            }
        
        return self
    
    def to_scatter_data(self, x_key: str, y_key: str, series_key: Optional[str] = None) -> 'ChartData':
        """
                                            
        
        Parameters
        ----------
        x_key : str
            X                                 
        y_key : str
            Y                                 
        series_key : Optional[str], optional
                                                , by default None
            
        Returns
        -------
        ChartData
                                                                                    
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and x_key in item and y_key in item for item in self.data):
            return self
        
        #                      
        if series_key is None:
            points = [{"x": item[x_key], "y": item[y_key]} for item in self.data]
            
            self.data = {
                "datasets": [{
                    "data": points,
                    "backgroundColor": self._generate_colors(1)[0],
                    "borderColor": self._generate_border_colors(1)[0],
                    "borderWidth": 1,
                    "pointRadius": 4,
                    "pointHoverRadius": 6
                }]
            }
        else:
            #                      
            if not all(series_key in item for item in self.data):
                return self
            
            #                                     
            series = list(set(item[series_key] for item in self.data))
            
            #                                           
            datasets = []
            colors = self._generate_colors(len(series))
            border_colors = self._generate_border_colors(len(series))
            
            for i, s in enumerate(series):
                #                                  
                series_data = [{"x": item[x_key], "y": item[y_key]} for item in self.data if item[series_key] == s]
                
                datasets.append({
                    "label": str(s),
                    "data": series_data,
                    "backgroundColor": colors[i],
                    "borderColor": border_colors[i],
                    "borderWidth": 1,
                    "pointRadius": 4,
                    "pointHoverRadius": 6
                })
            
            self.data = {
                "datasets": datasets
            }
        
        return self
    
    def to_line_data(self, x_key: str, y_key: str, series_key: Optional[str] = None) -> 'ChartData':
        """
                                                     
        
        Parameters
        ----------
        x_key : str
            X                                 
        y_key : str
            Y                                 
        series_key : Optional[str], optional
                                                , by default None
            
        Returns
        -------
        ChartData
                                                                                             
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and x_key in item and y_key in item for item in self.data):
            return self
        
        #                         X               
        self.data = sorted(self.data, key=lambda item: item[x_key])
        
        #                      
        if series_key is None:
            x_values = [item[x_key] for item in self.data]
            y_values = [item[y_key] for item in self.data]
            
            self.data = {
                "labels": x_values,
                "datasets": [{
                    "data": y_values,
                    "backgroundColor": self._generate_colors(1)[0] + "33",  #                   
                    "borderColor": self._generate_border_colors(1)[0],
                    "borderWidth": 2,
                    "tension": 0.1,
                    "fill": True
                }]
            }
        else:
            #                      
            if not all(series_key in item for item in self.data):
                return self
            
            #                                     
            series = list(set(item[series_key] for item in self.data))
            
            #             X                                 
            all_x_values = sorted(list(set(item[x_key] for item in self.data)))
            
            #                                           
            datasets = []
            colors = self._generate_colors(len(series))
            border_colors = self._generate_border_colors(len(series))
            
            for i, s in enumerate(series):
                #                                  
                series_data = {item[x_key]: item[y_key] for item in self.data if item[series_key] == s}
                
                #             X                           
                values = [series_data.get(x, None) for x in all_x_values]
                
                datasets.append({
                    "label": str(s),
                    "data": values,
                    "backgroundColor": colors[i] + "33",  #                   
                    "borderColor": border_colors[i],
                    "borderWidth": 2,
                    "tension": 0.1,
                    "fill": True
                })
            
            self.data = {
                "labels": all_x_values,
                "datasets": datasets
            }
        
        return self
    
    def set_data(self, data: Any) -> 'ChartData':
        """
                                
        
        Parameters
        ----------
        data : Any
                                 
            
        Returns
        -------
        ChartData
                                                                              
        """
        self.data = data
        return self
    
    def get_data(self) -> Any:
        """
                          
        
        Returns
        -------
        Any
                              
        """
        return self.data
    
    def _generate_colors(self, count: int) -> List[str]:
        """
                                         
        
        Parameters
        ----------
        count : int
                     
            
        Returns
        -------
        List[str]
                                             RGBA         
        """
        colors = [
            "rgba(54, 162, 235, 0.7)",    #    
            "rgba(255, 99, 132, 0.7)",    #    
            "rgba(75, 192, 192, 0.7)",    #    /         
            "rgba(255, 159, 64, 0.7)",    #             
            "rgba(153, 102, 255, 0.7)",   #    
            "rgba(255, 205, 86, 0.7)",    #    
            "rgba(201, 203, 207, 0.7)",   #          
            "rgba(255, 99, 71, 0.7)",     #          
            "rgba(50, 205, 50, 0.7)",     #          
            "rgba(65, 105, 225, 0.7)"     #                      
        ]
        
        #                                                                               
        if count > len(colors):
            colors = colors * (count // len(colors) + 1)
        
        return colors[:count]
    
    def _generate_border_colors(self, count: int) -> List[str]:
        """
                                                  
        
        Parameters
        ----------
        count : int
                     
            
        Returns
        -------
        List[str]
                                             RGBA         
        """
        colors = [
            "rgba(54, 162, 235, 1)",    #    
            "rgba(255, 99, 132, 1)",    #    
            "rgba(75, 192, 192, 1)",    #    /         
            "rgba(255, 159, 64, 1)",    #             
            "rgba(153, 102, 255, 1)",   #    
            "rgba(255, 205, 86, 1)",    #    
            "rgba(201, 203, 207, 1)",   #          
            "rgba(255, 99, 71, 1)",     #          
            "rgba(50, 205, 50, 1)",     #          
            "rgba(65, 105, 225, 1)"     #                      
        ]
        
        #                                                                               
        if count > len(colors):
            colors = colors * (count // len(colors) + 1)
        
        return colors[:count]


class ChartDataTransformation:
    """
                                        
    
                                                                                     
    """
    
    def __init__(self, transform_func: Callable[[Any], Any]):
        """
                 
        
        Parameters
        ----------
        transform_func : Callable[[Any], Any]
                        
        """
        self.transform_func = transform_func
    
    def apply(self, data: Any) -> Any:
        """
                       
        
        Parameters
        ----------
        data : Any
                                 
            
        Returns
        -------
        Any
                                    
        """
        return self.transform_func(data)
