const form = document.querySelector("#login-form");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const togglePasswordButton = document.querySelector("#toggle-password");
const statusMessage = document.querySelector("#form-status");
const submitButton = form.querySelector('button[type="submit"]');
const errorSlots = {
  email: document.querySelector('[data-error-for="email"]'),
  password: document.querySelector('[data-error-for="password"]'),
};

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function setError(field, message) {
  const input = field === "email" ? emailInput : passwordInput;
  input.classList.toggle("input-error", Boolean(message));
  errorSlots[field].textContent = message;
}

function validate() {
  let valid = true;
  const email = emailInput.value.trim();
  const password = passwordInput.value;

  setError("email", "");
  setError("password", "");

  if (!email) {
    setError("email", "请输入邮箱地址。");
    valid = false;
  } else if (!emailPattern.test(email)) {
    setError("email", "邮箱格式不正确。");
    valid = false;
  }

  if (!password) {
    setError("password", "请输入密码。");
    valid = false;
  } else if (password.length < 8) {
    setError("password", "密码长度至少为 8 位。");
    valid = false;
  }

  return valid;
}

togglePasswordButton.addEventListener("click", () => {
  const isMasked = passwordInput.type === "password";
  passwordInput.type = isMasked ? "text" : "password";
  togglePasswordButton.textContent = isMasked ? "隐藏" : "显示";
  togglePasswordButton.setAttribute("aria-label", isMasked ? "隐藏密码" : "显示密码");
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  statusMessage.textContent = "";

  if (!validate()) {
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "登录中...";
  statusMessage.textContent = "正在验证身份信息，请稍候。";

  window.setTimeout(() => {
    submitButton.disabled = false;
    submitButton.textContent = "登录";
    statusMessage.textContent = "登录请求已提交，正在跳转到工作台。";
  }, 900);
});

emailInput.addEventListener("input", () => {
  if (errorSlots.email.textContent) {
    validate();
  }
});

passwordInput.addEventListener("input", () => {
  if (errorSlots.password.textContent) {
    validate();
  }
});
