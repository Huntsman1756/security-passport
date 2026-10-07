import { test, expect } from "@playwright/test";

test.describe("Security Passport", () => {
  test("home → ISIN search → passport", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("textbox", { name: "ISIN", exact: true }).fill("DE000A3LJCB4");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page).toHaveURL(/\/isin\/DE000A3LJCB4/);
    await expect(page.getByText("IDENTITY")).toBeVisible();
    await expect(page.getByText("PRIMARY MARKET")).toBeVisible();
    await expect(page.getByText("SECONDARY MARKET")).toBeVisible();
    await expect(page.getByText("POST-TRADE")).toBeVisible();
    await expect(page.getByText("EUROSYSTEM COLLATERAL")).toBeVisible();
  });

  test("provenance drawer opens on field click", async ({ page }) => {
    await page.goto("/isin/DE000A3LJCB4");
    await page.getByRole("button", { name: /^CFI:/ }).click();
    await expect(
      page.getByRole("dialog", { name: /provenance/i }),
    ).toBeVisible();
    await expect(
      page.getByText(/Evidence \(\d+\)/),
    ).toBeVisible();
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
});
