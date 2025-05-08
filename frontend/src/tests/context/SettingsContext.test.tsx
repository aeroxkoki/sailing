import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { SettingsProvider, useSettings } from '@/context/SettingsContext';

// テスト用のコンポーネント
const TestComponent = () => {
  const { settings, updateSettings, resetSettings } = useSettings();
  
  return (
    <div>
      <div data-testid="wind-algorithm">{settings.wind.algorithm}</div>
      <div data-testid="strategy-sensitivity">{settings.strategy.sensitivity}</div>
      <button 
        onClick={() => updateSettings('wind', 'algorithm', 'bayesian')}
        data-testid="update-wind"
      >
        Update Wind Algorithm
      </button>
      <button 
        onClick={() => updateSettings('strategy', 'sensitivity', 80)}
        data-testid="update-sensitivity"
      >
        Update Sensitivity
      </button>
      <button onClick={resetSettings} data-testid="reset">Reset Settings</button>
    </div>
  );
};

describe('SettingsContext', () => {
  it('provides default settings', () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );
    
    expect(screen.getByTestId('wind-algorithm')).toHaveTextContent('combined');
    expect(screen.getByTestId('strategy-sensitivity')).toHaveTextContent('70');
  });
  
  it('updates settings when updateSettings is called', () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );
    
    // 初期値の確認
    expect(screen.getByTestId('wind-algorithm')).toHaveTextContent('combined');
    
    // 設定更新
    fireEvent.click(screen.getByTestId('update-wind'));
    
    // 変更後の値の確認
    expect(screen.getByTestId('wind-algorithm')).toHaveTextContent('bayesian');
  });
  
  it('resets settings when resetSettings is called', () => {
    render(
      <SettingsProvider>
        <TestComponent />
      </SettingsProvider>
    );
    
    // 初期値の確認
    expect(screen.getByTestId('strategy-sensitivity')).toHaveTextContent('70');
    
    // 設定更新
    fireEvent.click(screen.getByTestId('update-sensitivity'));
    expect(screen.getByTestId('strategy-sensitivity')).toHaveTextContent('80');
    
    // 設定リセット
    fireEvent.click(screen.getByTestId('reset'));
    
    // リセット後の値の確認
    expect(screen.getByTestId('strategy-sensitivity')).toHaveTextContent('70');
  });
});
