function getFooterVisiblePixels() {
  const footer = document.querySelector("footer");

  if (!footer) {
    return 0;
  }

  try {
    const rect = footer.getBoundingClientRect();
    const footerHeight =136;
    const viewportHeight = window.innerHeight;

    if (rect.bottom <= 0 || rect.top >= viewportHeight) {
      return 0;
    }

    let visiblePixels =
      rect.top >= 0
        ? Math.min(viewportHeight - rect.top, footerHeight)
        : Math.min(rect.bottom, footerHeight);

    return Math.max(0, Math.round(visiblePixels));
  } catch (error) {
    return 0;
  }
}

function setupScrollListeners() {
  window.addEventListener(
    "scroll",
    () => {
      const visiblePx = getFooterVisiblePixels();
      let sidebarHeight = `calc(100vh - ${visiblePx + 70}px)`;
      const sidebar = document.querySelector(".sidebar-wrapper");
      if (!sidebar) {
        return;
      }
      sidebar.style.height = sidebarHeight;
    },
    { passive: true }
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupScrollListeners);
} else {
  setupScrollListeners();
}
