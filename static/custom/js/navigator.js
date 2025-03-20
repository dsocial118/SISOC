function GetCurrentSection() {
  let path = window.location.pathname;
  let section = path.split("/")[1];
  return section;
}

function StoreCurrentSection() {
  let lastSection = sessionStorage.getItem("currentSection");
  let section = GetCurrentSection();
  if (lastSection == null || lastSection != section) {
    sessionStorage.setItem("currentSection", section);
    sessionStorage.removeItem("lastUrl");
  }
}

StoreCurrentSection();


document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.link-handler').forEach(item => {
        item.addEventListener('click', event => {
          sessionStorage.setItem("lastUrl", window.location.href);
        })
      });
      
      document.querySelectorAll('.backbutton-handler').forEach(item => {
        let lastUrl = sessionStorage.getItem("lastUrl");
        if(lastUrl != null)
        {
            item.setAttribute("href", sessionStorage.getItem("lastUrl"));
        }
      });
});