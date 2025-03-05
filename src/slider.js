// static/js/slider.js
document.addEventListener('DOMContentLoaded', function() {
    // 슬라이더 초기화
    initSlider();
    
    // 슬라이더 기능 초기화
    function initSlider() {
      const sliderContainer = document.querySelector('.slider-container');
      if (!sliderContainer) return;
      
      const sliderWrapper = sliderContainer.querySelector('.slider-wrapper');
      const slides = sliderContainer.querySelectorAll('.slide');
      const indicatorsContainer = sliderContainer.querySelector('.slider-indicators');
      
      if (!slides.length) return;
      
      // 슬라이더 상태
      let currentIndex = 0;
      let slideWidth = sliderContainer.clientWidth;
      let autoplayTimer = null;
      let touchStartX = 0;
      let touchEndX = 0;
      
      // 초기 설정
      function initialize() {
        // 좌우 화살표 버튼 제거 (요청대로)
        const prevBtn = sliderContainer.querySelector('.prev');
        const nextBtn = sliderContainer.querySelector('.next');
        if (prevBtn) prevBtn.remove();
        if (nextBtn) nextBtn.remove();
        
        // 슬라이드 갯수에 맞게 인디케이터 생성
        createIndicators();
        
        // 창 크기가 변경될 때 슬라이드 너비 업데이트
        window.addEventListener('resize', function() {
          slideWidth = sliderContainer.clientWidth;
          goToSlide(currentIndex);
        });
        
        // 첫 슬라이드 표시
        goToSlide(0);
        
        // 자동 슬라이드 시작
        startAutoplay();
        
        // 슬라이더 클릭 이벤트 추가 (왼쪽/오른쪽 영역 클릭 시 이동)
        sliderContainer.addEventListener('click', function(e) {
          const containerWidth = sliderContainer.clientWidth;
          const clickX = e.offsetX;
          
          // 컨테이너의 왼쪽 30% 영역 클릭 시 이전 슬라이드
          if (clickX < containerWidth * 0.3) {
            goToPrevSlide();
            resetAutoplay();
          } 
          // 컨테이너의 오른쪽 30% 영역 클릭 시 다음 슬라이드
          else if (clickX > containerWidth * 0.7) {
            goToNextSlide();
            resetAutoplay();
          }
        });
        
        // 터치 이벤트 추가 (모바일 지원)
        sliderContainer.addEventListener('touchstart', function(e) {
          touchStartX = e.changedTouches[0].screenX;
        }, {passive: true});
        
        sliderContainer.addEventListener('touchend', function(e) {
          touchEndX = e.changedTouches[0].screenX;
          handleSwipe();
        }, {passive: true});
      }
      
      // 스와이프 처리
      function handleSwipe() {
        // 오른쪽에서 왼쪽으로 스와이프 (다음 슬라이드)
        if (touchEndX < touchStartX - 50) {
          goToNextSlide();
          resetAutoplay();
        }
        // 왼쪽에서 오른쪽으로 스와이프 (이전 슬라이드)
        else if (touchEndX > touchStartX + 50) {
          goToPrevSlide();
          resetAutoplay();
        }
      }
      
      // 인디케이터 생성
      function createIndicators() {
        if (!indicatorsContainer) return;
        
        indicatorsContainer.innerHTML = '';
        
        for (let i = 0; i < slides.length; i++) {
          const indicator = document.createElement('span');
          indicator.classList.add('indicator');
          indicator.dataset.index = i;
          
          indicator.addEventListener('click', function() {
            goToSlide(i);
            resetAutoplay();
          });
          
          indicatorsContainer.appendChild(indicator);
        }
        
        updateIndicators();
      }
      
      // 인디케이터 업데이트
      function updateIndicators() {
        if (!indicatorsContainer) return;
        
        const indicators = indicatorsContainer.querySelectorAll('.indicator');
        indicators.forEach((indicator, index) => {
          if (index === currentIndex) {
            indicator.classList.add('active');
          } else {
            indicator.classList.remove('active');
          }
        });
      }
      
      // 슬라이드 이동
      function goToSlide(index) {
        if (index < 0) {
          index = slides.length - 1;
        } else if (index >= slides.length) {
          index = 0;
        }
        
        currentIndex = index;
        const offset = -currentIndex * slideWidth;
        sliderWrapper.style.transform = `translateX(${offset}px)`;
        
        updateIndicators();
      }
      
      // 이전 슬라이드
      function goToPrevSlide() {
        goToSlide(currentIndex - 1);
      }
      
      // 다음 슬라이드
      function goToNextSlide() {
        goToSlide(currentIndex + 1);
      }
      
      // 자동 슬라이드 시작
      function startAutoplay() {
        stopAutoplay();
        autoplayTimer = setInterval(goToNextSlide, 5000); // 5초마다 다음 슬라이드
      }
      
      // 자동 슬라이드 중지
      function stopAutoplay() {
        if (autoplayTimer) {
          clearInterval(autoplayTimer);
          autoplayTimer = null;
        }
      }
      
      // 자동 슬라이드 재설정
      function resetAutoplay() {
        stopAutoplay();
        startAutoplay();
      }
      
      // 초기화 실행
      initialize();
      
      // 슬라이더 컨테이너에 마우스 오버 시 자동 슬라이드 일시 중지
      sliderContainer.addEventListener('mouseenter', stopAutoplay);
      sliderContainer.addEventListener('mouseleave', startAutoplay);
    }
  });