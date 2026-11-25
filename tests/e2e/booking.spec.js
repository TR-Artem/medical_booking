const { test, expect } = require("@playwright/test");

const PASSWORD = "Test1234!";

async function login(page, username) {
  await page.goto("/accounts/login/");
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', PASSWORD);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.click('button[type="submit"]'),
  ]);
}

test("пациент: запись → отмена → повторная запись на тот же слот", async ({ page }) => {
  page.on("dialog", (dialog) => dialog.accept());
  await login(page, "patient@test.ru");

  await page.goto("/appointments/doctors/");
  const firstDoctor = page.locator(".doctor-card").first();
  const doctorName = (await firstDoctor.locator(".dc-name").innerText()).trim();

  await Promise.all([
    page.waitForLoadState("networkidle"),
    firstDoctor.locator('a:has-text("Записаться")').click(),
  ]);

  const slotLink = page.locator('a.slot-chip').first();
  await expect(slotLink).toBeVisible();
  const slotTime = (await slotLink.innerText()).trim();
  const bookUrl = await slotLink.getAttribute("href");

  await Promise.all([page.waitForLoadState("networkidle"), slotLink.click()]);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.click('button:has-text("Подтвердить запись")'),
  ]);

  await expect(page).toHaveURL(/\/appointments\/my\/$/);
  await expect(page.locator("body")).toContainText("успешно записаны");

  let card = page
    .locator(".appt-row.active-appt", { hasText: doctorName })
    .filter({ hasText: slotTime })
    .first();
  await expect(card).toBeVisible();

  await Promise.all([
    page.waitForLoadState("networkidle"),
    card.locator('button:has-text("Отменить")').click(),
  ]);
  await expect(page.locator("body")).toContainText("успешно отменена");

  await page.goto(bookUrl);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.click('button:has-text("Подтвердить запись")'),
  ]);
  await expect(page.locator("body")).toContainText("успешно записаны");

  card = page
    .locator(".appt-row.active-appt", { hasText: doctorName })
    .filter({ hasText: slotTime })
    .first();
  await expect(card).toBeVisible();
});

test("роли: администратор и сисадмин попадают в свои разделы", async ({ page }) => {
  await login(page, "admin@test.ru");
  await page.goto("/appointments/admin/dashboard/");
  await expect(page.locator("body")).toContainText("Панель администратора");

  await page.goto("/accounts/logout/");
  await login(page, "sysadmin@test.ru");
  await page.goto("/appointments/admin/users/");
  await expect(page.locator("body")).toContainText("Пользователи");
});
