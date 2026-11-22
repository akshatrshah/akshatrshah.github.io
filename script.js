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

const quickContactForm = document.querySelector("#quick-contact-form");

if (quickContactForm) {
  quickContactForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = quickContactForm.querySelector('button[type="submit"]');
    const status = quickContactForm.querySelector(".form-status");

    submitButton.disabled = true;
    submitButton.className = "button button-loading";
    submitButton.textContent = "Submitting...";
    status.textContent = "";

    try {
      const response = await fetch(quickContactForm.action, {
        method: "POST",
        headers: { "Accept": "application/json" },
        body: new FormData(quickContactForm)
      });
      const result = await response.json();

      if (!response.ok || result.success === false) {
        throw new Error(result.message || "Submission failed");
      }

      submitButton.className = "button button-success";
      submitButton.textContent = "Submitted";
      status.textContent = "Thanks — looking forward to staying connected.";
      quickContactForm.reset();
    } catch (error) {
      submitButton.disabled = false;
      submitButton.className = "button button-light";
      submitButton.textContent = "Try again";
      status.textContent = "Could not submit right now. Please try again.";
    }
  });
}

