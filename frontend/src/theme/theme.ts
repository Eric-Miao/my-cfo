export type ThemeMode = "light" | "dark";

export function applyTheme(theme: ThemeMode): void {
  document.documentElement.dataset.theme = theme;
}
