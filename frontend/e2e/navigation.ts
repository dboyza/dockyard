import { expect, type Page } from '@playwright/test';

export async function navigateTo(page: Page, destination: string) {
  const parents: Record<string, string> = {
    'Your course': 'Your course',
    'Find your starting point': 'Your course',
    'Troubleshooting': 'Practice',
    'Exam practice': 'Practice',
    'Your progress': 'Your progress',
    'Review practice': 'Your progress',
    'Saved projects': 'Your progress',
  };
  const parent = parents[destination] || destination;
  const primary = page.locator('.sidebar').getByRole('button', { name: parent, exact: true });
  await expect(primary).toBeAttached();
  if (!await primary.isVisible()) await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await primary.click();
  if (parents[destination]) await page.locator('.section-nav').getByRole('button', { name: destination, exact: true }).click();
}
