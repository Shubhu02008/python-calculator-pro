import assert from "node:assert/strict";
import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.stack || error.message));
  let graphRequests = 0;
  const graphExpressions = [];
  await page.route("**/api/v1/graph/sample", async (route) => {
    graphRequests += 1;
    const body = route.request().postDataJSON();
    graphExpressions.push(body.expression);
    const count = Math.min(body.points || 101, 801);
    const points = Array.from({ length: count }, (_, i) => {
      const x = body.x_min + (body.x_max - body.x_min) * i / (count - 1);
      let y;
      if (body.expression.includes("sin")) y = Math.sin(x);
      else if (body.expression.includes("cos")) y = Math.cos(x);
      else y = x * x;
      return { x, y };
    });
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ points }) });
  });

  await page.goto("http://127.0.0.1:8000/studio.html");
  try { await page.locator("#graph-status").getByText(/Plotted 2 function\(s\)/).waitFor({ timeout: 5000 }); } catch (error) { throw new Error(`Initial plot failed. Status: ${await page.locator("#graph-status").innerText()}; page errors: ${pageErrors.join(" | ")}; ${error.message}`); }
  assert.ok(graphRequests >= 2, "default functions should call the graph API");
  assert.equal(await page.locator("#graph path").count(), 2, "both default function curves should render");
  assert.ok(graphExpressions.some(expression => expression.includes("(1)") && expression.includes("x^2") && expression.includes("(0)")), "parameterized expressions should be substituted before API requests");
  const updatedSliderRequest = page.waitForResponse(response => {
    const request = response.request();
    if (!response.url().includes("/api/v1/graph/sample")) return false;
    try { const expression = request.postDataJSON().expression; return expression.includes("(2)") && expression.includes("x^2"); } catch { return false; }
  }, { timeout: 5000 });
  await page.locator('#parameters [data-param-slider]').first().evaluate(el => { el.value = "2"; el.dispatchEvent(new Event("input", { bubbles: true })); });
  await updatedSliderRequest;
  assert.ok(graphExpressions.some(expression => expression.includes("(2)") && expression.includes("x^2")), "updated slider values should reach the graph API");

  await page.getByRole("button", { name: "+ Add function" }).click();
  await page.locator(".function-row").nth(2).locator("input").fill("cos(x)");
  await page.locator("#plot").click();
  await page.locator("#graph-status").getByText(/Plotted 3 function\(s\)/).waitFor({ timeout: 5000 });
  assert.equal(await page.locator("#graph path").count(), 3, "adding a function should render a third curve");

  await page.locator("#xmin").fill("10");
  await page.locator("#xmax").fill("-10");
  await page.locator("#plot").click();
  await page.getByText(/minimum must be smaller/).waitFor({ timeout: 2000 });

  await page.getByRole("button", { name: /Spreadsheet/ }).click();
  assert.equal(await page.locator("#sheet-table tbody tr").count(), 12);
  assert.equal(await page.locator("#x-col").inputValue(), "0");
  assert.equal(await page.locator("#y-col").inputValue(), "1", "spreadsheet Y column should default to B");

  await page.locator('#sheet-table [data-r="0"][data-c="0"]').fill("1");
  await page.locator('#sheet-table [data-r="0"][data-c="1"]').fill("2");
  await page.locator('#sheet-table [data-r="1"][data-c="0"]').fill("3");
  await page.locator('#sheet-table [data-r="1"][data-c="1"]').fill("=A2+1");
  await page.locator('#sheet-table [data-r="0"][data-c="2"]').fill("=SUM(A1:B2)");
  await page.locator('#sheet-table [data-r="0"][data-c="2"]').dispatchEvent("change");
  await page.getByText("Cell C1 = 10").waitFor({ timeout: 2000 });
  await page.locator('#sheet-table [data-r="0"][data-c="3"]').fill("=D1");
  await page.locator('#sheet-table [data-r="0"][data-c="3"]').dispatchEvent("change");
  await page.getByText(/Formula error: Circular reference/).waitFor({ timeout: 2000 });
  await page.getByRole("button", { name: "Plot selected columns" }).click();
  await page.locator("#sheet-status").getByText(/Plotted 2 numeric data pairs/).waitFor({ timeout: 2000 });
  assert.equal(await page.locator("#sheet-chart path").count(), 1, "spreadsheet points should render as a curve");
  await page.locator('#sheet-table [data-r="2"][data-c="0"]').fill("5");
  await page.locator('#sheet-table [data-r="2"][data-c="1"]').fill("8");
  await page.locator("#regression-mode").selectOption("linear");
  await page.getByRole("button", { name: "Plot selected columns" }).click();
  await page.getByText(/Linear regression:.*R² =/).waitFor({ timeout: 2000 });
  assert.equal(await page.locator("#sheet-chart path").count(), 2, "linear regression should overlay a fitted line");
  await page.locator("#regression-mode").selectOption("quadratic");
  await page.getByRole("button", { name: "Plot selected columns" }).click();
  await page.getByText(/Quadratic regression:.*R² =/).waitFor({ timeout: 2000 });

  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.locator("#sheet-table").isVisible(), "spreadsheet should remain visible on a mobile viewport");
  await page.locator(".tab[data-view='graph']").click();
  await page.locator("#graph-mode").selectOption("parametric");
  await page.locator(".function-row").nth(2).locator(".remove").click();
  await page.locator(".function-row").nth(1).locator(".remove").click();
  await page.locator(".function-row input").first().fill("cos(x)"+String.fromCharCode(59)+"sin(x)");
  await page.locator("#plot").click();
  try { await page.getByText(/Plotted 1 parametric curve/).waitFor({ timeout: 3000 }); } catch { throw new Error("Parametric plot failed: "+await page.locator("#graph-status").innerText()); }
  await page.locator("#graph-mode").selectOption("polar");
  await page.locator(".function-row input").first().fill("1");
  await page.locator("#plot").click();
  await page.getByText(/Plotted 1 polar curve/).waitFor({ timeout: 3000 });
  console.log("Advanced Math Studio browser smoke tests passed.");
} finally {
  await browser.close();
}
