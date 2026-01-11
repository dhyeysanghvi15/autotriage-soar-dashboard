import { test, expect } from "@playwright/test";

test("loads dashboard and renders overview", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("AutoTriage")).toBeVisible();
  await expect(page.getByText("Ingested (24h)")).toBeVisible();
});

test("cases table renders and case detail loads", async ({ page }) => {
  await page.goto("/cases");
  await expect(page.locator(".panel-title", { hasText: "Cases" })).toBeVisible();

  const firstLink = page.locator("table.table tbody tr td a.link").first();
  await expect(firstLink).toBeVisible();
  await firstLink.click();

  await expect(page.getByText("Entity Graph")).toBeVisible();
  await expect(page.getByText("Timeline")).toBeVisible();
  await expect(page.getByText("Score Explainability")).toBeVisible();
});

test("playbook markdown serves 200", async ({ request }) => {
  const r = await request.get("/playbooks/actions/isolate_host.md");
  expect(r.status()).toBe(200);
  const text = await r.text();
  expect(text).toContain("Isolate Host");
});
