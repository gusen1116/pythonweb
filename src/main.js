function initInfiniteScroll() {
    // 블로그 목록 페이지에서만 실행
    const blogContainer = document.querySelector('.blog-container');
    if (!blogContainer) return;
    
    let page = 1;
    let loading = false;
    let noMorePosts = false;
    let requestInProgress = null; // 진행 중인, 혹은 최근 요청 저장
    let retryCount = 0; // 재시도 카운트
    const MAX_RETRIES = 3; // 최대 재시도 횟수
    
    // 로딩 인디케이터 생성
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 불러오는 중...';
    loadingIndicator.style.display = 'none';
    blogContainer.appendChild(loadingIndicator);
    
    // 디바운스 함수 - 스크롤 이벤트 최적화
    function debounce(func, wait) {
      let timeout;
      return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          func.apply(context, args);
        }, wait);
      };
    }
    
    // 스크롤 이벤트 리스너 - 디바운스 적용
    window.addEventListener('scroll', debounce(function() {
      if (loading || noMorePosts) return;
      
      // 페이지 하단에 도달했는지 확인 (하단에서 약 500px 위)
      if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
        loadMorePosts();
      }
    }, 100)); // 100ms 디바운스
    
    function loadMorePosts() {
      loading = true;
      loadingIndicator.style.display = 'block';
      
      // 이전 요청이 있으면 취소
      if (requestInProgress && requestInProgress.abort) {
        requestInProgress.abort();
      }
      
      // API 호출
      const controller = new AbortController();
      const signal = controller.signal;
      requestInProgress = controller;
      
      fetch(`/api/posts?page=${page + 1}`, { signal })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          retryCount = 0; // 성공 시 재시도 카운트 리셋
          
          if (data.posts && data.posts.length > 0) {
            page++;
            
            // 포스트 추가
            appendPosts(data.posts);
            
            // 마지막 페이지 확인
            if (!data.has_next) {
              noMorePosts = true;
              const endMessage = document.createElement('div');
              endMessage.className = 'end-of-posts';
              endMessage.textContent = '모든 글을 불러왔습니다.';
              blogContainer.appendChild(endMessage);
            }
          } else {
            noMorePosts = true;
          }
          
          loading = false;
          loadingIndicator.style.display = 'none';
        })
        .catch(error => {
          console.error('게시글 로드 중 오류 발생:', error);
          
          // 네트워크 오류면 재시도
          if (error.name === 'TypeError' && retryCount < MAX_RETRIES) {
            retryCount++;
            console.log(`재시도 중... (${retryCount}/${MAX_RETRIES})`);
            setTimeout(() => {
              loading = false;
              loadMorePosts();
            }, 2000); // 2초 후 재시도
          } else {
            loading = false;
            loadingIndicator.style.display = 'none';
            
            // 오류 메시지 표시
            const errorMsg = document.createElement('div');
            errorMsg.className = 'load-error';
            errorMsg.innerHTML = '<i class="fas fa-exclamation-circle"></i> 게시글을 불러오는 중 오류가 발생했습니다. <button class="retry-btn">재시도</button>';
            blogContainer.appendChild(errorMsg);
            
            errorMsg.querySelector('.retry-btn').addEventListener('click', () => {
              errorMsg.remove();
              retryCount = 0;
              loadMorePosts();
            });
          }
        });
    }
    
    function appendPosts(posts) {
      // 기존 페이지네이션 제거
      const pagination = document.querySelector('.pagination');
      if (pagination) {
        pagination.remove();
      }
      
      const postsContainer = document.querySelector('.blog-previews') || blogContainer;
      
      posts.forEach(post => {
        const postElement = createPostElement(post);
        postsContainer.appendChild(postElement);
        
        // 구분선 추가
        const separator = document.createElement('hr');
        separator.className = 'separator';
        postsContainer.appendChild(separator);
      });
    }
    
    function createPostElement(post) {
      const template = `
        <div class="blog-preview">
          <h3>
            <a href="/blog/post/${post.id}">${post.title}</a>
          </h3>
          
          <div class="post-preview">
            ${post.image ? `<img src="${post.image}" alt="Preview" class="post-preview-image">` : ''}
            
            <div class="preview-content">
              <div class="preview-text has-fade">
                ${post.preview_text}
              </div>
              <a href="/blog/post/${post.id}" class="read-more">더 읽기 →</a>
              
              <div class="post-meta-bottom">
                <div class="tags-category">
                  ${post.category ? `<span class="category">[${post.category}]</span>` : ''}
                  ${post.tags && post.tags.length > 0 ? `<span class="tags">${post.tags.join(', ')}</span>` : ''}
                </div>
                <span class="date">${post.created_at}</span>
              </div>
            </div>
          </div>
        </div>
      `;
      
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = template.trim();
      return tempDiv.firstChild;
    }
  }