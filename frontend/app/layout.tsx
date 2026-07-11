import type { Metadata, Viewport } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import "leaflet/dist/leaflet.css";
import { PwaRegistration } from "@/components/pwa-registration";
import "./globals.css";

const bodyFont = IBM_Plex_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const displayFont = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["600", "700"],
});

export const metadata: Metadata = {
  title: "MovePredict BH",
  description: "Linhas, pontos e trajetos do transporte coletivo de Belo Horizonte.",
  applicationName: "MovePredict BH",
  manifest: "./manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "MovePredict BH",
  },
  icons: {
    icon: [
      {
        url: `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/icon-192.png`,
        sizes: "192x192",
        type: "image/png",
      },
      {
        url: `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/icon-512.png`,
        sizes: "512x512",
        type: "image/png",
      },
    ],
    apple: [
      {
        url: `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/apple-touch-icon.png`,
        sizes: "180x180",
        type: "image/png",
      },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: "#102a43",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${bodyFont.variable} ${displayFont.variable}`}>
        <PwaRegistration />
        {children}
      </body>
    </html>
  );
}
