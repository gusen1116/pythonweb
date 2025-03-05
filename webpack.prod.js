const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const webpack = require('webpack');

module.exports = {
  mode: 'production',
  entry: {
    main: './src/index.js',
     // 에디터 코드를 별도 번들로 분리
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, 'app/static/js'),
    publicPath: '/static/js/',
    clean: true
  },
  resolve: {
    extensions: ['.js', '.mjs'],
    fallback: {
      "fs": false,
      "path": require.resolve("path-browserify")
    }
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
                useBuiltIns: 'usage',
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
            drop_console: true,
            drop_debugger: true
          },
          format: {
            comments: false
          }
        },
        extractComments: false
      })
    ],
    splitChunks: {
      chunks: 'all',
      maxSize: 244 * 1024,
      minChunks: 1,
      name: false
    }
  },
  performance: {
    hints: 'warning',
    maxEntrypointSize: 250000,
    maxAssetSize: 250000
  },
  plugins: [
    new CompressionPlugin({
      algorithm: 'gzip',
      test: /\.js$/,
      compressionOptions: { level: 9 }
    }),
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false
    }),
    new webpack.ProvidePlugin({
      Underline: ['@editorjs/underline', 'default']
    })
  ],
  devtool: 'source-map'
};