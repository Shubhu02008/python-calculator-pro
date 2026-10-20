(() => {
  const API_BASE_URL = (window.CALCULATOR_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
  const HISTORY_KEY = "python-calculator-pro.history.v1";
  const sidebar = document.querySelector("#sidebar");
  const scrim = document.querySelector("[data-close-drawer]");
  const openButton = document.querySelector("[data-open-drawer]");
  const navItems = [...document.querySelectorAll("[data-tool]")];
  const pageTitle = document.querySelector("#page-title");
  const workspaceTitle = document.querySelector("#workspace-title");
  const workspaceSubtitle = document.querySelector("#workspace-subtitle");
  const angleButtons = [...document.querySelectorAll("[data-angle]")];
  const expressionInput = document.querySelector("#expression-input");
  const expressionError = document.querySelector("#expression-error");
  const answerOutput = document.querySelector("#answer-output");
  const resultDetails = document.querySelector("#result-details");
  const exactOutput = document.querySelector("#exact-output");
  const approxOutput = document.querySelector("#approx-output");
  const modeOutput = document.querySelector("#mode-output");
  const apiStatus = document.querySelector("#api-status");
  const historyList = document.querySelector("#history-list");
  const historyCount = document.querySelector("#history-count");
  const clearHistoryButton = document.querySelector("#clear-history");
  let angleMode = "DEG";
  let history = loadHistory();
  let isCalculating = false;

  const descriptions = {
    "Scientific Calculator": "A precise space for everyday maths and advanced expressions.",
    "Quadratic & Polynomial Solver": "Solve polynomial equations and inspect their mathematical results.",
    "Binomial Expansion": "Expand binomial expressions and review the resulting terms.",
    "Graphing Calculator": "Explore functions visually with an interactive graphing workspace.",
    "Calculus": "Work with derivatives, integrals, and limits.",
    "Matrix Calculator": "Explore matrix operations, transformations, and solutions.",
    "Statistics": "Summarize data with descriptive statistical measures.",
    "Probability & Combinatorics": "Work with probability, permutations, combinations, and counting.",
    "Unit Converter": "Convert values between supported measurement units.",
    "Currency Converter": "Convert currencies using the backend's available exchange-rate data.",
    "Finance & Loan EMI": "Calculate interest, compound growth, and loan instalments.",
    "Discount & GST Calculator": "Work out discounts, GST, and tax-inclusive prices.",
    "Number Base Converter": "Convert integer values between number bases.",
    "BMI Calculator": "Calculate body mass index from height and weight.",
    "Date Calculator": "Calculate date differences and date-based results."
  };

  function setDrawer(open) {
    sidebar.classList.toggle("is-open", open);
    scrim.hidden = !open;
    openButton.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("drawer-open", open);
  }
  openButton.addEventListener("click", () => setDrawer(true));
  scrim.addEventListener("click", () => setDrawer(false));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") setDrawer(false);
  });

  navItems.forEach(item => item.addEventListener("click", () => {
    navItems.forEach(candidate => {
      const selected = candidate === item;
      candidate.classList.toggle("is-active", selected);
      if (selected) candidate.setAttribute("aria-current", "page");
      else candidate.removeAttribute("aria-current");
    });
    const title = item.dataset.tool;
    pageTitle.textContent = title;
    workspaceTitle.textContent = title;
    workspaceSubtitle.textContent = descriptions[title] || "Choose a tool to begin.";
    setDrawer(false);
    if (title !== "Scientific Calculator") {
      showError("This tool is planned for a later phase. The scientific calculator remains available from the sidebar.");
    } else {
      clearError();
    }
  }));

  function setAngleMode(mode) {
    angleMode = mode;
    angleButtons.forEach(button => {
      const selected = button.dataset.angle === mode;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    modeOutput.textContent = mode;
  }
  angleButtons.forEach(button => button.addEventListener("click", () => setAngleMode(button.dataset.angle)));

  function showError(message) {
    expressionError.textContent = message;
    expressionError.hidden = false;
    expressionInput.setAttribute("aria-invalid", "true");
  }
  function clearError() {
    expressionError.textContent = "";
    expressionError.hidden = true;
    expressionInput.removeAttribute("aria-invalid");
  }
  function setApiStatus(connected, message) {
    apiStatus.innerHTML = "";
    const dot = document.createElement("span");
    dot.className = connected ? "status-dot" : "status-dot status-dot-muted";
    const text = document.createElement("span");
    text.textContent = message;
    apiStatus.append(dot, text);
  }

  async function checkApi() {
    try {
      const response = await fetch(API_BASE_URL + "/healthz", { method: "GET" });
      if (!response.ok) throw new Error("API health check failed");
      setApiStatus(true, "API connected");
    } catch {
      setApiStatus(false, "API offline");
    }
  }

  function transformDegreeTrig(expression) {
    if (angleMode !== "DEG") return expression;
    const names = new Set(["sin", "cos", "tan"]);
    let out = "";
    let i = 0;
    while (i < expression.length) {
      const match = expression.slice(i).match(/^([A-Za-z_][A-Za-z_0-9]*)\s*\(/);
      if (!match) { out += expression[i]; i++; continue; }
      const name = match[1];
      const openIndex = i + match[0].lastIndexOf("(");
      let depth = 1, j = openIndex + 1;
      while (j < expression.length && depth > 0) {
        if (expression[j] === "(") depth++;
        else if (expression[j] === ")") depth--;
        j++;
      }
      if (depth !== 0) { out += expression.slice(i); break; }
      const inner = transformDegreeTrig(expression.slice(openIndex + 1, j - 1));
      out += names.has(name.toLowerCase()) ? name + "(radians(" + inner + "))" : name + "(" + inner + ")";
      i = j;
    }
    return out;
  }

  function formatResult(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return String(value);
    if (Number.isInteger(value) && Math.abs(value) < 1e15) return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
    return value.toLocaleString("en-US", { maximumSignificantDigits: 12, useGrouping: true });
  }

  async function calculate() {
    if (isCalculating) return;
    const expression = expressionInput.value.trim();
    if (!expression) { showError("Enter an expression to calculate."); expressionInput.focus(); return; }
    if (navItems.some(item => item.classList.contains("is-active") && item.dataset.tool !== "Scientific Calculator")) {
      showError("Select Scientific Calculator in the sidebar to calculate an expression.");
      return;
    }
    clearError();
    isCalculating = true;
    answerOutput.textContent = "Calculating…";
    answerOutput.classList.add("is-loading");
    const submittedExpression = transformDegreeTrig(expression);
    try {
      const response = await fetch(API_BASE_URL + "/api/v1/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expression: submittedExpression })
      });
      let payload;
      try { payload = await response.json(); }
      catch { throw new Error("The API returned an unreadable response."); }
      if (!response.ok) {
        const message = payload?.error?.message || "Calculation failed. Check the expression and try again.";
        throw new Error(message);
      }
      if (typeof payload.result !== "number" || !Number.isFinite(payload.result)) {
        throw new Error("The API did not return a finite numeric result.");
      }
      answerOutput.textContent = formatResult(payload.result);
      answerOutput.classList.remove("is-loading");
      exactOutput.textContent = payload.exact_fraction || "Not available";
      approxOutput.textContent = payload.approximation || formatResult(payload.result);
      modeOutput.textContent = angleMode;
      resultDetails.hidden = !(payload.exact_fraction || payload.approximation);
      if (!resultDetails.hidden) resultDetails.open = false;
      addHistory({ expression, result: payload.result, displayedResult: formatResult(payload.result), angleMode, timestamp: new Date().toISOString() });
    } catch (error) {
      answerOutput.textContent = "Calculation unsuccessful";
      answerOutput.classList.remove("is-loading");
      resultDetails.hidden = true;
      showError(error instanceof TypeError ? "Could not reach the calculator API. Check that the backend is running and the API URL/CORS settings are correct." : error.message);
    } finally {
      isCalculating = false;
      answerOutput.classList.remove("is-loading");
    }
  }

  function insertAtCursor(text) {
    const start = expressionInput.selectionStart ?? expressionInput.value.length;
    const end = expressionInput.selectionEnd ?? start;
    const current = expressionInput.value;
    expressionInput.value = current.slice(0, start) + text + current.slice(end);
    const cursor = start + text.length;
    expressionInput.focus();
    expressionInput.setSelectionRange(cursor, cursor);
    clearError();
  }
  document.querySelectorAll("[data-insert]").forEach(button => button.addEventListener("click", () => insertAtCursor(button.dataset.insert)));
  document.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => {
    if (button.dataset.action === "calculate") calculate();
    if (button.dataset.action === "clear") {
      expressionInput.value = "";
      clearError();
      answerOutput.textContent = "Your answer appears here";
      resultDetails.hidden = true;
      expressionInput.focus();
    }
    if (button.dataset.action === "backspace") {
      const start = expressionInput.selectionStart ?? expressionInput.value.length;
      const end = expressionInput.selectionEnd ?? start;
      if (start !== end) insertAtCursor("");
      else if (start > 0) {
        expressionInput.setRangeText("", start - 1, start, "end");
        expressionInput.focus();
      }
      clearError();
    }
  }));
  expressionInput.addEventListener("keydown", event => {
    if (event.key === "Enter") { event.preventDefault(); calculate(); }
    if (event.key === "Escape") { expressionInput.value = ""; clearError(); }
  });
  expressionInput.addEventListener("input", clearError);

  function loadHistory() {
    try {
      const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
      return Array.isArray(parsed) ? parsed.filter(item => item && typeof item.expression === "string" && typeof item.displayedResult === "string").slice(0, 20) : [];
    } catch { return []; }
  }
  function persistHistory() {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); }
    catch { /* History remains usable in memory if browser storage is unavailable. */ }
  }
  function addHistory(item) {
    history = [item, ...history].slice(0, 20);
    persistHistory();
    renderHistory();
  }
  function renderHistory() {
    historyCount.textContent = String(history.length);
    clearHistoryButton.disabled = history.length === 0;
    historyList.replaceChildren();
    if (!history.length) {
      const empty = document.createElement("div");
      empty.className = "history-empty";
      const icon = document.createElement("span");
      icon.className = "history-empty-icon";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = "↺";
      const title = document.createElement("strong");
      title.textContent = "No calculations yet";
      const description = document.createElement("p");
      description.textContent = "Your recent results will appear here as you work.";
      empty.append(icon, title, description);
      historyList.append(empty);
      return;
    }
    history.forEach((item, index) => {
      const card = document.createElement("article");
      card.className = "history-entry";
      const expr = document.createElement("button");
      expr.type = "button";
      expr.className = "history-expression";
      expr.textContent = item.expression;
      expr.title = "Reuse this expression";
      expr.addEventListener("click", () => {
        expressionInput.value = item.expression;
        setAngleMode(item.angleMode === "RAD" ? "RAD" : "DEG");
        clearError();
        expressionInput.focus();
        expressionInput.setSelectionRange(expressionInput.value.length, expressionInput.value.length);
      });
      const result = document.createElement("div");
      result.className = "history-result";
      result.textContent = "= " + item.displayedResult;
      const meta = document.createElement("div");
      meta.className = "history-meta";
      const time = document.createElement("time");
      time.dateTime = item.timestamp;
      const date = new Date(item.timestamp);
      time.textContent = Number.isNaN(date.getTime()) ? "" : date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
      const actions = document.createElement("div");
      actions.className = "history-actions";
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "history-action";
      copy.textContent = "Copy result";
      copy.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(String(item.result));
          copy.textContent = "Copied";
          setTimeout(() => { copy.textContent = "Copy result"; }, 1200);
        } catch {
          const temp = document.createElement("textarea");
          temp.value = String(item.result);
          temp.setAttribute("readonly", "");
          temp.style.position = "fixed";
          temp.style.opacity = "0";
          document.body.append(temp);
          temp.select();
          const copied = document.execCommand("copy");
          temp.remove();
          copy.textContent = copied ? "Copied" : "Copy unavailable";
        }
      });
      actions.append(copy);
      meta.append(time, actions);
      card.append(expr, result, meta);
      historyList.append(card);
    });
  }
  clearHistoryButton.addEventListener("click", () => {
    if (!history.length) return;
    if (!window.confirm("Clear all recent calculations from this browser? This cannot be undone.")) return;
    history = [];
    persistHistory();
    renderHistory();
  });

  renderHistory();
  checkApi();
})();