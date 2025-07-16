export const siteConfig = {
  name: "Kenya Crypto Payment",
  description:
    "A dual-account crypto-fiat web application for the Kenyan market, integrating crypto wallets (BTC, USDT) and M-Pesa for fiat KES settlement.",
  mainNav: [
    {
      title: "Home",
      href: "/",
    },
    {
      title: "Test UI",
      href: "/test-ui",
    },
    {
      title: "Documentation",
      href: "/documentation",
    },
  ],
  links: {
    twitter: "https://twitter.com/vercel",
    github: "https://github.com/vercel/next.js", // Placeholder, replace with actual repo
    docs: "https://ui.shadcn.com", // Placeholder, replace with actual docs
  },
}

export type SiteConfig = typeof siteConfig
