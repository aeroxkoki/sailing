const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    setupNodeEvents(on, config) {
      // e2e テスト中のNode.jsイベントを実装
      // 詳細はhttps://docs.cypress.io/api/plugins/after-screenshot-api
    },
  },
  env: {
    // テスト用の環境変数を設定
    apiUrl: 'https://sailing-strategy-api.onrender.com'
  },
  video: false, // CIでの実行時にビデオを無効化
});
