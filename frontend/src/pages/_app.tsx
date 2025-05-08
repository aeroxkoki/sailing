import type { AppProps } from 'next/app';
import { SettingsProvider, AnalysisProvider } from '../context';
import '../styles/globals.css';

/**
 * アプリケーションのルートコンポーネント
 * 全ページ共通のプロバイダーやレイアウトを定義
 */
export default function App({ Component, pageProps }: AppProps) {
  return (
    <SettingsProvider>
      <AnalysisProvider>
        <Component {...pageProps} />
      </AnalysisProvider>
    </SettingsProvider>
  );
}
