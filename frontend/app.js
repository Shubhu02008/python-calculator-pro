(() => {
  const sidebar = document.querySelector("#sidebar");
  const scrim = document.querySelector("[data-close-drawer]");
  const openButton = document.querySelector("[data-open-drawer]");
  const navItems = [...document.querySelectorAll("[data-tool]")];
  const pageTitle = document.querySelector("#page-title");
  const workspaceTitle = document.querySelector("#workspace-title");
  const workspaceSubtitle = document.querySelector("#workspace-subtitle");
  const angleButtons = [...document.querySelectorAll("[data-angle]")];

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

  navItems.forEach(item => {
    item.addEventListener("click", () => {
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
      // Phase 2 shell only: calculator and tool API behavior is intentionally not wired yet.
    });
  });

  angleButtons.forEach(button => {
    button.addEventListener("click", () => {
      angleButtons.forEach(candidate => {
        const selected = candidate === button;
        candidate.classList.toggle("is-selected", selected);
        candidate.setAttribute("aria-pressed", String(selected));
      });
      // Visual selection only in Phase 2. Mathematical angle conversion is planned for Phase 3.
    });
  });
})();