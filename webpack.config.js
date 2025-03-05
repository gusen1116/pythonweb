const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  mode: 'production',
  entry: {
    main: './src/index.js'
  },
  output: {
    filename: 'bundle.js', // 파일 이름 설정
    path: path.resolve(__dirname, 'static/js'),
    publicPath: '/static/js/',
    clean: true // 빌드 전 이전 번들 자동 삭제
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', {
                targets: '> 0.25%, not dead',
                useBuiltIns: 'usage', // 필요한 폴리필만 자동 포함
                corejs: 3
              }]
            ]
          }
        }
      }
    ]
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true, // 콘솔 로그 제거
            drop_debugger: true, // 디버거 명령문 제거
            pure_funcs: ['console.log'] // 특정 함수 완전 제거
          },
          format: {
            comments: false // 주석 제거
          }
        },
        extractComments: false
      })
    ],
    splitChunks: {
      chunks: 'async', // 비동기 청크만 분할
      minSize: 20000, // 최소 청크 크기 20KB
      maxSize: 244 * 1024, // 최대 청크 크기 제한
      minChunks: 1,
      maxAsyncRequests: 5, // 동시 비동기 요청 제한
      maxInitialRequests: 3, // 초기 로드 시 요청 제한
      automaticNameDelimiter: '~',
      cacheGroups: {
        defaultVendors: {
          test: /[\\/]node_modules[\\/]/,
          priority: -10,
          reuseExistingChunk: true
        },
        default: {
          minChunks: 2,
          priority: -20,
          reuseExistingChunk: true
        }
      }
    }
  },
  performance: {
    hints: 'warning', // 성능 경고 활성화
    maxEntrypointSize: 250000, // 엔트리 포인트 최대 크기
    maxAssetSize: 250000 // 단일 에셋 최대 크기
  },
  cache: {
    type: 'memory', // 메모리 기반 캐싱
    maxGenerations: 3 // 캐시 세대 제한
  },
  plugins: [
    new CompressionPlugin({
      algorithm: 'gzip', // Gzip 압축
      test: /\.js$/, // JS 파일만 압축
      compressionOptions: { level: 9 }, // 최대 압축 레벨
      threshold: 10240, // 10KB 이상인 경우에만 압축
      minRatio: 0.8 // 압축 이익이 80% 이상인 경우만 압축
    }),
    new BundleAnalyzerPlugin({
      analyzerMode: 'static', // 정적 HTML 보고서 생성
      openAnalyzer: false, // 자동으로 분석기 열기 비활성화
      reportFilename: 'bundle-report.html' // 보고서 파일명 지정
    })
  ],
  devtool: 'source-map' // 소스 맵 생성
};