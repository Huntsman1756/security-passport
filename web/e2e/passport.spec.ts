import { test, expect } from "@playwright/test";

const SECTIONS = [
  "Identity",
  "Primary market",
  "Secondary market",
  "Post-trade",
  "Eurosystem collateral",
];

test.describe("Security Passport", () => {
  test("home → ISIN search → passport", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("textbox", { name: "ISIN", exact: true }).fill("DE000A3LJCB4");
    await page.getByRole("button", { name: "Build passport" }).click();
    await expect(page).toHaveURL(/\/isin\/DE000A3LJCB4/);
    for (const s of SECTIONS)
      await expect(page.getByRole("heading", { name: s, exact: true })).toBeVisible();
  });

  test("client-side check digit validation blocks a typo", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("textbox", { name: "ISIN", exact: true }).fill("DE000A3LJCB0");
    await page.getByRole("button", { name: "Build passport" }).click();
    await expect(page.getByRole("alert")).toContainText("Check digit should be 4");
    await expect(page).toHaveURL(/\/$/);
  });

  test("provenance drawer opens on field click and closes on Escape", async ({ page }) => {
    await page.goto("/isin/DE000A3LJCB4");
    await page.getByRole("button", { name: /^CFI:/ }).click();
    const dialog = page.getByRole("dialog", { name: /provenance/i });
    await expect(dialog).toBeVisible();
    await expect(page.getByText(/Evidence \(\d+\)/)).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
  });

  test("conflict is rendered, not hidden", async ({ page }) => {
    await page.goto("/isin/IE0007SRI1C7");
    await expect(
      page.getByText("conflict", { exact: false }).first(),
    ).toBeVisible();
  });

  test("not_found renders as an explicit state", async ({ page }) => {
    await page.goto("/isin/ES0113900J37");
    await expect(page.getByText("not found").first()).toBeVisible();
  });

  test("invalid ISIN shows a clear error", async ({ page }) => {
    await page.goto("/isin/DE000A3LJCB0");
    await expect(page.getByText(/not a valid ISIN/i).first()).toBeVisible();
  });

  test("as-of query shows not-yet-effective settlement locations", async ({ page }) => {
    await page.goto("/isin/IE00B4L5Y983?as_of=2026-09-19");
    await expect(page.getByText("not yet").first()).toBeVisible();
  });

  test("ISIN outside the demo corpus is explained, not faked", async ({ page }) => {
    await page.goto("/isin/US0378331005");
    await expect(page.getByText(/outside the demo corpus/i)).toBeVisible();
  });

  test("corpus page lists and filters instruments", async ({ page }) => {
    await page.goto("/corpus");
    await page.getByRole("textbox", { name: "Filter corpus" }).fill("SAP");
    await expect(page.getByRole("link", { name: "DE0007164600" })).toBeVisible();
    await expect(page.getByRole("link", { name: "FR0000120271" })).toHaveCount(0);
  });
});
