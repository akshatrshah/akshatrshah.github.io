const navWrap = document.querySelector(".nav-wrap");
const menuButton = document.querySelector(".menu-button");
const navLinks = document.querySelector(".nav-links");

window.addEventListener("scroll", () => {
  navWrap.classList.toggle("scrolled", window.scrollY > 12);
});

menuButton.addEventListener("click", () => {
  const isOpen = navLinks.classList.toggle("open");
  menuButton.setAttribute("aria-expanded", String(isOpen));
});

navLinks.addEventListener("click", (event) => {
  if (event.target.closest("a")) {
    navLinks.classList.remove("open");
    menuButton.setAttribute("aria-expanded", "false");
  }
});

document.querySelector("#year").textContent = new Date().getFullYear();
