const path = require('path');

module.exports = {
  mode: 'development', // 개발 시 'development', 배포 시 'production'으로 변경
  entry: './src/index.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, '../static/js'),
    publicPath: '/static/js/'
  },
  module: {
    rules: [
      {
         test: /\.js$/,
         exclude: /node_modules/,
         use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env']
            }
         }
      }
    ]
  }
};