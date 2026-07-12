import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "MovePredict BH",
    short_name: "MovePredict",
    description: "Linhas, pontos e trajetos do transporte coletivo de Belo Horizonte.",
    start_url: "./",
    scope: "./",
    display: "standalone",
    background_color: "#f4f8fb",
    theme_color: "#102a43",
    lang: "pt-BR",
    orientation: "portrait-primary",
    categories: ["navigation", "travel", "utilities"],
    icons: [
      {
        src: "./icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "./icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
