const form = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const formMessage = document.getElementById("formMessage");

function showMessage(message, type) {
  formMessage.textContent = message;
  formMessage.className = `form-message is-visible ${type}`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const email = emailInput.value.trim();
  const password = passwordInput.value.trim();

  if (!email || !password) {
    showMessage("Please fill in both email and password.", "error");
    return;
  }

  if (!email.includes("@")) {
    showMessage("Please enter a valid email address.", "error");
    return;
  }

  if (password.length < 6) {
    showMessage("Password must be at least 6 characters long.", "error");
    return;
  }

  showMessage("Login successful. Redirecting...", "success");
  form.reset();
});
