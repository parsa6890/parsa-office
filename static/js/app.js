/* ==========================================================
   Enterprise SaaS — App JS (Final)
   ========================================================== */

(function () {
    'use strict';

    /* ==========================================================
       THEME (Light / Dark)
       ========================================================== */
    const THEME_KEY = 'django-todo-theme';
    const root = document.documentElement;

    function getPreferredTheme() {
        const stored = localStorage.getItem(THEME_KEY);
        if (stored) return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
        const icon = document.querySelector('[data-theme-toggle] i');
        if (icon) icon.className = theme === 'dark' ? 'ti ti-sun' : 'ti ti-moon';
    }

    // اعمال فوری برای جلوگیری از FOUC
    applyTheme(getPreferredTheme());


    /* ==========================================================
       DOM READY
       ========================================================== */
    document.addEventListener('DOMContentLoaded', () => {

        /* ---------- Re-apply theme ---------- */
        applyTheme(getPreferredTheme());

        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', () => {
                const current = root.getAttribute('data-theme');
                applyTheme(current === 'dark' ? 'light' : 'dark');
            });
        });


        /* ==========================================================
           MOBILE SIDEBAR
           ========================================================== */
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.querySelector('[data-menu-toggle]');
        if (menuBtn && sidebar) {
            menuBtn.addEventListener('click', () => sidebar.classList.toggle('is-open'));
            document.addEventListener('click', (e) => {
                if (sidebar.classList.contains('is-open') &&
                    !sidebar.contains(e.target) &&
                    !menuBtn.contains(e.target)) {
                    sidebar.classList.remove('is-open');
                }
            });
        }


        /* ==========================================================
           PASSWORD TOGGLE
           ========================================================== */
        document.querySelectorAll('.toggle-pw').forEach(btn => {
            btn.addEventListener('click', () => {
                const input = btn.parentElement.querySelector('input');
                if (!input) return;
                const type = input.type === 'password' ? 'text' : 'password';
                input.type = type;
                btn.querySelector('i').className =
                    type === 'password' ? 'ti ti-eye' : 'ti ti-eye-off';
            });
        });


        /* ==========================================================
           TOASTS
           ========================================================== */
        const toasts = document.querySelectorAll('.toast');
        toasts.forEach((t, i) => {
            setTimeout(() => dismissToast(t), 4000 + i * 200);
            t.querySelector('.toast__close')?.addEventListener('click', () => dismissToast(t));
        });

        function dismissToast(el) {
            if (!el || el.classList.contains('is-leaving')) return;
            el.classList.add('is-leaving');
            setTimeout(() => el.remove(), 300);
        }

        window.showToast = (message, variant = 'info') => {
            const icons = {
                success: 'ti-check',
                danger: 'ti-alert-circle',
                warning: 'ti-alert-triangle',
                info: 'ti-info-circle',
            };
            const container = document.querySelector('.toast-container') || createToastContainer();
            const t = document.createElement('div');
            t.className = `toast toast--${variant}`;
            t.innerHTML = `<i class="ti ${icons[variant] || icons.info}"></i><span>${message}</span>`;
            container.appendChild(t);
            setTimeout(() => dismissToast(t), 4000);
        };

        function createToastContainer() {
            const c = document.createElement('div');
            c.className = 'toast-container';
            document.body.appendChild(c);
            return c;
        }


        /* ==========================================================
           CSRF HELPER
           ========================================================== */
        function getCSRF() {
            const v = `; ${document.cookie}`;
            const p = v.split('; csrftoken=');
            if (p.length === 2) return p.pop().split(';').shift();
            return '';
        }


        /* ==========================================================
           KANBAN DRAG & DROP
           ========================================================== */
        const cards = document.querySelectorAll('.kanban-card');
        const columns = document.querySelectorAll('.kanban-column');

        // تشخیص drag تا مودال باز نشه
        window.__isDragging = false;
        document.addEventListener('dragstart', () => { window.__isDragging = true; });
        document.addEventListener('dragend', () => {
            setTimeout(() => { window.__isDragging = false; }, 100);
        });

        if (cards.length && columns.length) {
            cards.forEach(card => {
                card.addEventListener('dragstart', e => {
                    e.dataTransfer.setData('text/plain', card.dataset.id);
                    e.dataTransfer.effectAllowed = 'move';
                    card.classList.add('is-dragging');
                });
                card.addEventListener('dragend', () => card.classList.remove('is-dragging'));
            });

            columns.forEach(col => {
                col.addEventListener('dragover', e => {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    col.classList.add('is-dragover');
                });
                col.addEventListener('dragleave', e => {
                    if (!col.contains(e.relatedTarget)) col.classList.remove('is-dragover');
                });
                col.addEventListener('drop', async e => {
                    e.preventDefault();
                    col.classList.remove('is-dragover');

                    const id = e.dataTransfer.getData('text/plain');
                    const card = document.querySelector(`.kanban-card[data-id="${id}"]`);
                    if (!card) return;

                    const newStatus = col.dataset.status;
                    const oldStatus = card.dataset.status;
                    if (newStatus === oldStatus) return;

                    const oldColumnBody = document.querySelector(
                        `.kanban-column[data-status="${oldStatus}"] .kanban-column__body`
                    );
                    const newColumnBody = col.querySelector('.kanban-column__body');

                    // Optimistic UI
                    newColumnBody.appendChild(card);
                    card.dataset.status = newStatus;
                    updateCounts();

                    try {
                        const res = await fetch(`/task/${id}/status/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCSRF(),
                            },
                            body: JSON.stringify({ status: newStatus }),
                        });
                        if (!res.ok) throw new Error();
                        window.showToast?.('وضعیت وظیفه به‌روزرسانی شد', 'success');
                    } catch {
                        oldColumnBody.appendChild(card);
                        card.dataset.status = oldStatus;
                        updateCounts();
                        window.showToast?.('خطا در ذخیره تغییرات', 'danger');
                    }
                });
            });

            function updateCounts() {
                document.querySelectorAll('.kanban-column').forEach(col => {
                    const count = col.querySelectorAll('.kanban-card').length;
                    const badge = col.querySelector('.kanban-column__count');
                    if (badge) badge.textContent = count;

                    const body = col.querySelector('.kanban-column__body');
                    const empty = body.querySelector('.empty');
                    if (count === 0 && !empty) {
                        const div = document.createElement('div');
                        div.className = 'empty';
                        div.innerHTML = '<i class="ti ti-inbox"></i><p>وظیفه‌ای نیست</p>';
                        body.appendChild(div);
                    } else if (count > 0 && empty) {
                        empty.remove();
                    }
                });
            }
        }


        /* ==========================================================
           COPY TO CLIPBOARD (profile info rows)
           ========================================================== */
        document.querySelectorAll('[data-copy]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const text = btn.dataset.copy;
                try {
                    await navigator.clipboard.writeText(text);
                    window.showToast?.('کپی شد', 'success');
                    const icon = btn.querySelector('i');
                    const old = icon.className;
                    icon.className = 'ti ti-check';
                    setTimeout(() => icon.className = old, 1200);
                } catch {
                    window.showToast?.('خطا در کپی', 'danger');
                }
            });
        });


        /* ==========================================================
           CHAT UNREAD BADGE (global polling)
           ========================================================== */
        const chatLink = document.querySelector('.sidebar__link[href*="/chat/"]');
        if (chatLink) {
            let lastTotal = 0;
            let currentBadge = chatLink.querySelector('.sidebar__badge');
            const onChatPage = window.location.pathname.startsWith('/chat/');

            function updateBadge(total) {
                if (total > 0) {
                    if (!currentBadge) {
                        currentBadge = document.createElement('span');
                        currentBadge.className = 'sidebar__badge';
                        chatLink.appendChild(currentBadge);
                    }
                    currentBadge.textContent = total;
                    currentBadge.style.display = '';
                } else if (currentBadge) {
                    currentBadge.style.display = 'none';
                }
            }

            async function pollUnread() {
                try {
                    const res = await fetch('/chat/unread/');
                    const data = await res.json();
                    if (!data.ok) return;

                    updateBadge(data.total);

                    if (data.total > lastTotal && !onChatPage && data.details.length) {
                        const first = data.details[0];
                        const msg = first.count === 1
                            ? `پیام جدید از ${first.last_sender}`
                            : `${data.total} پیام خوانده‌نشده جدید`;
                        window.showToast?.(msg, 'info');
                    }
                    lastTotal = data.total;
                } catch (e) {
                    // silent fail
                }
            }

            pollUnread();
            setInterval(pollUnread, 15000);
        }

    }); // end DOMContentLoaded

})();