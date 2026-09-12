import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const root = process.env.ATPLCRM_ROOT ?? path.resolve("../..");
const envFile = process.env.ATPLCRM_ENV ?? ".env";
const password = fs
  .readFileSync(path.join(root, envFile), "utf8")
  .split("\n")
  .find((l) => l.startsWith("DEMO_PASSWORD="))!
  .split("=")
  .slice(1)
  .join("=");
async function signIn(page: Page, user = "alex") {
  await page.goto("/");
  await page.getByLabel("Email address").fill(`${user}@atplcrm.local`);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Good (morning|afternoon)/ }),
  ).toBeVisible();
}

test("desktop workspace, all routes and opportunity details", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await signIn(page);
  await page.screenshot({
    path: "test-results/overview-desktop.png",
    fullPage: true,
  });
  for (const [route, title] of [
    ["work", "My work"],
    ["attention", "Needs attention"],
    ["pipeline", "Opportunities"],
    ["leads", "Leads"],
    ["companies", "Companies"],
    ["contacts", "Contacts"],
    ["presales", "Pre-sales"],
    ["reports", "Reports"],
    ["data", "Data tools"],
    ["settings", "Administration"],
  ]) {
    await page.goto("/#" + route);
    await expect(
      page.getByRole("heading", { name: title, exact: true }),
    ).toBeVisible();
  }
  await page.goto("/#pipeline");
  await page
    .getByRole("button")
    .filter({
      has: page.getByRole("heading", {
        name: "Predictive maintenance platform",
        exact: true,
      }),
    })
    .click();
  await expect(
    page.getByRole("dialog").getByRole("heading", {
      name: "Predictive maintenance platform",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Timeline", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Discovery and priorities discussion" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Value history", exact: true })
    .click();
  await expect(
    page.getByText("Initial estimate", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close details" }).click();
  expect(errors).toEqual([]);
});

test("a salesperson creates a lead and an independent manager converts it", async ({
  page,
}) => {
  const name = `Browser acceptance ${Date.now()}`;
  await signIn(page, "maya");
  await page.getByRole("button", { name: "New lead", exact: true }).click();
  const form = page.getByRole("dialog");
  await form.getByLabel("Lead name").fill(name);
  await form
    .getByLabel("Company", { exact: false })
    .selectOption({ label: "Northstar Industries" });
  await form
    .getByLabel("Next action", { exact: false })
    .fill("Confirm discovery agenda");
  await form.getByRole("button", { name: "Create lead", exact: true }).click();
  await expect(page.getByText("Changes saved successfully.")).toBeVisible();
  await page.goto("/#leads");
  await page
    .getByRole("button")
    .filter({ has: page.getByRole("heading", { name, exact: true }) })
    .click();
  await page.getByLabel("Lead status").selectOption("ready");
  await expect(page.getByLabel("Lead status")).toHaveValue("ready");
  await page.getByRole("button", { name: "Close details" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Email address")).toBeVisible();
  await signIn(page, "alex");
  await page.goto("/#leads");
  await page
    .getByRole("button")
    .filter({ has: page.getByRole("heading", { name, exact: true }) })
    .click();
  await page
    .getByRole("button", { name: "Validate & convert", exact: true })
    .click();
  const convert = page.getByRole("dialog").last();
  await convert
    .getByLabel("Customer need")
    .fill("Eliminate manual inspection bottlenecks");
  await convert
    .getByLabel("Scope summary")
    .fill("Discovery followed by a measurable pilot");
  await convert
    .getByLabel("Primary contact")
    .selectOption({ label: "Elena Rodriguez" });
  await convert.getByLabel("Initial estimate").fill("50000");
  await convert
    .getByLabel("Service line")
    .selectOption({ label: "AI & ML delivery" });
  await convert
    .getByRole("button", { name: "Validate & convert", exact: true })
    .click();
  await expect(page.getByLabel("Opportunity stage")).toHaveValue("discovery");
  await page
    .getByRole("button", { name: "Value history", exact: true })
    .click();
  await expect(
    page.locator(".value-row").getByText("$50,000", { exact: true }),
  ).toBeVisible();
});

test("phone layout stays within the viewport and navigation works", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  await page.screenshot({
    path: "test-results/overview-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: "Contacts", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Contacts", exact: true }),
  ).toBeVisible();
});

test("workspace administrator manages local users and reference data", async ({
  page,
}) => {
  const email = `admin-check-${Date.now()}@example.com`;
  await signIn(page, "admin");
  await page.goto("/#settings");
  await expect(
    page.getByRole("heading", { name: "Workspace reference data" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Add user", exact: true }).click();
  const form = page.getByRole("dialog");
  await form.getByLabel("First name").fill("Admin");
  await form.getByLabel("Last name").fill("Verification");
  await form.getByLabel("Email address").fill(email);
  await form.getByLabel("Job title").fill("Verification account");
  await form.getByLabel("Access level").selectOption("Standard");
  await form.getByLabel("Temporary password").fill("Temporary1234");
  await form.getByRole("button", { name: "Create user", exact: true }).click();
  await expect(page.getByText("Changes saved successfully.")).toBeVisible();
  await expect(page.getByText(email)).toBeVisible();
});

test("manager searches and imports validated CRM data", async ({ page }) => {
  const name = `Imported browser company ${Date.now()}`;
  await signIn(page, "alex");
  await page.goto("/#data");
  await page.getByLabel("Search terms").fill("Northstar");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByText("Northstar Industries", { exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Import center" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "browser-companies.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      `name,country,owner_email,domain,industry\n${name},India,alex@atplcrm.local,browser-${Date.now()}.example,Technology\n`,
    ),
  });
  await page.getByRole("button", { name: "Validate file" }).click();
  await expect(
    page.getByRole("button", { name: "Import 1 valid row" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Import 1 valid row" }).click();
  await expect(page.getByText("1 rows imported; 0 skipped.")).toBeVisible();
  await page.getByRole("tab", { name: "Global search" }).click();
  await page.getByLabel("Search terms").fill(name);
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByText(name, { exact: true })).toBeVisible();
});

test("manager saves a pipeline view and assigns work in bulk", async ({
  page,
}) => {
  const viewName = `High priority ${Date.now()}`;
  await signIn(page, "alex");
  await page.goto("/#pipeline");
  await page.getByRole("button", { name: "List", exact: true }).click();
  await expect(page.getByLabel("Search opportunities")).toBeVisible();
  await page.getByLabel("List priority").selectOption("High");
  await page.getByRole("button", { name: "+ Save current filters" }).click();
  await page.getByLabel("Saved view name").fill(viewName);
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await expect(
    page.getByRole("button", { name: viewName, exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: false }).click();
  await expect(page.getByLabel("List priority")).toHaveValue("");
  await page.getByLabel("Select Predictive maintenance platform").check();
  await page
    .getByLabel("New Ball in Court holder")
    .selectOption({ label: "Omar Hassan" });
  await page
    .getByLabel("Assignment reason")
    .fill("Browser acceptance coverage");
  await page
    .getByRole("button", { name: "Apply assignment", exact: false })
    .click();
  await expect(page.getByText("1 pursuit assigned.")).toBeVisible();
});

test("manager adds and edits an opportunity stakeholder", async ({ page }) => {
  const suffix = Date.now();
  const firstName = "Browser";
  const lastName = `Stakeholder ${suffix}`;
  const fullName = `${firstName} ${lastName}`;
  await signIn(page, "alex");
  await page.goto("/#contacts");
  await page.getByRole("button", { name: "Add contact", exact: true }).click();
  const contactForm = page.getByRole("dialog");
  await contactForm.getByLabel("First name").fill(firstName);
  await contactForm.getByLabel("Last name").fill(lastName);
  await contactForm
    .getByLabel("Company", { exact: false })
    .selectOption({ label: "Northstar Industries" });
  await contactForm.getByLabel("Country").fill("United States");
  const refreshedContacts = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/bootstrap/") && response.ok(),
  );
  await contactForm
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await refreshedContacts;
  await expect(page.getByText("Changes saved successfully.")).toBeVisible();
  await page.goto("/#pipeline");
  await page
    .getByRole("button")
    .filter({
      has: page.getByRole("heading", {
        name: "Predictive maintenance platform",
        exact: true,
      }),
    })
    .click();
  await page
    .getByRole("button", { name: "Team & contacts", exact: true })
    .click();
  await page.getByRole("button", { name: "Add stakeholder" }).click();
  const stakeholderForm = page.getByRole("dialog").last();
  await stakeholderForm.getByLabel("Contact").selectOption({ label: fullName });
  await stakeholderForm
    .getByLabel("Relationship role")
    .selectOption("Decision maker");
  await stakeholderForm
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await expect(page.getByText(fullName, { exact: true })).toBeVisible();
  const person = page.locator(".settings-person").filter({ hasText: fullName });
  await person.getByRole("button", { name: "Edit", exact: true }).click();
  const editForm = page.getByRole("dialog").last();
  await editForm.getByLabel("Relationship role").selectOption("Champion");
  await editForm
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await expect(person.getByText("Champion", { exact: true })).toBeVisible();
});

test("login recovers when another tab refreshes the CSRF cookie", async ({
  page,
  context,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Email address")).toBeVisible();
  await page.getByLabel("Email address").fill("alex@atplcrm.local");
  await page.getByLabel("Password", { exact: true }).fill(password);

  const secondTab = await context.newPage();
  await secondTab.goto("/");
  await expect(secondTab.getByLabel("Email address")).toBeVisible();
  await secondTab.close();

  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Good (morning|afternoon)/ }),
  ).toBeVisible();
  await expect(page.getByText("CSRF validation failed.")).toHaveCount(0);
});
