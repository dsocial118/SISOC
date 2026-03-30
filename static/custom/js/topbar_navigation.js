(function() {
    "use strict";

    function isDesktopViewport() {
        return window.matchMedia("(min-width: 992px)").matches;
    }

    function closeAllMenus(exceptItem) {
        document.querySelectorAll(".sisoc-topbar-menu > .nav-item.is-open").forEach((item) => {
            if (item !== exceptItem) {
                item.classList.remove("is-open");
            }
        });
    }

    function bindTopbarMenu() {
        const menu = document.querySelector(".sisoc-topbar-menu");
        if (!menu) {
            return;
        }

        menu.querySelectorAll(":scope > .nav-item").forEach((item) => {
            const toggle = item.querySelector(":scope > .nav-link");
            const submenu = item.querySelector(":scope > .nav-treeview");

            if (item.querySelector(".nav-treeview .nav-link.active")) {
                item.classList.add("is-current");
            }

            if (!toggle || !submenu) {
                return;
            }

            toggle.addEventListener("click", (event) => {
                if (!isDesktopViewport()) {
                    return;
                }

                const href = toggle.getAttribute("href");
                if (href && href !== "#") {
                    return;
                }

                event.preventDefault();
                const willOpen = !item.classList.contains("is-open");
                closeAllMenus(item);
                item.classList.toggle("is-open", willOpen);
            });
        });

        document.addEventListener("click", (event) => {
            if (!menu.contains(event.target)) {
                closeAllMenus();
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeAllMenus();
            }
        });

        window.addEventListener("resize", () => {
            if (!isDesktopViewport()) {
                closeAllMenus();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", bindTopbarMenu);
})();
