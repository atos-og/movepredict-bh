import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import "leaflet/dist/leaflet.css";
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
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${bodyFont.variable} ${displayFont.variable}`}>{children}</body>
    </html>
  );
}
