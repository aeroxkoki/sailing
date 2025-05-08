describe('Upload Flow', () => {
  beforeEach(() => {
    // APIリクエストをインターセプトするためのスタブ
    cy.intercept('POST', '**/analyze', {
      statusCode: 200,
      body: {
        sessionId: 'test-session-123',
        fileName: 'test.gpx',
        startTime: 1683111600000,
        endTime: 1683118800000,
        currentTime: 1683111600000,
        gpsData: [
          { 
            timestamp: 1683111600000, 
            latitude: 35.123, 
            longitude: 139.456, 
            speed: 5.2, 
            heading: 270 
          },
          // 他のポイントデータ...
        ],
        windData: [],
        strategyPoints: [],
        averageWindDirection: 230.5,
        averageWindSpeed: 12.3,
        upwindVMG: 4.5,
        downwindVMG: 5.8,
        trackLength: 12.5,
        totalTacks: 8,
        totalJibes: 3,
        performanceScore: 0.78
      },
      delay: 500 // 500msの遅延
    }).as('analyzeRequest');
    
    // ホームページに移動
    cy.visit('/');
  });

  it('should upload a file and show analysis results', () => {
    // テスト用のファイルをアップロード
    cy.fixture('test.gpx', { encoding: null }).as('gpxFile');
    cy.get('input[type="file"]').selectFile('@gpxFile', { force: true });
    
    // ローディング表示の確認
    cy.contains('データ分析中').should('be.visible');
    
    // APIコールの完了を待つ
    cy.wait('@analyzeRequest');
    
    // 分析結果の表示を確認
    cy.contains('230.5°').should('be.visible');
    cy.contains('12.3 kts').should('be.visible');
    
    // ビュー切り替えの確認
    cy.contains('風向風速').click();
    cy.contains('戦略').click();
    
    // 設定パネルの表示確認
    cy.contains('設定').click();
    cy.contains('詳細設定').should('be.visible');
    cy.contains('風向風速').should('be.visible');
    cy.contains('戦略').should('be.visible');
    cy.contains('表示').should('be.visible');
    cy.contains('詳細').should('be.visible');
  });

  it('should show error message on upload failure', () => {
    // エラーレスポンスのスタブ
    cy.intercept('POST', '**/analyze', {
      statusCode: 400,
      body: {
        message: 'Invalid file format or corrupted data'
      }
    }).as('failedRequest');
    
    // ファイルをアップロード
    cy.fixture('invalid.gpx', { encoding: null }).as('invalidFile');
    cy.get('input[type="file"]').selectFile('@invalidFile', { force: true });
    
    // APIコールの完了を待つ
    cy.wait('@failedRequest');
    
    // エラーメッセージの表示を確認
    cy.contains('エラーが発生しました').should('be.visible');
    cy.contains('Invalid file format or corrupted data').should('be.visible');
  });
});
