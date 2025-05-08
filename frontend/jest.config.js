const nextJest = require('next/jest');

const createJestConfig = nextJest({
  // next.config.jsとテスト環境用の.envファイルが配置されたディレクトリへのパス
  dir: './',
});

// Jestに渡すカスタム設定
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/src/tests/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    // エイリアスの設定
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/'],
};

// createJestConfigを使用することによって、next/jestが提供する設定とカスタム設定をマージして返す
module.exports = createJestConfig(customJestConfig);
