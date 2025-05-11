import React from 'react';

function Error({ statusCode, hasGetInitialPropsRun, err }: any) {
  if (!hasGetInitialPropsRun && err) {
    // getInitialProps is not called in case of
    // https://github.com/vercel/next.js/issues/8592. As a workaround, we pass
    // err via _app.js so it can be captured
    console.warn(
      'getInitialProps was not called for _error. ' +
        'https://github.com/vercel/next.js/issues/8592'
    );
  }

  return (
    <div className="min-h-screen bg-black text-gray-200 flex items-center justify-center">
      <div className="text-center p-8">
        <h1 className="text-6xl font-bold text-red-500 mb-4">
          {statusCode || 'エラー'}
        </h1>
        <p className="text-xl mb-8">
          {statusCode
            ? `サーバーで${statusCode}エラーが発生しました。`
            : 'クライアントでエラーが発生しました。'}
        </p>
        {err?.message && (
          <div className="mb-8 p-4 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400 font-mono">
              {err.message}
            </p>
          </div>
        )}
        <a
          href="/"
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          ホームに戻る
        </a>
      </div>
    </div>
  );
}

Error.getInitialProps = ({ res, err }: any) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
  return { statusCode, hasGetInitialPropsRun: true };
};

export default Error;
