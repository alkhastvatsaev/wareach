/** Brand pages content for LuxFind FR SEO façade */

export type BrandGuide = {
  slug: string;
  name: string;
  headline: string;
  intro: string;
  tips: string[];
};

export const BRAND_GUIDES: BrandGuide[] = [
  {
    slug: "louis-vuitton",
    name: "Louis Vuitton",
    headline: "Guide discret Louis Vuitton",
    intro:
      "Comment identifier un vendeur sérieux, lire un QC et anticiper la livraison en France — sans bruit.",
    tips: [
      "Vérifiez la présence Yupoo + WhatsApp cohérents sur plusieurs sources.",
      "Comparez les photos QC (coutures, hardware, embossing) avant tout paiement.",
      "Privilégiez les agents (Pandabuy / CSSBuy) pour le suivi colis FR.",
    ],
  },
  {
    slug: "hermes",
    name: "Hermès",
    headline: "Guide discret Hermès",
    intro:
      "Birkin, Kelly, Constance : repères qualité 1:1 et red flags vendeurs pour acheteurs FR.",
    tips: [
      "Le cuir et le ferroir sont les premiers critères de QC.",
      "Méfiez-vous des catalogues trop larges sans photos atelier.",
      "Demandez des photos sous lumière naturelle avant validation.",
    ],
  },
  {
    slug: "chanel",
    name: "Chanel",
    headline: "Guide discret Chanel",
    intro: "Flap bags, Classic et 22 — checklist discrète pour acheteurs exigeants.",
    tips: [
      "Alignement des matelassés et poids du hardware sont décisifs.",
      "Vérifiez le numéro de série / stickers sur les photos QC.",
      "Évitez les offres « trop belles » sans historique communautaire.",
    ],
  },
  {
    slug: "dior",
    name: "Dior",
    headline: "Guide discret Dior",
    intro: "Book Tote, Saddle, Lady Dior — points de contrôle et canaux FR.",
    tips: [
      "Broderie Book Tote : densité et régularité des points.",
      "Demandez des détails logo + lining sur chaque pièce.",
      "Croisez les retours community (Reddit / Telegram) avant achat.",
    ],
  },
  {
    slug: "cartier",
    name: "Cartier",
    headline: "Guide discret Cartier",
    intro: "Love, Juste un Clou, Trinity — focus finition métal et gravures.",
    tips: [
      "Poids et gravure intérieure sont les premiers filtres.",
      "Exigez une vidéo QC 360° avant validation.",
      "Préférez les vendeurs spécialisés joaillerie aux généralistes.",
    ],
  },
  {
    slug: "gucci",
    name: "Gucci",
    headline: "Guide discret Gucci",
    intro: "GG Marmont, Dionysus, Horsebit — checklist qualité pour la France.",
    tips: [
      "Vérifiez la symétrie du monogramme et la qualité du cuir.",
      "Comparez plusieurs QC du même modèle chez le vendeur.",
      "Documentez chaque échange pour votre suivi personnel.",
    ],
  },
];

export function getBrand(slug: string): BrandGuide | undefined {
  return BRAND_GUIDES.find((b) => b.slug === slug);
}
