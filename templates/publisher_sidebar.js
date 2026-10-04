(() => {
    const sidebar = document.getElementById('publisher_intro');
    const sample = document.getElementById('plurk-ad-preview');
    const summary = sidebar.querySelector('.publisher_summary');
    let page = null;
    let currentPage = '搜尋表符';
    let hasContent = sidebar.dataset.hasContent === 'true';

    function layout() {
        if (!page || sidebar.hidden) return;
        const bounds = page.querySelector('.div_input_card').getBoundingClientRect();
        const pageBounds = page.getBoundingClientRect();
        const availableWidth = document.documentElement.clientWidth;
        const desktop = bounds.right + 20 + 300 + 20 <= availableWidth;
        sidebar.classList.toggle('sidebar-desktop', desktop);
        if (desktop) {
            sidebar.style.left = `${(sidebar.dataset.variant === 'b' ? availableWidth - 320 : bounds.right + 20) - pageBounds.left}px`;
            sidebar.style.top = `${bounds.top - pageBounds.top}px`;
        } else {
            sidebar.style.removeProperty('left');
            sidebar.style.removeProperty('top');
        }
        // One local sample, shared across pages. No Google request or refresh.
        if (sample) sample.hidden = (currentPage === '搜尋表符' && !hasContent) || sidebar.clientWidth < 300;
    }

    window.plurkSidebar = {
        mount() {
            page = document.getElementById('搜尋表符');
            page.insertBefore(document.getElementById('initial_gallery'), document.getElementById('emoji_result_table'));
            page.append(sidebar);
            document.getElementById('initial_shell').hidden = true;
            layout();
        },
        setSearchState(state) {
            if (state === 'ready') hasContent = true;
            if (state === 'empty' || state === 'error') hasContent = false;
            document.getElementById('search_update_status').textContent = state === 'loading' ? '更新中…' : '';
            layout();
        },
        setSubpage(name) {
            currentPage = name;
            sidebar.hidden = name !== '搜尋表符' && name !== '新增表符';
            if (sidebar.hidden) {
                if (sample) sample.hidden = true;
                return;
            }
            page = document.getElementById(name);
            page.append(sidebar);
            summary.textContent = name === '新增表符' ? '選擇來源，匯入你想收錄的表符。' : '用標籤找表符，點擊圖片即可複製。';
            layout();
        },
    };
    window.addEventListener('resize', layout);
})();
