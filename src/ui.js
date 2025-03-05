// static/js/ui.js
document.addEventListener('DOMContentLoaded', function() {
    // 테마 토글 기능
    const themeToggle = document.getElementById('theme-toggle');
    const lightbulbIcon = themeToggle.querySelector('i');
    
    // 전구 아이콘 업데이트 함수
    function updateLightbulbIcon() {
      if (document.body.classList.contains('dark-theme')) {
        // 다크 모드 - 꺼진 전구
        lightbulbIcon.className = 'far fa-lightbulb';
        themeToggle.title = '라이트 모드로 전환';
        themeToggle.setAttribute('aria-label', '라이트 모드로 전환');
      } else {
        // 라이트 모드 - 켜진 전구
        lightbulbIcon.className = 'fas fa-lightbulb';
        themeToggle.title = '다크 모드로 전환';
        themeToggle.setAttribute('aria-label', '다크 모드로 전환');
      }
    }
    
    updateLightbulbIcon();
    
    themeToggle.addEventListener('click', function() {
      document.body.classList.toggle('dark-theme');
      
      // 로컬 스토리지에 테마 설정 저장
      if (document.body.classList.contains('dark-theme')) {
        localStorage.setItem('theme', 'dark');
      } else {
        localStorage.setItem('theme', 'light');
      }
      
      updateLightbulbIcon();
    });
    
    // 드롭다운 메뉴 기능
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
      dropdown.addEventListener('click', function() {
        const menu = this.nextElementSibling;
        const isExpanded = menu.classList.contains('show');
        
        // 모든 메뉴 닫기
        document.querySelectorAll('.dropdown-menu.show').forEach(openMenu => {
          openMenu.classList.remove('show');
          openMenu.previousElementSibling.setAttribute('aria-expanded', 'false');
        });
        
        // 클릭한 메뉴 토글
        menu.classList.toggle('show');
        this.setAttribute('aria-expanded', !isExpanded);
      });
      
      // 키보드 접근성 지원
      dropdown.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.click();
        }
      });
    });
    
    // 드롭다운 외부 클릭 시 닫기
    document.addEventListener('click', function(e) {
      if (!e.target.matches('.dropdown-toggle') && !e.target.closest('.dropdown-toggle')) {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
          menu.classList.remove('show');
          menu.previousElementSibling.setAttribute('aria-expanded', 'false');
        });
      }
    });
    
// ui.js 파일에서 스크롤 이벤트 관련 코드 수정
// 스크롤 시 헤더 숨김/표시 효과
let lastScrollTop = 0;
const scrollThreshold = 50;
const scrollUpThreshold = 20; // 더 짧게 수정
let scrollUpAmount = 0;

window.addEventListener('scroll', function() {
  const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
  const header = document.querySelector('header');
  
  if (currentScroll > lastScrollTop) {
    // 아래로 스크롤 중
    scrollUpAmount = 0;
    if (currentScroll > scrollThreshold) {
      header.classList.add('hide');
    }
  } else {
    // 위로 스크롤 중
    scrollUpAmount += (lastScrollTop - currentScroll);
    
    if (scrollUpAmount > scrollUpThreshold) {
      header.classList.remove('hide');
    }
  }
  
  lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
}, { passive: true });
    
    // 플래시 메시지 자동 숨김
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
      setTimeout(() => {
        flashMessages.forEach(message => {
          message.classList.add('fade-out');
          setTimeout(() => {
            message.style.display = 'none';
          }, 500);
        });
      }, 4000);
    }
    
    // 무한 스크롤 기능 초기화 (blog.html이나 search.html 등에서 사용)
    if (typeof initInfiniteScroll === 'function') {
      initInfiniteScroll();
    }
  });