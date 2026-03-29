$.widget.bridge("uibutton", $.ui.button);

(function($) {
    "use strict";

    const THEME_STORAGE_KEY = "theme";
    const FORCED_THEME = "dark";
    const DARK_CLASS = "dark-mode";
    let updatingThemeAttr = false;

    function getStoredTheme() {
        try {
            return localStorage.getItem(THEME_STORAGE_KEY);
        } catch (error) {
            return null;
        }
    }

    function storeTheme(value) {
        try {
            localStorage.setItem(THEME_STORAGE_KEY, FORCED_THEME);
        } catch (error) {
            // Sin almacenamiento disponible, no persistimos la preferencia.
        }
    }

    function prefersDark() {
        if (typeof window.matchMedia !== "function") {
            return false;
        }
        return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    function resolveTheme(theme) {
        return FORCED_THEME;
    }

    function updateDarkModeIcon(isDark) {
        const icon = $("#darkmode_icon");
        if (!icon.length) {
            return;
        }
        icon.addClass("fas")
            .removeClass("far")
            .attr("title", "Modo oscuro activo");
    }

    function setBodyThemeClass(theme) {
        const isDark = theme === "dark";
        $("body").toggleClass(DARK_CLASS, isDark);
        updateDarkModeIcon(isDark);
    }

    function getCSRFToken() {
        const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function sendThemePreference(isDark) {
        $.ajax({
            url: "/set_dark_mode/",
            type: "POST",
            headers: (function() {
                const token = getCSRFToken();
                return token ? {"X-CSRFToken": token} : {};
            })(),
            data: {"dark_mode": isDark},
        }).fail(function(error) {
            console.warn("No se pudo sincronizar la preferencia de modo oscuro.", error);
        });
    }

    function applyTheme(theme, options) {
        const settings = $.extend({persist: true, notify: false}, options);
        const resolved = resolveTheme(theme);

        updatingThemeAttr = true;
        document.documentElement.setAttribute("data-bs-theme", resolved);
        updatingThemeAttr = false;

        setBodyThemeClass(resolved);

        if (settings.persist) {
            storeTheme(resolved);
        }

        if (settings.notify) {
            sendThemePreference(true);
        }
    }

    function synchronizeFromRootAttr() {
        const rootTheme = document.documentElement.getAttribute("data-bs-theme") || FORCED_THEME;
        if (rootTheme !== FORCED_THEME) {
            applyTheme(FORCED_THEME, {persist: true, notify: false});
            return;
        }
        setBodyThemeClass(FORCED_THEME);
        storeTheme(FORCED_THEME);
    }

    function initializeTheme() {
        applyTheme(FORCED_THEME, {persist: true, notify: false});
    }

    initializeTheme();

    const rootObserver = new MutationObserver(function(mutations) {
        if (updatingThemeAttr) {
            return;
        }
        mutations.forEach(function(mutation) {
            if (mutation.type === "attributes" && mutation.attributeName === "data-bs-theme") {
                synchronizeFromRootAttr();
            }
        });
    });

    rootObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-bs-theme"],
    });

    window.addEventListener("storage", function(event) {
        if (event.key === THEME_STORAGE_KEY) {
            applyTheme(FORCED_THEME, {persist: true, notify: false});
        }
    });

    if (typeof window.matchMedia === "function") {
        const colorSchemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const handleColorSchemeChange = function() {
            applyTheme(FORCED_THEME, {persist: true, notify: false});
        };

        if (typeof colorSchemeQuery.addEventListener === "function") {
            colorSchemeQuery.addEventListener("change", handleColorSchemeChange);
        } else if (typeof colorSchemeQuery.addListener === "function") {
            colorSchemeQuery.addListener(handleColorSchemeChange);
        }
    }

    function resolveGlobalFunction(functionName) {
        if (!functionName) {
            return null;
        }

        return functionName.split(".").reduce(function(ctx, part) {
            if (ctx && typeof ctx[part] !== "undefined") {
                return ctx[part];
            }
            return null;
        }, window);
    }

    function parseDataCallArgs(element) {
        const rawArgs = element.getAttribute("data-call-args");
        if (!rawArgs) {
            return [];
        }

        try {
            const parsed = JSON.parse(rawArgs);
            return Array.isArray(parsed) ? parsed : [parsed];
        } catch (error) {
            console.warn("No se pudieron parsear los argumentos de data-call-args.", {
                element: element,
                rawArgs: rawArgs,
                error: error,
            });
            return [];
        }
    }

    function invokeDataCall(element, attrName) {
        const functionName = element.getAttribute(attrName);
        const targetFn = resolveGlobalFunction(functionName);

        if (typeof targetFn !== "function") {
            console.warn("No se encontró la función global para data-call.", {
                attrName: attrName,
                functionName: functionName,
                element: element,
            });
            return undefined;
        }

        let args = parseDataCallArgs(element);
        if (element.getAttribute("data-call-pass-this") === "true") {
            args = [element].concat(args);
        }

        try {
            return targetFn.apply(window, args);
        } catch (error) {
            console.error("Error ejecutando función declarada con data-call.", {
                attrName: attrName,
                functionName: functionName,
                args: args,
                error: error,
            });
            throw error;
        }
    }

    $(function() {
        const logoutIcon = $("#logout_icon");
        if (logoutIcon.length) {
            logoutIcon.hover(
                function() {
                    $(this).addClass("text-danger").removeClass("text-success");
                },
                function() {
                    $(this).addClass("text-success").removeClass("text-danger");
                },
            );
        }

        const darkModeToggle = $("#darkmode");
        if (darkModeToggle.length) {
            darkModeToggle.on("click", function(event) {
                event.preventDefault();
                applyTheme(FORCED_THEME, {persist: true, notify: true});
            });
        } else {
            updateDarkModeIcon(document.body.classList.contains(DARK_CLASS));
        }

        const sidebarMenu = $(".app-sidebar");
        const sidebarToggleMobileButton = document.querySelector(
            "[data-lte-toggle=\"sidebar\"].d-lg-none",
        );
        const sidebarToggleDesktopButton = document.querySelector(
            "[data-lte-toggle=\"sidebar\"]:not(.d-lg-none)",
        );

        function isDesktopSidebarViewport() {
            if (!sidebarToggleMobileButton) {
                return window.innerWidth >= 992;
            }
            const styles = window.getComputedStyle(sidebarToggleMobileButton);
            return styles.display === "none";
        }

        function preservesDesktopSidebarCollapse() {
            if (!sidebarToggleDesktopButton) {
                return false;
            }

            const styles = window.getComputedStyle(sidebarToggleDesktopButton);
            return styles.display !== "none";
        }

        function hideMenuOpenULs() {
            if ($("body").hasClass("sidebar-collapse")) {
                $(".sidebar-menu .nav-item.menu-open>ul").css("display", "none");
            }
        }

        function showMenuOpenULs() {
            if ($("body").hasClass("sidebar-collapse")) {
                $(".sidebar-menu .nav-item.menu-open>ul").css("display", "block");
            }
        }

        hideMenuOpenULs();

        const sidebarObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === "attributes" && mutation.attributeName === "class") {
                    hideMenuOpenULs();
                }
            });
        });

        sidebarObserver.observe(document.body, {attributes: true});

        sidebarMenu.on("mouseenter", function() {
            showMenuOpenULs();
        });

        sidebarMenu.on("mouseleave", function() {
            hideMenuOpenULs();
        });

        const sidebarElement = document.querySelector("[data-lte-toggle=\"sidebar\"]");
        if (sidebarElement) {
            sidebarElement.addEventListener("open.lte.push-menu", function() {
                $(".sidebar-menu .nav-item.menu-open>ul").css("display", "block");
            });
        }

        function syncSidebarWithToggleVisibility() {
            if (!isDesktopSidebarViewport()) {
                return;
            }

            const body = $("body");
            body.removeClass("sidebar-open");
            if (!preservesDesktopSidebarCollapse()) {
                body.removeClass("sidebar-collapse");
            }
            $(".app-sidebar").removeClass("show sidebar-open").css("margin-left", "");
            $(".sidebar-overlay").remove();
        }

        window.addEventListener("resize", function() {
            window.setTimeout(syncSidebarWithToggleVisibility, 0);
        });

        syncSidebarWithToggleVisibility();

        $(document).on("click", "[data-history-back]", function(event) {
            event.preventDefault();
            window.history.back();
        });

        $(document).on("click", "[data-confirm-click]", function(event) {
            const message = $(this).attr("data-confirm-click") || "¿Confirmar acción?";
            if (!window.confirm(message)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });

        $(document).on("submit", "form[data-confirm-submit]", function(event) {
            const message = $(this).attr("data-confirm-submit") || "¿Confirmar envío?";
            if (!window.confirm(message)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });

        $(document).on("click", "[data-page-reload]", function(event) {
            event.preventDefault();
            window.location.reload();
        });

        $(document).on("click", "[data-click-target-id]", function(event) {
            event.preventDefault();
            const targetId = $(this).attr("data-click-target-id");
            if (!targetId) {
                return;
            }
            const target = document.getElementById(targetId);
            if (target && typeof target.click === "function") {
                target.click();
            }
        });

        $(document).on("click", "[data-call-click]", function(event) {
            const result = invokeDataCall(this, "data-call-click");
            if (result === false) {
                event.preventDefault();
                event.stopPropagation();
            }
        });

        $(document).on("change", "[data-call-change]", function(event) {
            const result = invokeDataCall(this, "data-call-change");
            if (result === false) {
                event.preventDefault();
                event.stopPropagation();
            }
        });

        $(document).on("submit", "form[data-call-submit]", function(event) {
            const result = invokeDataCall(this, "data-call-submit");
            if (result === false) {
                event.preventDefault();
                event.stopPropagation();
            }
        });

        $(document).on("click", "[data-toggle-section]", function() {
            const section = $(this).attr("data-toggle-section");
            if (typeof window.toggleSection === "function") {
                window.toggleSection(section);
            }
        });

        $(document).on("click", "[data-toggle-section-ciudadano]", function() {
            const section = $(this).attr("data-toggle-section-ciudadano");
            if (typeof window.toggleSectionCiudadano === "function") {
                window.toggleSectionCiudadano(section);
            }
        });

        $(document).on("keyup", "[data-filter-table-on-keyup]", function() {
            if (typeof window.filterTable === "function") {
                window.filterTable();
            }
        });

        $(document).on("change", "[data-auto-submit-on-change]", function() {
            const mode = $(this).attr("data-auto-submit-on-change");
            if (mode === "disable") {
                this.disabled = true;
            }
            if (this.form) {
                this.form.submit();
            }
        });

        $(document).on("click", "[data-submit-with-spinner]", function(event) {
            const form = this.form;
            if (!form) {
                return;
            }
            event.preventDefault();
            if (this.disabled) {
                return;
            }

            const message = $(this).attr("data-submit-with-spinner") || "Procesando…";
            this.disabled = true;
            this.innerHTML = "<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span> " + message;
            form.submit();
        });
    });
})(jQuery);

window.mostrarRespuesta = function() {
    const selectElement = document.getElementById("id_nombre3");
    const respuestaDetalle = document.getElementById("respuestaDetalle");

    if (!selectElement || !respuestaDetalle) {
        return;
    }

    const selectedValue = selectElement.value;
    if (selectedValue === "Vos sola") {
        respuestaDetalle.innerText = "Vos sola";
    } else if (selectedValue === "Vos con tu pareja") {
        respuestaDetalle.innerText = "Vos con tu pareja";
    } else if (selectedValue === "Tu pareja sola") {
        respuestaDetalle.innerText = "Tu pareja sola";
    } else {
        respuestaDetalle.innerText = "";
    }
};
