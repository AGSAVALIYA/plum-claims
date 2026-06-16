// Configuration for the interactive PPT
// All values can be overridden via environment variables (NEXT_PUBLIC_*)

export const CONFIG = {
  // GitHub repository base URL
  githubBaseUrl:
    process.env.NEXT_PUBLIC_GITHUB_URL ||
    "https://github.com/AGSAVALIYA/plum-claims/blob/main",

  // Presenter info (customize via env or edit here)
  presenter: {
    name: process.env.NEXT_PUBLIC_PRESENTER_NAME || "Your Name",
    email: process.env.NEXT_PUBLIC_PRESENTER_EMAIL || "your.email@example.com",
    linkedin:
      process.env.NEXT_PUBLIC_PRESENTER_LINKEDIN ||
      "https://linkedin.com/in/ags0504",
  },

  // Audio base path (files placed in public/audio/)
  audioBasePath: "/audio",

  // Screenshot base path
  screenshotBasePath: "/screenshots",
};

// GitHub file URL helper
export function githubFile(path: string, lines?: string): string {
  const url = `${CONFIG.githubBaseUrl}/${path}`;
  return lines ? `${url}#L${lines}` : url;
}
