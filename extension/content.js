// content.js — Repo page + Explore page + Search page badges (GitHub 2025+ DOM compatible)

const API_URL = "http://127.0.0.1:8000/domain";

const STORAGE_KEYS = {
  enabled: "dc_enabled",
  openaiKey: "dc_openai_key",
  githubToken: "dc_github_token",
};

const BADGE_ID_REPO = "dc-domain-badge-repo";
const BADGE_CLASS_LIST = "dc-domain-badge-list";

const DEBUG = false; // 需要排查时改 true
const LOADING_DELAY_MS = 150; // ✅ B 方案：150ms 内返回就不显示 Loading，避免闪烁

function log(...args) {
  if (DEBUG) console.log("[DomainClassifier]", ...args);
}
function warn(...args) {
  console.warn("[DomainClassifier]", ...args);
}

function isGithub() {
  return location.hostname === "github.com";
}

function getPathParts() {
  return location.pathname.split("/").filter(Boolean);
}

function isRepoLikePath() {
  const parts = getPathParts();
  if (parts.length < 2) return false;
  const blacklist = new Set([
    "settings","notifications","login","join","pricing","marketplace",
    "explore","organizations","apps","features","topics","trending",
    "collections","events","sponsors","orgs","search"
  ]);
  if (blacklist.has(parts[0])) return false;
  return true;
}

function isRepoPage() {
  // repo page: /owner/repo[/...]
  return isRepoLikePath();
}

function isExplorePage() {
  // explore + trending + topics等页都属于“列表页”
  const p = location.pathname;
  return (
    p.startsWith("/explore") ||
    p.startsWith("/trending") ||
    p.startsWith("/topics") ||
    p.startsWith("/collections")
  );
}

function isSearchRepoPage() {
  // GitHub 搜索结果页（仓库）
  // /search?q=xxx&type=repositories
  if (!location.pathname.startsWith("/search")) return false;
  const sp = new URLSearchParams(location.search);
  return (sp.get("type") || "").toLowerCase() === "repositories";
}

// ✅ 统一的“列表页”判断：Explore/Trending + Search repositories
function isListPage() {
  return isExplorePage() || isSearchRepoPage();
}

function parseOwnerRepoFromHref(href) {
  // href could be "/owner/repo" or full url
  try {
    const u = href.startsWith("http") ? new URL(href) : new URL(href, location.origin);
    if (u.hostname !== "github.com") return null;

    const parts = u.pathname.split("/").filter(Boolean);
    // ✅ 必须恰好两段：/owner/repo，避免 /username（开发者/用户）被命中
    if (parts.length !== 2) return null;

    const owner = parts[0];
    const repo = parts[1];

    // 过滤一些非 repo href（比如 /settings/...）
    const blacklist = new Set([
      "settings","notifications","login","join","pricing","marketplace",
      "explore","organizations","apps","features","topics","trending",
      "collections","events","sponsors","orgs","search"
    ]);
    if (blacklist.has(owner.toLowerCase())) return null;

    return { owner, repo };
  } catch {
    return null;
  }
}

async function getSettings() {
  return chrome.storage.local.get([
    STORAGE_KEYS.enabled,
    STORAGE_KEYS.openaiKey,
    STORAGE_KEYS.githubToken,
  ]);
}

async function fetchDomain(owner, repo, openaiKey, githubToken) {
  const body = { owner, repo };
  if (openaiKey) body.api_key = openaiKey;
  if (githubToken) body.github_token = githubToken;

  const resp = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `${resp.status} ${resp.statusText}`);
  return data;
}

/* --------------------------
   Request queue (limit concurrency)
-------------------------- */
const MAX_CONCURRENCY = 3;
let inFlight = 0;
const queue = [];

function enqueue(task) {
  return new Promise((resolve, reject) => {
    queue.push({ task, resolve, reject });
    pumpQueue();
  });
}

function pumpQueue() {
  while (inFlight < MAX_CONCURRENCY && queue.length) {
    const { task, resolve, reject } = queue.shift();
    inFlight++;
    Promise.resolve()
      .then(task)
      .then(resolve)
      .catch(reject)
      .finally(() => {
        inFlight--;
        pumpQueue();
      });
  }
}

/* --------------------------
   Badge styles
-------------------------- */
function makeBadge(text, mode = "list") {
  const span = document.createElement("span");
  span.textContent = text;

  // 两种模式：repo 标题 / 列表卡片
  const base = [
    "display:inline-flex",
    "align-items:center",
    "margin-left:8px",
    "padding:2px 8px",
    "border-radius:999px",
    "font-size:12px",
    "font-weight:600",
    "line-height:18px",
    "white-space:nowrap",
    "border:1px solid rgba(27,31,36,.15)",
    "background:rgba(9,105,218,.10)",
    "color:var(--color-accent-fg,#0969da)",
    "vertical-align:middle",
  ];

  // 列表页更紧凑一点
  if (mode === "list") {
    base.push("font-size:11px");
    base.push("padding:1px 7px");
    base.push("line-height:16px");
  }

  span.style.cssText = base.join(";") + ";";
  return span;
}

// ✅ Loading badge 灰色样式
function setBadgeLoadingStyle(badge) {
  badge.style.background = "rgba(175,184,193,.20)";
  badge.style.color = "var(--color-fg-muted,#57606a)";
}

// ✅ 恢复正常 badge 样式（用于把 Loading 变回最终样式）
function setBadgeNormalStyle(badge) {
  badge.style.background = "rgba(9,105,218,.10)";
  badge.style.color = "var(--color-accent-fg,#0969da)";
}

/* --------------------------
   Repo page: insert next to repo link
-------------------------- */
function removeRepoBadge() {
  document.getElementById(BADGE_ID_REPO)?.remove();
}

function findRepoTitleLink() {
  // 找 href="/owner/repo" 的链接，并且在 h1 里优先
  const parts = getPathParts();
  if (parts.length < 2) return null;
  const href = `/${parts[0]}/${parts[1]}`;

  const links = Array.from(document.querySelectorAll(`a[href="${href}"]`));
  if (!links.length) return null;

  for (const a of links) {
    if (a.closest("h1")) return a;
  }
  return links[0];
}

async function renderRepoBadgeIfNeeded(settings) {
  if (!isRepoPage()) {
    removeRepoBadge();
    return;
  }

  const enabled = Boolean(settings[STORAGE_KEYS.enabled]);
  if (!enabled) {
    removeRepoBadge();
    return;
  }

  const parts = getPathParts();
  if (parts.length < 2) return;
  const owner = parts[0];
  const repo = parts[1];
  const key = `${owner}/${repo}`;

  const anchor = findRepoTitleLink();
  if (!anchor) return;

  // 已存在且同仓库就不重复
  const existing = document.getElementById(BADGE_ID_REPO);
  if (existing && existing.dataset.key === key) return;

  // 缓存
  const cacheKey = `dc_cache_${key}`;
  const cached = sessionStorage.getItem(cacheKey);

  const getData = async () => {
    if (cached) return JSON.parse(cached);
    const data = await fetchDomain(
      owner,
      repo,
      settings[STORAGE_KEYS.openaiKey] || "",
      settings[STORAGE_KEYS.githubToken] || ""
    );
    sessionStorage.setItem(cacheKey, JSON.stringify(data));
    return data;
  };

  // ✅ B 方案：150ms 内返回就不显示 Loading
  removeRepoBadge();

  const taskPromise = enqueue(getData);
  let loadingTimer = null;

  loadingTimer = setTimeout(() => {
    // 页面可能已经变化：再次确认
    const nowAnchor = findRepoTitleLink();
    if (!nowAnchor) return;

    // 如果已经有 badge 就不重复插入
    const ex = document.getElementById(BADGE_ID_REPO);
    if (ex) return;

    const badge = makeBadge("⏳ Loading…", "repo");
    badge.id = BADGE_ID_REPO;
    badge.dataset.key = key;
    setBadgeLoadingStyle(badge);
    nowAnchor.insertAdjacentElement("afterend", badge);
  }, LOADING_DELAY_MS);

  try {
    const data = await taskPromise;
    clearTimeout(loadingTimer);

    const domain = (data?.result || "").toString().trim();

    // 如果没结果：移除可能存在的 loading
    if (!domain) {
      document.getElementById(BADGE_ID_REPO)?.remove();
      return;
    }

    // 优先更新现有（loading）badge；否则直接插入最终 badge
    const ex = document.getElementById(BADGE_ID_REPO);
    if (ex && ex.dataset.key === key) {
      ex.textContent = domain;
      setBadgeNormalStyle(ex);
      return;
    }

    const nowAnchor = findRepoTitleLink();
    if (!nowAnchor) return;

    const badge = makeBadge(domain, "repo");
    badge.id = BADGE_ID_REPO;
    badge.dataset.key = key;
    nowAnchor.insertAdjacentElement("afterend", badge);
  } catch (e) {
    clearTimeout(loadingTimer);
    warn("repo badge failed:", e);
    document.getElementById(BADGE_ID_REPO)?.remove();
  }
}

/* --------------------------
   List pages (Explore/Search repositories): add badge next to each repo link
   - only for repo links that look like "/owner/repo" (exactly 2 segments)
   - only when the link is visible (IntersectionObserver)
-------------------------- */
const seenLinks = new WeakSet();
let io = null;

function ensureIntersectionObserver(settings) {
  if (io) return io;

  io = new IntersectionObserver(
    (entries) => {
      for (const ent of entries) {
        if (!ent.isIntersecting) continue;
        const link = ent.target;
        io.unobserve(link);

        // 如果扩展开关关了就不做
        if (!settings[STORAGE_KEYS.enabled]) continue;

        decorateRepoLinkInList(link, settings);
      }
    },
    { root: null, rootMargin: "200px 0px 200px 0px", threshold: 0.01 }
  );

  return io;
}

function hasListBadge(link, key) {
  const next = link.nextElementSibling;
  return next && next.classList.contains(BADGE_CLASS_LIST) && next.dataset.key === key;
}

function isLikelyRepoTitleLink(link) {
  const href = link.getAttribute("href") || "";
  const info = parseOwnerRepoFromHref(href);
  if (!info) return false;

  // ✅ Search 页面会出现很多操作链接，GitHub 仓库标题链接一般带 hovercard-type="repository"
  //    但有时没有，所以我们用“严格 href + 文本过滤”双保险
  const text = (link.textContent || "").trim();
  if (!text) return false;

  // 排除一些常见非标题链接
  const badTexts = new Set(["Issues", "Pull requests", "Discussions", "Code", "Marketplace"]);
  if (badTexts.has(text)) return false;

  // ✅ 排除用户/组织 hovercard（避免 developer / users）
  const ht = (link.getAttribute("data-hovercard-type") || "").toLowerCase();
  if (ht === "user" || ht === "organization") return false;

  return true;
}

async function decorateRepoLinkInList(link, settings) {
  const href = link.getAttribute("href") || "";
  const info = parseOwnerRepoFromHref(href);
  if (!info) return;

  const key = `${info.owner}/${info.repo}`;

  // 已有 badge 就不重复
  if (hasListBadge(link, key)) return;

  // 缓存
  const cacheKey = `dc_cache_${key}`;
  const cached = sessionStorage.getItem(cacheKey);

  const getData = async () => {
    if (cached) return JSON.parse(cached);
    const data = await fetchDomain(
      info.owner,
      info.repo,
      settings[STORAGE_KEYS.openaiKey] || "",
      settings[STORAGE_KEYS.githubToken] || ""
    );
    sessionStorage.setItem(cacheKey, JSON.stringify(data));
    return data;
  };

  // ✅ B 方案：150ms 内返回就不显示 Loading
  const taskPromise = enqueue(getData);
  let loadingTimer = null;

  loadingTimer = setTimeout(() => {
    // 仍然没有 badge 才插入 loading
    if (hasListBadge(link, key)) return;

    const badge = makeBadge("⏳ Loading…", "list");
    badge.classList.add(BADGE_CLASS_LIST);
    badge.dataset.key = key;
    setBadgeLoadingStyle(badge);

    // link 可能已被移除
    if (!link.isConnected) return;

    link.insertAdjacentElement("afterend", badge);
  }, LOADING_DELAY_MS);

  try {
    const data = await taskPromise;
    clearTimeout(loadingTimer);

    const domain = (data?.result || "").toString().trim();

    // 找到 badge（可能是 loading 或不存在）
    const next = link.nextElementSibling;
    const isOurBadge =
      next && next.classList && next.classList.contains(BADGE_CLASS_LIST) && next.dataset.key === key;

    if (!domain) {
      // 无结果：删掉可能存在的 loading
      if (isOurBadge) next.remove();
      return;
    }

    if (isOurBadge) {
      // 有 loading：更新文本 + 样式
      next.textContent = domain;
      setBadgeNormalStyle(next);
      return;
    }

    // 没有 loading：直接插入最终 badge（并发下再次检查）
    if (hasListBadge(link, key)) return;

    const badge = makeBadge(domain, "list");
    badge.classList.add(BADGE_CLASS_LIST);
    badge.dataset.key = key;

    if (!link.isConnected) return;
    link.insertAdjacentElement("afterend", badge);
  } catch (e) {
    clearTimeout(loadingTimer);
    warn("list badge failed:", e, key);

    // 出错移除可能存在的 loading
    const next = link.nextElementSibling;
    if (next && next.classList?.contains(BADGE_CLASS_LIST) && next.dataset.key === key) {
      next.remove();
    }
  }
}

function scanListLinksAndObserve(settings) {
  // ✅ 现在 Explore + Search repositories 都会走这里
  if (!isListPage()) return;

  const enabled = Boolean(settings[STORAGE_KEYS.enabled]);
  if (!enabled) {
    document.querySelectorAll(`.${BADGE_CLASS_LIST}`).forEach((n) => n.remove());
    return;
  }

  const observer = ensureIntersectionObserver(settings);

  // ✅ 优先只扫 repo hovercard 链接（更准，误伤更少）
  const primary = Array.from(document.querySelectorAll('a[data-hovercard-type="repository"]'));

  // ✅ fallback：所有 / 开头链接里挑 /owner/repo
  const fallback = Array.from(document.querySelectorAll('a[href^="/"]'));

  const links = [...primary, ...fallback];

  for (const link of links) {
    if (seenLinks.has(link)) continue;
    if (!isLikelyRepoTitleLink(link)) continue;

    seenLinks.add(link);
    observer.observe(link);
  }
}

/* --------------------------
   Orchestration: init + mutations + storage changes
-------------------------- */
let settingsCache = null;

async function refreshAll(trigger = "init") {
  if (!isGithub()) return;

  settingsCache = await getSettings();

  // Repo page badge
  await renderRepoBadgeIfNeeded(settingsCache);

  // List badges (Explore + Search repositories)
  scanListLinksAndObserve(settingsCache);

  log("refreshed", trigger, {
    path: location.pathname,
    enabled: Boolean(settingsCache[STORAGE_KEYS.enabled]),
  });
}

function debounce(fn, t = 250) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), t);
  };
}

const debouncedRefresh = debounce(() => refreshAll("mutation"), 250);

// 初次运行
refreshAll("init");

// 监听 DOM 变化（GitHub PJAX/动态渲染）
const mo = new MutationObserver(() => {
  debouncedRefresh();
});
mo.observe(document.documentElement, { childList: true, subtree: true });

// 监听设置变化（开关、token）
chrome.storage.onChanged.addListener((_changes, area) => {
  if (area !== "local") return;

  removeRepoBadge();
  document.querySelectorAll(`.${BADGE_CLASS_LIST}`).forEach((n) => n.remove());

  refreshAll("storage_changed");
});
