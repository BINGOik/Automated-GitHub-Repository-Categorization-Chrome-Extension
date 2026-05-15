const STORAGE_KEYS = {
  enabled: "dc_enabled",
  openaiKey: "dc_openai_key",
  githubToken: "dc_github_token"
};

function $(id) {
  return document.getElementById(id);
}

function show(el) {
  el.classList.add("show");
}
function hide(el) {
  el.classList.remove("show");
}

async function getSettings() {
  return await chrome.storage.local.get([
    STORAGE_KEYS.enabled,
    STORAGE_KEYS.openaiKey,
    STORAGE_KEYS.githubToken
  ]);
}

async function setSettings(obj) {
  return await chrome.storage.local.set(obj);
}

document.addEventListener("DOMContentLoaded", async () => {
  const mainPanel = $("mainPanel");
  const settingsPanel = $("settingsPanel");

  const enabledToggle = $("enabledToggle");
  const settingsBtn = $("settingsBtn");

  const openaiKeyInput = $("openaiKey");
  const githubTokenInput = $("githubToken");

  const saveBtn = $("saveBtn");
  const backBtn = $("backBtn");
  const okMsg = $("okMsg");
  const errMsg = $("errMsg");

  const s = await getSettings();

  enabledToggle.checked = Boolean(s[STORAGE_KEYS.enabled]);
  openaiKeyInput.value = s[STORAGE_KEYS.openaiKey] || "";
  githubTokenInput.value = s[STORAGE_KEYS.githubToken] || "";

  enabledToggle.addEventListener("change", async () => {
    await setSettings({ [STORAGE_KEYS.enabled]: enabledToggle.checked });
    // 可选：提示用户刷新页面
  });

  settingsBtn.addEventListener("click", async () => {
    // 切到设置页时，重新读取一次（避免多窗口不同步）
    const ss = await getSettings();
    openaiKeyInput.value = ss[STORAGE_KEYS.openaiKey] || "";
    githubTokenInput.value = ss[STORAGE_KEYS.githubToken] || "";

    hide(mainPanel);
    show(settingsPanel);
    okMsg.style.display = "none";
    errMsg.style.display = "none";
  });

  backBtn.addEventListener("click", () => {
    hide(settingsPanel);
    show(mainPanel);
    okMsg.style.display = "none";
    errMsg.style.display = "none";
  });

  saveBtn.addEventListener("click", async () => {
    okMsg.style.display = "none";
    errMsg.style.display = "none";

    const openaiKey = openaiKeyInput.value.trim();
    const githubToken = githubTokenInput.value.trim();

    try {
      await setSettings({
        [STORAGE_KEYS.openaiKey]: openaiKey,
        [STORAGE_KEYS.githubToken]: githubToken
      });
      okMsg.style.display = "block";
    } catch (e) {
      errMsg.textContent = "保存失败：" + (e?.message || String(e));
      errMsg.style.display = "block";
    }
  });
});
