import { enUS } from "./en-US";
import { zhCN } from "./zh-CN";

export type Locale = "en-US" | "zh-CN";

const dictionaries = {
  "en-US": enUS,
  "zh-CN": zhCN,
};

export function translate(locale: Locale, key: string): string {
  const typedKey = key as keyof typeof enUS;
  return dictionaries[locale][typedKey] ?? enUS[typedKey] ?? key;
}
