// src/index.js
// 기본 사이트 기능에 필요한 파일만 가져오기
import './main.js';
import './ui.js';
import './slider.js';

// 메인 애플리케이션 초기화
document.addEventListener('DOMContentLoaded', function() {
  console.log('메인 애플리케이션 초기화');
  
  // 무한 스크롤 초기화 (필요한 경우)
  if (typeof initInfiniteScroll === 'function') {
    initInfiniteScroll();
  }
});