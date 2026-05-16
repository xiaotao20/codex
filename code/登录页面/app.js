const form = document.querySelector("#login-form");
const workspaceInput = document.querySelector("#workspace");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const togglePasswordButton = document.querySelector("#toggle-password");
const statusMessage = document.querySelector("#form-status");
const submitButton = document.querySelector("#submit-button");
const strengthLabel = document.querySelector("#password-strength");
const strengthBar = document.querySelector("#strength-bar");
const cursorGlow = document.querySelector(".cursor-glow");
const sceneCanvas = document.querySelector("#scene-canvas");
const panels = document.querySelectorAll(".experience-panel, .auth-panel");
const errorSlots = {
  workspace: document.querySelector('[data-error-for="workspace"]'),
  email: document.querySelector('[data-error-for="email"]'),
  password: document.querySelector('[data-error-for="password"]'),
};

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const passwordPhases = [
  "正在建立安全隧道...",
  "正在同步组织策略...",
  "身份签名已通过，正在进入控制台...",
];

function wait(duration) {
  return new Promise((resolve) => window.setTimeout(resolve, duration));
}

function setError(field, message) {
  const inputMap = {
    workspace: workspaceInput,
    email: emailInput,
    password: passwordInput,
  };

  inputMap[field].classList.toggle("input-error", Boolean(message));
  errorSlots[field].textContent = message;
}

function getPasswordStrength(password) {
  if (!password) {
    return { label: "未输入", ratio: 0 };
  }

  let score = 0;

  if (password.length >= 8) {
    score += 1;
  }

  if (password.length >= 12) {
    score += 1;
  }

  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) {
    score += 1;
  }

  if (/\d/.test(password)) {
    score += 1;
  }

  if (/[^A-Za-z0-9]/.test(password)) {
    score += 1;
  }

  if (score <= 1) {
    return { label: "偏弱", ratio: 0.24 };
  }

  if (score <= 3) {
    return { label: "中等", ratio: 0.58 };
  }

  if (score === 4) {
    return { label: "较强", ratio: 0.82 };
  }

  return { label: "很强", ratio: 1 };
}

function updatePasswordStrength() {
  const { label, ratio } = getPasswordStrength(passwordInput.value);
  strengthLabel.textContent = label;
  strengthBar.style.width = `${ratio * 100}%`;
}

function validate() {
  let valid = true;

  const workspace = workspaceInput.value.trim();
  const email = emailInput.value.trim();
  const password = passwordInput.value;

  setError("workspace", "");
  setError("email", "");
  setError("password", "");

  if (!workspace) {
    setError("workspace", "请输入工作区标识。");
    valid = false;
  } else if (workspace.length < 4) {
    setError("workspace", "工作区至少需要 4 个字符。");
    valid = false;
  }

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
  } else if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    setError("password", "密码需同时包含字母和数字。");
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusMessage.textContent = "";

  if (!validate()) {
    return;
  }

  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "身份校验中";

  for (const [index, phase] of passwordPhases.entries()) {
    statusMessage.textContent = phase;
    await wait(index === passwordPhases.length - 1 ? 850 : 620);
  }

  submitButton.disabled = false;
  submitButton.querySelector("span").textContent = "进入控制台";
  statusMessage.textContent = "登录请求已通过，正在为你打开工作台。";
});

[workspaceInput, emailInput, passwordInput].forEach((input) => {
  input.addEventListener("input", () => {
    if (input === passwordInput) {
      updatePasswordStrength();
    }

    const hasErrors = Object.values(errorSlots).some((slot) => slot.textContent);

    if (hasErrors) {
      validate();
    }
  });
});

function applyPanelTilt(event) {
  const { innerWidth, innerHeight } = window;
  const pointerX = (event.clientX / innerWidth) * 100;
  const pointerY = (event.clientY / innerHeight) * 100;

  document.documentElement.style.setProperty("--pointer-x", `${pointerX}%`);
  document.documentElement.style.setProperty("--pointer-y", `${pointerY}%`);
  cursorGlow.style.opacity = "1";

  panels.forEach((panel) => {
    const rect = panel.getBoundingClientRect();
    const offsetX = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const offsetY = ((event.clientY - rect.top) / rect.height - 0.5) * 2;

    if (
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom
    ) {
      panel.style.transform = `perspective(1400px) rotateX(${-offsetY * 3.4}deg) rotateY(${offsetX * 4.2}deg) translateY(-4px)`;
      panel.classList.add("panel-floating");
    } else {
      panel.style.transform = "perspective(1400px) rotateX(0deg) rotateY(0deg) translateY(0)";
      panel.classList.remove("panel-floating");
    }
  });
}

function resetPanelTilt() {
  cursorGlow.style.opacity = "0.9";
  panels.forEach((panel) => {
    panel.style.transform = "perspective(1400px) rotateX(0deg) rotateY(0deg) translateY(0)";
    panel.classList.remove("panel-floating");
  });
}

const sceneContext = sceneCanvas.getContext("2d");
let animationFrameId = 0;
let nodes = [];
let canvasWidth = 0;
let canvasHeight = 0;
let devicePixelRatioValue = 1;
let lastRenderTime = 0;
const targetFrameDuration = 1000 / 30;

function createNodes() {
  const count = Math.max(14, Math.min(22, Math.floor((canvasWidth * canvasHeight) / 60000)));
  nodes = Array.from({ length: count }, () => ({
    x: Math.random() * canvasWidth,
    y: Math.random() * canvasHeight,
    vx: (Math.random() - 0.5) * 0.18,
    vy: (Math.random() - 0.5) * 0.18,
    radius: Math.random() * 1.6 + 0.8,
  }));
}

function resizeCanvas() {
  devicePixelRatioValue = window.devicePixelRatio || 1;
  canvasWidth = window.innerWidth;
  canvasHeight = window.innerHeight;

  sceneCanvas.width = canvasWidth * devicePixelRatioValue;
  sceneCanvas.height = canvasHeight * devicePixelRatioValue;
  sceneCanvas.style.width = `${canvasWidth}px`;
  sceneCanvas.style.height = `${canvasHeight}px`;
  sceneContext.setTransform(devicePixelRatioValue, 0, 0, devicePixelRatioValue, 0, 0);

  createNodes();
}

function drawScene(timestamp = 0) {
  if (timestamp - lastRenderTime < targetFrameDuration) {
    animationFrameId = window.requestAnimationFrame(drawScene);
    return;
  }

  lastRenderTime = timestamp;
  sceneContext.clearRect(0, 0, canvasWidth, canvasHeight);

  const scanGradient = sceneContext.createLinearGradient(0, 0, canvasWidth, canvasHeight);
  scanGradient.addColorStop(0, "rgba(102, 231, 220, 0.08)");
  scanGradient.addColorStop(0.45, "rgba(102, 231, 220, 0)");
  scanGradient.addColorStop(1, "rgba(240, 169, 111, 0.08)");

  sceneContext.fillStyle = scanGradient;
  sceneContext.fillRect(0, 0, canvasWidth, canvasHeight);

  for (const node of nodes) {
    node.x += node.vx;
    node.y += node.vy;

    if (node.x <= -30 || node.x >= canvasWidth + 30) {
      node.vx *= -1;
    }

    if (node.y <= -30 || node.y >= canvasHeight + 30) {
      node.vy *= -1;
    }
  }

  for (let index = 0; index < nodes.length; index += 1) {
    const first = nodes[index];

    for (let innerIndex = index + 1; innerIndex < nodes.length; innerIndex += 1) {
      const second = nodes[innerIndex];
      const distanceX = first.x - second.x;
      const distanceY = first.y - second.y;
      const distance = Math.hypot(distanceX, distanceY);

      if (distance < 168) {
        sceneContext.strokeStyle = `rgba(102, 231, 220, ${0.14 - distance / 1500})`;
        sceneContext.lineWidth = 1;
        sceneContext.beginPath();
        sceneContext.moveTo(first.x, first.y);
        sceneContext.lineTo(second.x, second.y);
        sceneContext.stroke();
      }
    }
  }

  for (const node of nodes) {
    sceneContext.beginPath();
    sceneContext.fillStyle = "rgba(214, 255, 248, 0.85)";
    sceneContext.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    sceneContext.fill();
  }

  animationFrameId = window.requestAnimationFrame(drawScene);
}

window.addEventListener("mousemove", applyPanelTilt);
window.addEventListener("mouseleave", resetPanelTilt);
window.addEventListener("resize", () => {
  window.cancelAnimationFrame(animationFrameId);
  resizeCanvas();
  drawScene();
});

updatePasswordStrength();
resizeCanvas();
drawScene();
