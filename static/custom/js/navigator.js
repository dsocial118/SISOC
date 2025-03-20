function GetCurrentSection() {
  let path = window.location.pathname;
  let section = path.split("/")[1];
  console.log("DebugLog section = " + section);
  return section;
}

function StoreCurrentSection() {
  let lastSection = sessionStorage.getItem("currentSection");
  console.log("DebugLog previousSection = " + lastSection);
  let section = GetCurrentSection();
  if (lastSection == null || lastSection != section) {
    sessionStorage.setItem("currentSection", section);
    console.log("DebugLog saved in session = " + sessionStorage.getItem("currentSection"));
    sessionStorage.removeItem("lastUrl");
    console.log("DebugLog lastUrl removed from session");
  }
}

StoreCurrentSection();


document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.link-handler').forEach(item => {
        item.addEventListener('click', event => {
          sessionStorage.setItem("lastUrl", window.location.href);
          console.log("DebugLog lastUrl = " + sessionStorage.getItem("lastUrl"));
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