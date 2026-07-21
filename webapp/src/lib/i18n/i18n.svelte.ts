import { en, ja, zh, type MessageKey } from "./messages";

export const CATALOGS = { zh, ja, en } as const;
export type Language = keyof typeof CATALOGS;
export const LANGUAGES = Object.keys(CATALOGS) as Language[];

export type MessageParams = Record<string, string | number>;

export function format(template: string, params?: MessageParams): string {
  if (!params) return template;
  let text = template;
  for (const [name, value] of Object.entries(params)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

export function isLanguage(value: unknown): value is Language {
  return typeof value === "string" && value in CATALOGS;
}

const STORAGE_KEY = "terrai-language";

function initialLanguage(): Language {
  if (typeof window === "undefined") return "zh";
  const requested = new URLSearchParams(window.location.search).get("lang");
  if (isLanguage(requested)) return requested;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isLanguage(stored) ? stored : "zh";
}

let current = $state<Language>(initialLanguage());

export const i18n = {
  get lang(): Language {
    return current;
  },
  set lang(value: Language) {
    current = value;
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, value);
  },
  t(key: MessageKey, params?: MessageParams): string {
    return format(CATALOGS[current][key], params);
  },
};

export type { MessageKey };
