(function() {
    "use strict";

    function isDesktopViewport() {
        return window.matchMedia("(min-width: 992px)").matches;
    }

    function simplifySingleOptionGroups(scope) {
        scope.querySelectorAll(".nav-item").forEach((item) => {
            const parentLink = item.querySelector(":scope > .nav-link");
            const submenu = item.querySelector(":scope > .nav-treeview");

            if (!parentLink || !submenu) {
                return;
            }

            const submenuItems = submenu.querySelectorAll(":scope > .nav-item");
            if (submenuItems.length !== 1) {
                return;
            }

            const onlyItem = submenuItems[0];
            const directLinks = onlyItem.querySelectorAll(":scope > .nav-link");
            const nestedTree = onlyItem.querySelector(":scope > .nav-treeview");

            if (directLinks.length !== 1 || nestedTree) {
                return;
            }

            const childLink = directLinks[0];
            const href = childLink.getAttribute("href");
            if (!href || href === "#") {
                return;
            }

            parentLink.setAttribute("href", href);
            parentLink.classList.toggle("active", childLink.classList.contains("active"));

            const arrow = parentLink.querySelector(".nav-arrow");
            if (arrow) {
                arrow.remove();
            }

            submenu.remove();
            item.classList.remove("menu-open");
        });
    }

    function closeAllMenus(exceptItem) {
        document.querySelectorAll(".sisoc-topbar-menu > .nav-item.is-open").forEach((item) => {
            if (item !== exceptItem) {
                item.classList.remove("is-open");
            }
        });
    }

    function bindTopbarMenu() {
        document.querySelectorAll(".sidebar-menu").forEach((menuRoot) => {
            simplifySingleOptionGroups(menuRoot);
        });

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
