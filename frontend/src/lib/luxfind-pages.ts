/** LuxFind FR — all SEO guide pages (intent + brand + model). Soft tone only. */

export type PageSection = { h2: string; body: string };

export type LuxfindPage = {
  slug: string;
  title: string;
  h1: string;
  description: string;
  intent: "howto" | "brand" | "model";
  intro: string;
  sections: PageSection[];
  brands?: string[];
  related: string[];
};

export const LUXFIND_PAGES: LuxfindPage[] = [
  // ── Batch 1: Intentions ──────────────────────────────────────────
  {
    slug: "comment-commander-yupoo",
    title: "Comment commander sur Yupoo depuis la France",
    h1: "Comment commander sur Yupoo depuis la France",
    description:
      "Guide discret : Yupoo est une vitrine, pas une boutique. Agent ou WhatsApp, QC, livraison FR.",
    intent: "howto",
    intro:
      "Yupoo n’est pas une boutique en ligne classique : c’est un catalogue photo. Pour commander depuis la France, vous passez soit par un agent d’achat, soit en contact direct avec le vendeur.",
    sections: [
      {
        h2: "Comprendre Yupoo",
        body: "Chaque vendeur publie des albums (modèles, couleurs, détails). Les prix et le paiement se négocient ailleurs. Repérez toujours l’onglet Contact : WhatsApp, Telegram ou WeChat y figurent en général.",
      },
      {
        h2: "Deux chemins d’achat",
        body: "Chemin agent : vous collez le lien album dans CNFans, Sugargoo ou Kakobuy ; l’agent achète, stocke, envoie des photos QC, puis expédie vers la France. Chemin direct : vous écrivez au WhatsApp du vendeur, validez le modèle, payez selon l’accord, et recevez le colis sans entrepôt intermédiaire.",
      },
      {
        h2: "Avant de payer",
        body: "Demandez des photos QC récentes du même lot, confirmez taille et couleur par écrit, et notez le délai annoncé. Méfiez-vous des catalogues sans historique communautaire et des prix irréalistes.",
      },
    ],
    related: ["agent-france", "whatsapp-vendeur-chine", "qc-checklist"],
  },
  {
    slug: "whatsapp-vendeur-chine",
    title: "Contacter un vendeur chinois sur WhatsApp",
    h1: "WhatsApp vendeur Chine : comment procéder",
    description:
      "Message type, infos à demander, red flags — guide discret pour acheteurs en France.",
    intent: "howto",
    intro:
      "Le contact WhatsApp est le canal le plus courant pour un achat direct hors agent. Un échange clair évite les malentendus sur le modèle, le prix et la livraison.",
    sections: [
      {
        h2: "Premier message utile",
        body: "Indiquez le lien Yupoo exact (album + photo), la taille, la couleur, et votre pays (France). Demandez le prix total vers entrepôt agent ou vers adresse FR, selon votre option.",
      },
      {
        h2: "Ce qu’il faut obtenir par écrit",
        body: "Référence du modèle, batch / qualité annoncée, délai de préparation, mode de paiement accepté, et si des photos QC sont fournies avant expédition.",
      },
      {
        h2: "Signaux d’alerte",
        body: "Pression pour payer immédiatement, refus de QC, numéro qui change sans raison, ou catalogue copié d’un autre vendeur connu. Dans le doute, passez par un agent.",
      },
    ],
    related: ["comment-commander-yupoo", "eviter-arnaques-vendeurs", "paiement-securise"],
  },
  {
    slug: "agent-france",
    title: "Agent d’achat Chine vers la France",
    h1: "Choisir un agent pour commander depuis la France",
    description:
      "CNFans, Sugargoo, Kakobuy : rôle de l’agent, QC, shipping tax-free vers la France.",
    intent: "howto",
    intro:
      "Un agent achète pour vous en Chine, inspecte le colis, photographie (QC), puis expédie vers la France. C’est le chemin le plus rassurant pour une première commande.",
    sections: [
      {
        h2: "À quoi sert l’agent",
        body: "Paiement carte, consolidation de plusieurs articles, photos QC, choix de ligne d’expédition (dont options tax-free / EU). Pandabuy n’est plus une option fiable depuis 2024.",
      },
      {
        h2: "Agents souvent cités",
        body: "CNFans, Sugargoo, Kakobuy et équivalents remplissent le même rôle. Comparez frais de service, délais QC et options d’envoi vers la France avant de déposer des fonds.",
      },
      {
        h2: "Flux typique",
        body: "Lien produit → commande manuelle → arrivée entrepôt → QC → validation → shipping → last-mile Colissimo / Chronopost selon la ligne.",
      },
    ],
    related: ["meilleur-agent-2026", "douane-france", "premiere-commande"],
  },
  {
    slug: "qc-checklist",
    title: "Checklist QC avant validation",
    h1: "Checklist QC : valider avant d’expédier",
    description:
      "Points à contrôler sur les photos QC : coutures, hardware, logo, symétrie — guide LuxFind FR.",
    intent: "howto",
    intro:
      "Le QC (quality check) est le moment où vous acceptez ou refusez une pièce. Sans checklist, on valide trop vite.",
    sections: [
      {
        h2: "Photos indispensables",
        body: "Face, dos, profils, intérieur, fermetures, logo de près, et une vue avec règle ou objet pour l’échelle. Demandez une vidéo 360° si le vendeur / agent le permet.",
      },
      {
        h2: "Points critiques sacs",
        body: "Alignement des motifs, régularité des coutures, poids et finition du hardware, gravures, odeur mentionnée, état du lining.",
      },
      {
        h2: "Décision GL / RL",
        body: "GL (green light) = vous validez l’envoi. RL (red light) = retour / échange selon la politique agent. Notez toujours la raison du RL pour la prochaine commande.",
      },
    ],
    related: ["photos-qc-lire", "premiere-commande", "book-tote"],
  },
  {
    slug: "douane-france",
    title: "Douane France et colis depuis la Chine",
    h1: "Douane France : ce que les acheteurs surveillent",
    description:
      "TVA, frais de dossier, lignes tax-free, bonnes pratiques de déclaration — guide informatif FR.",
    intent: "howto",
    intro:
      "La douane française est le sujet n°1 des discussions livraison. L’objectif des acheteurs expérimentés : réduire les mauvaises surprises à l’arrivée.",
    sections: [
      {
        h2: "Frais possibles",
        body: "Selon la ligne et la déclaration, TVA et frais de dossier transporteur peuvent s’appliquer. Les lignes tax-free / IOSS cherchent à intégrer ces coûts en amont.",
      },
      {
        h2: "Bonnes pratiques citées",
        body: "Choisir une ligne adaptée à la France, éviter les colis trop lourds d’un coup, conserver tracking, et ne pas relancer inutilement le transporteur au mauvais moment.",
      },
      {
        h2: "Information, pas conseil juridique",
        body: "Ce guide est informatif. Les règles évoluent ; vérifiez toujours les conditions de votre agent et du transporteur au moment de l’envoi.",
      },
    ],
    related: ["tariffless-europe", "livraison-colissimo-chine", "shipping-france-delais"],
  },
  {
    slug: "livraison-colissimo-chine",
    title: "Livraison Colissimo depuis la Chine",
    h1: "Colissimo et last-mile en France",
    description:
      "Comment le last-mile Colissimo s’inscrit après un envoi Chine → France via agent.",
    intent: "howto",
    intro:
      "Beaucoup de lignes internationales se terminent par un last-mile français : Colissimo, Chronopost ou point relais. Comprendre ce basculement aide à suivre le colis.",
    sections: [
      {
        h2: "Deux trackings",
        body: "Vous avez souvent un numéro international puis un numéro domestique une fois le colis repris par La Poste. Patientez le transfert avant de signaler une perte.",
      },
      {
        h2: "Délais réalistes",
        body: "Comptez fréquemment 2 à 4 semaines porte-à-porte selon la ligne. Les pics (soldes, Nouvel An chinois) allongent les files d’entrepôt.",
      },
      {
        h2: "À la livraison",
        body: "Vérifiez l’emballage. En cas d’anomalie, documentez photos et contactez d’abord l’assurance / l’agent si vous en aviez une.",
      },
    ],
    related: ["shipping-france-delais", "douane-france", "haul-france"],
  },
  {
    slug: "tariffless-europe",
    title: "Lignes tax-free / tariffless vers l’Europe",
    h1: "Lignes tax-free Europe : l’idée générale",
    description:
      "Comprendre les lignes EU tax-free / tariffless utilisées par les agents vers la France.",
    intent: "howto",
    intro:
      "Les communautés d’acheteurs parlent beaucoup de lignes « tax-free » ou « tariffless ». L’idée : anticiper taxes et réduire les frictions à l’entrée UE.",
    sections: [
      {
        h2: "Principe",
        body: "Ces lignes passent souvent par des hubs et une logique de pré-clearance. Le prix au kilo est plus élevé, mais le risque de frais surprise à la porte diminue.",
      },
      {
        h2: "Quand les choisir",
        body: "Hauls moyens/lourds, pièces sensibles, ou première expérience France. Pour un article léger, une ligne économique peut suffire — au prix d’un risque différent.",
      },
      {
        h2: "Comparer chez l’agent",
        body: "Regardez estimation, poids volumétrique, assurance, et retours d’expérience récents (les lignes changent de nom souvent).",
      },
    ],
    related: ["douane-france", "agent-france", "haul-france"],
  },
  {
    slug: "haul-france",
    title: "Préparer un haul livré en France",
    h1: "Organiser un haul pour la France",
    description:
      "Poids, split de colis, QC groupé, budget shipping — guide haul France LuxFind.",
    intent: "howto",
    intro:
      "Un haul = plusieurs articles regroupés. Bien le préparer évite un shipping ruinant ou un colis trop exposé.",
    sections: [
      {
        h2: "Poids et split",
        body: "Beaucoup d’acheteurs FR limitent le poids par carton et splitent si nécessaire. Demandez estimation shipping avant de valider tous les QC.",
      },
      {
        h2: "Ordre des opérations",
        body: "Commandez → attendez tous les QC → validez → estimez → choisissez la ligne → payez le shipping. Ne précipitez pas le submit.",
      },
      {
        h2: "Budget",
        body: "Article + frais agent + shipping international. Le shipping peut dépasser le prix unitaire sur les pièces légères.",
      },
    ],
    related: ["tariffless-europe", "qc-checklist", "premiere-commande"],
  },
  {
    slug: "w2c-guide",
    title: "W2C : trouver le bon lien vendeur",
    h1: "W2C — Where to Cop, expliqué simplement",
    description:
      "W2C signifie trouver le lien Yupoo / Weidian / Taobao d’un article. Méthode et précautions.",
    intent: "howto",
    intro:
      "W2C (Where to Cop) = « où trouver ce modèle ». Dans les communautés, on partage des liens plutôt que des captures floues.",
    sections: [
      {
        h2: "Sources de liens",
        body: "Threads Reddit, Discord, feuilles partagées, et catalogues Yupoo. Vérifiez toujours la date du lien : les albums disparaissent.",
      },
      {
        h2: "Qualité du W2C",
        body: "Un bon W2C inclut lien direct, batch, prix indicatif, et idéalement des QC récents. Sans ça, recommencez la recherche.",
      },
      {
        h2: "Après le lien",
        body: "Ouvrez dans l’agent ou contactez le vendeur WhatsApp. Comparez 2–3 sources avant de payer.",
      },
    ],
    related: ["comment-commander-yupoo", "yupoo-vs-weidian", "qc-checklist"],
  },
  {
    slug: "eviter-arnaques-vendeurs",
    title: "Éviter les arnaques vendeurs",
    h1: "Éviter les arnaques : signaux et réflexes",
    description:
      "Red flags vendeurs, paiements risqués, catalogues fantômes — checklist sécurité acheteur FR.",
    intent: "howto",
    intro:
      "Les arnaques existent. Quelques réflexes simples éliminent la majorité des mauvais dossiers.",
    sections: [
      {
        h2: "Red flags",
        body: "Paiement uniquement crypto sans preuve, refus total de QC, urgence artificielle, et profils créés la veille.",
      },
      {
        h2: "Réflexes",
        body: "Passer par un agent quand c’est possible, croiser le vendeur sur plusieurs fils, garder les captures d’écran des accords.",
      },
      {
        h2: "Si ça sent mauvais",
        body: "Arrêtez. Un autre vendeur existe toujours. LuxFind privilégie la prudence à la vitesse.",
      },
    ],
    related: ["paiement-securise", "whatsapp-vendeur-chine", "agent-france"],
  },
  {
    slug: "yupoo-vs-weidian",
    title: "Yupoo vs Weidian : quelles différences",
    h1: "Yupoo ou Weidian ?",
    description:
      "Yupoo = vitrine photos. Weidian / Taobao = fiches produit souvent passées via agent.",
    intent: "howto",
    intro:
      "Les deux coexistent. Yupoo sert de lookbook ; Weidian et Taobao offrent des fiches plus « e-commerce » pour les agents.",
    sections: [
      {
        h2: "Yupoo",
        body: "Idéal pour parcourir des catalogues marque / modèle. Contact vendeur souvent WhatsApp. Moins adapté au checkout automatique.",
      },
      {
        h2: "Weidian / Taobao",
        body: "Liens collés dans l’agent, prix affichés, variations taille. Certains vendeurs publient les deux.",
      },
      {
        h2: "En pratique",
        body: "Trouvez le modèle sur Yupoo, demandez le lien agent si besoin, ou achetez en direct WA selon votre tolérance au risque.",
      },
    ],
    related: ["comment-commander-yupoo", "w2c-guide", "agent-france"],
  },
  {
    slug: "paiement-securise",
    title: "Paiement plus sûr vers un vendeur ou un agent",
    h1: "Payer plus sereinement",
    description:
      "Agent vs direct, preuves écrites, montants échelonnés — bonnes pratiques paiement.",
    intent: "howto",
    intro:
      "Aucun paiement n’est sans risque. L’objectif est de réduire la surface d’exposition.",
    sections: [
      {
        h2: "Via agent",
        body: "Vous rechargez un solde agent. L’argent ne part pas directement au premier numéro inconnu. C’est souvent le meilleur début.",
      },
      {
        h2: "En direct",
        body: "Exigez un récap écrit (modèle, prix, adresse). Évitez les méthodes irréversibles sans historique. Commencez petit.",
      },
      {
        h2: "Preuves",
        body: "Conservez chats, reçus, tracking. En cas de litige agent, le dossier accélère le support.",
      },
    ],
    related: ["eviter-arnaques-vendeurs", "whatsapp-vendeur-chine", "premiere-commande"],
  },
  {
    slug: "tailles-sacs-luxe",
    title: "Guide des tailles sacs",
    h1: "Choisir la bonne taille de sac",
    description:
      "CM, litres, usage quotidien : comment lire les tailles sur catalogues vendeurs.",
    intent: "howto",
    intro:
      "Une erreur de taille est la première cause de déception. Les catalogues mélangent souvent noms marketing et cm réels.",
    sections: [
      {
        h2: "Mesures",
        body: "Demandez L × H × P en cm et comparez à un sac que vous possédez. Les photos flatteuses trompent.",
      },
      {
        h2: "Usage",
        body: "Quotidien dense → volume généreux. Soirée → format compact. Notez si vous portez surtout à l’épaule ou crossbody.",
      },
      {
        h2: "QC taille",
        body: "Sur le QC, vérifiez qu’une règle apparaît ou demandez les mesures prises à l’entrepôt.",
      },
    ],
    related: ["neverfull", "birkin", "qc-checklist"],
  },
  {
    slug: "premiere-commande",
    title: "Première commande depuis la France",
    h1: "Votre première commande, sans stress",
    description:
      "Parcours recommandé première fois : agent, 1–2 articles, QC, ligne adaptée France.",
    intent: "howto",
    intro:
      "La première commande doit rester simple : peu d’articles, agent, checklist QC, ligne d’envoi claire.",
    sections: [
      {
        h2: "Plan en 6 étapes",
        body: "1) Choisir 1–2 modèles. 2) Trouver W2C fiable. 3) Commander via agent. 4) Valider QC. 5) Estimer shipping. 6) Expédier et tracker.",
      },
      {
        h2: "Erreurs fréquentes",
        body: "Trop d’articles d’un coup, ignorer le QC, choisir la ligne la moins chère sans lire les retours France.",
      },
      {
        h2: "Après réception",
        body: "Notez ce qui a bien marché (vendeur, agent, ligne). Votre deuxième haul ira deux fois plus vite.",
      },
    ],
    related: ["agent-france", "qc-checklist", "comment-commander-yupoo"],
  },
  {
    slug: "photos-qc-lire",
    title: "Savoir lire une photo QC",
    h1: "Lire une photo QC comme un acheteur expérimenté",
    description:
      "Lumière, angles, zoom logo, défauts acceptables vs bloquants — guide lecture QC.",
    intent: "howto",
    intro:
      "Une belle photo ne dit pas tout. Apprendre à lire un QC évite les validations émotionnelles.",
    sections: [
      {
        h2: "Lumière et angle",
        body: "Demandez une lumière neutre. Les flashes durs cachent les défauts de teinte. Multipliez les angles.",
      },
      {
        h2: "Zoom utile",
        body: "Logo, couture, coin, fermoir. Si le vendeur envoie uniquement des vues lointaines, reclamez.",
      },
      {
        h2: "Défauts",
        body: "Fils, asymétrie légère, micro-rayure hardware : notez et décidez selon le prix. Défaut structurel = RL.",
      },
    ],
    related: ["qc-checklist", "sneakers-qc", "love-bracelet"],
  },
  {
    slug: "telegram-guides",
    title: "Guides et canaux Telegram",
    h1: "Telegram pour rester informé (sans le bruit)",
    description:
      "Pourquoi un canal discret aide : alertes QC, guides, questions — LuxFind FR.",
    intent: "howto",
    intro:
      "Telegram concentre les échanges rapides. Un canal bien tenu bat un fil Reddit saturé — à condition d’éviter le spam.",
    sections: [
      {
        h2: "À quoi ça sert",
        body: "Mises à jour de guides, rappels checklist, réponses aux questions fréquentes, et orientation vers les bonnes pages LuxFind.",
      },
      {
        h2: "Ce que ce n’est pas",
        body: "Pas une foire aux vendeurs non filtrés. La qualité du signal prime sur le volume.",
      },
      {
        h2: "Rejoindre",
        body: "Utilisez le bouton Contacter / Canal Telegram en bas de chaque page, ou le formulaire email si vous préférez.",
      },
    ],
    related: ["premiere-commande", "comment-commander-yupoo", "agent-france"],
  },
  {
    slug: "meilleur-agent-2026",
    title: "Quel agent choisir en 2026",
    h1: "Agents 2026 : comment comparer",
    description:
      "Critères de choix d’agent en 2026 : frais, QC, shipping France, support — sans classement payant.",
    intent: "howto",
    intro:
      "Il n’existe pas un « meilleur » agent universel. Il existe celui qui colle à votre usage France aujourd’hui.",
    sections: [
      {
        h2: "Critères",
        body: "Frais %, qualité photos QC, délais entrepôt, lignes vers FR, assurance, et réactivité du support.",
      },
      {
        h2: "Tester petit",
        body: "Commencez avec un article peu cher. Le vrai test, c’est le premier shipping reçu.",
      },
      {
        h2: "Migration",
        body: "Les agents évoluent. Gardez vos liens W2C exportables pour changer de plateforme si besoin.",
      },
    ],
    related: ["agent-france", "shipping-france-delais", "tariffless-europe"],
  },
  {
    slug: "shipping-france-delais",
    title: "Délais de livraison Chine → France",
    h1: "Délais réalistes Chine → France",
    description:
      "Entrepôt, ligne internationale, last-mile : à quoi s’attendre sur les délais.",
    intent: "howto",
    intro:
      "Les délais se décomposent : préparation vendeur, transit agent, ligne internationale, douane / hub, last-mile FR.",
    sections: [
      {
        h2: "Ordres de grandeur",
        body: "QC en quelques jours à deux semaines. International souvent 10–25 jours. Last-mile 1–5 jours une fois en France.",
      },
      {
        h2: "Retards fréquents",
        body: "Pics saisonniers, météo cargo, files hub, et week-ends. Un tracking « silencieux » quelques jours n’est pas forcément une perte.",
      },
      {
        h2: "Quand s’inquiéter",
        body: "Suivez les seuils de votre agent (souvent 30–45 jours). Ouvrez un ticket avec preuves plutôt qu’un spam de messages.",
      },
    ],
    related: ["livraison-colissimo-chine", "douane-france", "haul-france"],
  },

  // ── Batch 2: Marques ─────────────────────────────────────────────
  {
    slug: "louis-vuitton",
    title: "Guide Louis Vuitton — LuxFind FR",
    h1: "Guide discret Louis Vuitton",
    description:
      "Vendeur, QC, livraison FR pour modèles LV — Neverfull, Speedy et classiques.",
    intent: "brand",
    brands: ["louis_vuitton"],
    intro:
      "Comment identifier un vendeur sérieux, lire un QC et anticiper la livraison en France — sans bruit.",
    sections: [
      {
        h2: "Repères vendeur",
        body: "Yupoo + WhatsApp cohérents, QC historiques sur les mêmes modèles, pas de catalogue infini sans preuve.",
      },
      {
        h2: "QC LV",
        body: "Embossing, symétrie monogram, coutures, hardware. Comparez plusieurs photos du même batch.",
      },
      {
        h2: "Livraison FR",
        body: "Agent recommandé pour une première pièce. Estimez le shipping avant validation finale.",
      },
    ],
    related: ["neverfull", "comment-commander-yupoo", "qc-checklist"],
  },
  {
    slug: "hermes",
    title: "Guide Hermès — LuxFind FR",
    h1: "Guide discret Hermès",
    description: "Birkin, Kelly, Constance : repères QC et vendeurs pour acheteurs FR.",
    intent: "brand",
    brands: ["hermes"],
    intro:
      "Birkin, Kelly, Constance : repères qualité et red flags vendeurs pour acheteurs FR.",
    sections: [
      {
        h2: "Points QC",
        body: "Cuir, ferroir, symétrie, couture sellier. Exigez lumière naturelle et détails fermoir.",
      },
      {
        h2: "Vendeur",
        body: "Méfiez-vous des catalogues trop larges sans photos atelier. Croisez les retours community.",
      },
      {
        h2: "Parcours",
        body: "W2C → QC strict → agent ou WA. Pour Hermès, la patience bat la précipitation.",
      },
    ],
    related: ["birkin", "photos-qc-lire", "eviter-arnaques-vendeurs"],
  },
  {
    slug: "chanel",
    title: "Guide Chanel — LuxFind FR",
    h1: "Guide discret Chanel",
    description: "Classic, Flap, 22 — checklist QC et conseils acheteurs France.",
    intent: "brand",
    brands: ["chanel"],
    intro: "Flap bags, Classic et 22 — checklist discrète pour acheteurs exigeants.",
    sections: [
      {
        h2: "QC clé",
        body: "Alignement matelassé, poids hardware, stickers / série sur photos, finition chaînes.",
      },
      {
        h2: "Offres trop belles",
        body: "Sans historique communautaire, passez votre chemin. Demandez des QC datés.",
      },
      {
        h2: "Suite",
        body: "Reliez ce guide à la checklist QC générale et au parcours première commande.",
      },
    ],
    related: ["qc-checklist", "premiere-commande", "sac-bandeouliere"],
  },
  {
    slug: "dior",
    title: "Guide Dior — LuxFind FR",
    h1: "Guide discret Dior",
    description: "Book Tote, Saddle, Lady Dior — contrôles broderie et finitions.",
    intent: "brand",
    brands: ["dior"],
    intro: "Book Tote, Saddle, Lady Dior — points de contrôle et canaux FR.",
    sections: [
      {
        h2: "Book Tote",
        body: "Densité et régularité de la broderie. Demandez des zooms logo et lining.",
      },
      {
        h2: "Autres modèles",
        body: "Saddle : forme et hardware. Lady Dior : cannage et poignées.",
      },
      {
        h2: "Communauté",
        body: "Croisez les QC récents avant d’acheter un batch « trop parfait ».",
      },
    ],
    related: ["book-tote", "photos-qc-lire", "agent-france"],
  },
  {
    slug: "cartier",
    title: "Guide Cartier — LuxFind FR",
    h1: "Guide discret Cartier",
    description: "Love, Juste un Clou, Trinity — poids, gravures, QC vidéo.",
    intent: "brand",
    brands: ["cartier"],
    intro: "Love, Juste un Clou, Trinity — focus finition métal et gravures.",
    sections: [
      {
        h2: "Filtres QC",
        body: "Poids, gravure intérieure, finition des vis / charnières. Vidéo 360° recommandée.",
      },
      {
        h2: "Vendeur",
        body: "Préférez les spécialisés joaillerie aux généralistes fourre-tout.",
      },
      {
        h2: "Réception",
        body: "Comparez à des mesures officielles de référence (taille, épaisseur).",
      },
    ],
    related: ["love-bracelet", "photos-qc-lire", "paiement-securise"],
  },
  {
    slug: "gucci",
    title: "Guide Gucci — LuxFind FR",
    h1: "Guide discret Gucci",
    description: "GG Marmont, Dionysus, Horsebit — symétrie et cuir.",
    intent: "brand",
    brands: ["gucci"],
    intro: "GG Marmont, Dionysus, Horsebit — checklist qualité pour la France.",
    sections: [
      {
        h2: "QC",
        body: "Symétrie monogramme, qualité cuir, hardware Double G, alignement matelassé.",
      },
      {
        h2: "Comparaison",
        body: "Demandez plusieurs QC du même modèle chez le vendeur avant de trancher.",
      },
      {
        h2: "Suivi",
        body: "Documentez vos échanges pour capitaliser sur la prochaine commande.",
      },
    ],
    related: ["sac-bandeouliere", "qc-checklist", "w2c-guide"],
  },
  {
    slug: "rolex",
    title: "Guide Rolex — LuxFind FR",
    h1: "Guide discret montres Rolex",
    description: "Repères QC montres : poids, gravures, bracelet — prudence maximale.",
    intent: "brand",
    brands: ["rolex"],
    intro:
      "Les montres exigent un QC plus strict : poids, finitions bracelet, gravures, et vendeur spécialisé.",
    sections: [
      {
        h2: "QC montre",
        body: "Photos macro lunette, fond, fermoir. Demandez mouvement annoncé et poids.",
      },
      {
        h2: "Risque",
        body: "Catégorie sensible : privilégiez agent + vendeurs avec long historique.",
      },
      {
        h2: "Attentes",
        body: "Lisez plusieurs QC community avant tout paiement direct.",
      },
    ],
    related: ["eviter-arnaques-vendeurs", "photos-qc-lire", "agent-france"],
  },
  {
    slug: "saint-laurent",
    title: "Guide Saint Laurent — LuxFind FR",
    h1: "Guide discret Saint Laurent",
    description: "Sac de Jour, Lou, Cassandra — points QC et parcours FR.",
    intent: "brand",
    brands: ["saint_laurent"],
    intro: "Lignes YSL les plus demandées : structure, logo, cuir et hardware doré.",
    sections: [
      {
        h2: "QC",
        body: "Embossing YSL, coins, fermoirs, teinte cuir sous lumière neutre.",
      },
      {
        h2: "Taille",
        body: "Vérifiez les cm : les noms marketing varient selon les saisons.",
      },
      {
        h2: "Achat",
        body: "W2C récent + QC + agent pour une première YSL.",
      },
    ],
    related: ["tailles-sacs-luxe", "qc-checklist", "comment-commander-yupoo"],
  },
  {
    slug: "bottega-veneta",
    title: "Guide Bottega Veneta — LuxFind FR",
    h1: "Guide discret Bottega Veneta",
    description: "Intrecciato, Jodie, Cassette — lecture du tressage et du cuir.",
    intent: "brand",
    brands: ["bottega_veneta"],
    intro: "Le tressage Intrecciato est le juge de paix. Un QC flou ne suffit pas.",
    sections: [
      {
        h2: "QC tressage",
        body: "Régularité, tension, teinte homogène. Zooms obligatoires.",
      },
      {
        h2: "Formes",
        body: "Jodie : nœud et chute. Cassette : matelassé et chaîne.",
      },
      {
        h2: "Parcours",
        body: "Comme toujours : vendeur crédible, QC, shipping France anticipé.",
      },
    ],
    related: ["photos-qc-lire", "sac-bandeouliere", "premiere-commande"],
  },
  {
    slug: "fendi",
    title: "Guide Fendi — LuxFind FR",
    h1: "Guide discret Fendi",
    description: "Baguette, Peekaboo, FF — checklist logo et finitions.",
    intent: "brand",
    brands: ["fendi"],
    intro: "Motifs FF et hardware : deux zones où les QC médiocres se voient tout de suite.",
    sections: [
      {
        h2: "QC",
        body: "Alignement FF, coutures, gravures hardware, intérieur.",
      },
      {
        h2: "Modèles",
        body: "Baguette et Peekaboo restent les plus cherchés — exigez des QC datés.",
      },
      {
        h2: "Achat FR",
        body: "Agent + estimation shipping avant validation.",
      },
    ],
    related: ["w2c-guide", "qc-checklist", "agent-france"],
  },
  {
    slug: "celine",
    title: "Guide Celine — LuxFind FR",
    h1: "Guide discret Celine",
    description: "Triomphe, Luggage, Ava — structure et logo.",
    intent: "brand",
    brands: ["celine"],
    intro: "Lignes Celine : sobriété du logo et qualité du cuir font la différence au QC.",
    sections: [
      {
        h2: "QC",
        body: "Triomphe metal, teinte cuir, coins, fermetures.",
      },
      {
        h2: "Taille",
        body: "Mesurez : les Mini / Small se confondent sur photos.",
      },
      {
        h2: "Suite",
        body: "Reliez à tailles sacs et checklist QC.",
      },
    ],
    related: ["tailles-sacs-luxe", "qc-checklist", "louis-vuitton"],
  },
  {
    slug: "van-cleef",
    title: "Guide Van Cleef — LuxFind FR",
    h1: "Guide discret Van Cleef & Arpels",
    description: "Alhambra et motifs trèfle — QC bijou minutieux.",
    intent: "brand",
    brands: ["van_cleef_arpels"],
    intro: "Motifs Alhambra : symétrie, motif, fermoir et finition des contours.",
    sections: [
      {
        h2: "QC bijou",
        body: "Macro sur motif, chaîne, fermoir. Demandez poids si possible.",
      },
      {
        h2: "Vendeur",
        body: "Spécialiste joaillerie plutôt que catalogue sneakers + bijoux mélangés.",
      },
      {
        h2: "Prudence",
        body: "Même parcours : preuves écrites, QC, pas d’urgence artificielle.",
      },
    ],
    related: ["cartier", "love-bracelet", "eviter-arnaques-vendeurs"],
  },

  // ── Batch 3: Modèles / niches ────────────────────────────────────
  {
    slug: "birkin",
    title: "Guide Birkin — points QC",
    h1: "Birkin : checklist QC essentielle",
    description: "Ferroir, cuir, couture, poignées — lire un QC Birkin.",
    intent: "model",
    brands: ["hermes"],
    intro: "La Birkin se joue sur des détails. Un QC incomplet ne permet pas de décider.",
    sections: [
      {
        h2: "Focus",
        body: "Ferroir, clous, symétrie des poignées, grain du cuir, couture.",
      },
      {
        h2: "Taille",
        body: "25 / 30 / 35 : confirmez les cm. Les photos trompent l’échelle.",
      },
      {
        h2: "Parcours",
        body: "Voir aussi le guide Hermès et la lecture de photos QC.",
      },
    ],
    related: ["hermes", "photos-qc-lire", "tailles-sacs-luxe"],
  },
  {
    slug: "neverfull",
    title: "Guide Neverfull — QC et tailles",
    h1: "Neverfull : MM, GM et QC",
    description: "Neverfull LV : tailles, monogram, poignées, intérieur.",
    intent: "model",
    brands: ["louis_vuitton"],
    intro: "La Neverfull est un classique. Les erreurs de taille et de teinte sont fréquentes.",
    sections: [
      {
        h2: "Tailles",
        body: "PM / MM / GM — demandez L×H×P. Comparez à une tote que vous avez.",
      },
      {
        h2: "QC",
        body: "Alignement monogram, poignées, rivets, pochette intérieure si incluse.",
      },
      {
        h2: "Achat",
        body: "W2C récent + agent pour une première Neverfull.",
      },
    ],
    related: ["louis-vuitton", "tailles-sacs-luxe", "premiere-commande"],
  },
  {
    slug: "book-tote",
    title: "Guide Book Tote Dior — broderie QC",
    h1: "Book Tote : contrôler la broderie",
    description: "Densité des points, logo, forme — QC Book Tote.",
    intent: "model",
    brands: ["dior"],
    intro: "Sur Book Tote, la broderie décide de tout. Exigez des zooms nets.",
    sections: [
      {
        h2: "Broderie",
        body: "Densité, régularité, tension du tissu. Rejetez les flous.",
      },
      {
        h2: "Structure",
        body: "Forme ouverte, poignées, intérieur propre.",
      },
      {
        h2: "Suite",
        body: "Guide Dior + checklist QC générale.",
      },
    ],
    related: ["dior", "qc-checklist", "photos-qc-lire"],
  },
  {
    slug: "love-bracelet",
    title: "Guide bracelet Love Cartier — QC",
    h1: "Bracelet Love : QC métal et vis",
    description: "Poids, gravure, vis, finition — points de contrôle Love.",
    intent: "model",
    brands: ["cartier"],
    intro: "Le Love se juge au poids, à la gravure et à la précision des vis / charnières.",
    sections: [
      {
        h2: "QC",
        body: "Macro gravure intérieure, tour complet, tournevis / vis si fourni.",
      },
      {
        h2: "Taille",
        body: "Confirmez le tour de poignet. Les échanges bijoux sont plus délicats.",
      },
      {
        h2: "Achat",
        body: "Vendeur joaillerie + preuves écrites.",
      },
    ],
    related: ["cartier", "paiement-securise", "photos-qc-lire"],
  },
  {
    slug: "sneakers-qc",
    title: "QC sneakers — guide lecture",
    h1: "Lire un QC sneakers",
    description: "Shape, embossing, semelle, glue — checklist sneakers.",
    intent: "model",
    intro: "Les sneakers ont leur propre grammaire QC : shape, toebox, embossing, glue stains.",
    sections: [
      {
        h2: "Angles",
        body: "Profil, 3/4, arrière, semelle, intérieur tongue, close-up logo.",
      },
      {
        h2: "Défauts fréquents",
        body: "Toebox trop haute, asymétrie, surplus de colle, teinte off.",
      },
      {
        h2: "Décision",
        body: "Comparez à des QC community du même batch avant GL.",
      },
    ],
    related: ["qc-checklist", "photos-qc-lire", "w2c-guide"],
  },
  {
    slug: "sac-bandeouliere",
    title: "Sacs bandoulière — guide choix",
    h1: "Choisir un sac bandoulière",
    description: "Confort, longueur chaîne, poids hardware — guide pratique.",
    intent: "model",
    intro: "Le bandoulière quotidien se joue sur le confort autant que sur le look.",
    sections: [
      {
        h2: "Porté",
        body: "Longueur de chaîne / bandoulière, poids total, ouverture une main.",
      },
      {
        h2: "QC",
        body: "Attaches chaîne, coins, fermeture, usure simulée du hardware.",
      },
      {
        h2: "Marques",
        body: "Voir aussi Gucci, Chanel, Bottega selon le style recherché.",
      },
    ],
    related: ["gucci", "chanel", "tailles-sacs-luxe"],
  },
  {
    slug: "speedy",
    title: "Guide Speedy LV — tailles et QC",
    h1: "Speedy : 25, 30, 35",
    description: "Speedy Louis Vuitton — tailles, bandoulière, points QC.",
    intent: "model",
    brands: ["louis_vuitton"],
    intro: "La Speedy reste un pilier. Confirmez taille et présence de bandoulière.",
    sections: [
      {
        h2: "Tailles",
        body: "25 / 30 / 35 — cm réels > nom marketing.",
      },
      {
        h2: "QC",
        body: "Poignées Vachetta (teinte), zip, monogram aligné, rivets.",
      },
      {
        h2: "Parcours",
        body: "Guide LV + première commande.",
      },
    ],
    related: ["louis-vuitton", "neverfull", "premiere-commande"],
  },
  {
    slug: "kelly",
    title: "Guide Kelly Hermès — QC",
    h1: "Kelly : points de contrôle",
    description: "Sellier vs retourné, ferroir, poignées — QC Kelly.",
    intent: "model",
    brands: ["hermes"],
    intro: "La Kelly demande la même rigueur QC qu’une Birkin, avec ses codes propres.",
    sections: [
      {
        h2: "Construction",
        body: "Clarifiez sellier / retourné avec le vendeur. Ça change le rendu couture.",
      },
      {
        h2: "QC",
        body: "Ferroir, clous, poignée, symétrie rabat.",
      },
      {
        h2: "Suite",
        body: "Guide Hermès + Birkin pour comparer.",
      },
    ],
    related: ["hermes", "birkin", "photos-qc-lire"],
  },
  {
    slug: "classic-flap",
    title: "Guide Classic Flap Chanel — QC",
    h1: "Classic Flap : checklist",
    description: "Matelassé, chaîne, CC — points QC Classic Flap.",
    intent: "model",
    brands: ["chanel"],
    intro: "Classic Flap : l’alignement matelassé et le tombé de chaîne sont décisifs.",
    sections: [
      {
        h2: "QC",
        body: "Losanges alignés, logo CC, poids chaîne, couture intérieure.",
      },
      {
        h2: "Taille",
        body: "Mini / small / medium — confirmez cm et photos avec échelle.",
      },
      {
        h2: "Parcours",
        body: "Guide Chanel + checklist QC.",
      },
    ],
    related: ["chanel", "qc-checklist", "sac-bandeouliere"],
  },
  {
    slug: "marmont",
    title: "Guide GG Marmont Gucci — QC",
    h1: "GG Marmont : lire le QC",
    description: "Matelassé, Double G, chaîne — checklist Marmont.",
    intent: "model",
    brands: ["gucci"],
    intro: "Le Marmont se juge sur le matelassé et le Double G. Zooms obligatoires.",
    sections: [
      {
        h2: "QC",
        body: "Régularité matelassé, logo, teinte cuir, fermeture.",
      },
      {
        h2: "Formats",
        body: "Super mini à large — validez l’usage quotidien vs soirée.",
      },
      {
        h2: "Suite",
        body: "Guide Gucci + sacs bandoulière.",
      },
    ],
    related: ["gucci", "sac-bandeouliere", "photos-qc-lire"],
  },
];

export function getPage(slug: string): LuxfindPage | undefined {
  return LUXFIND_PAGES.find((p) => p.slug === slug);
}

export function pagesByIntent(intent: LuxfindPage["intent"]): LuxfindPage[] {
  return LUXFIND_PAGES.filter((p) => p.intent === intent);
}

export function relatedPages(page: LuxfindPage): LuxfindPage[] {
  return page.related
    .map((slug) => getPage(slug))
    .filter((p): p is LuxfindPage => Boolean(p));
}

/** @deprecated use LUXFIND_PAGES / getPage — kept for any leftover imports */
export const BRAND_GUIDES = pagesByIntent("brand").map((p) => ({
  slug: p.slug,
  name: p.h1.replace(/^Guide discret\s+/i, "").replace(/\s*—.*$/, ""),
  headline: p.h1,
  intro: p.intro,
  tips: p.sections.map((s) => s.body.slice(0, 120)),
}));

export function getBrand(slug: string) {
  return BRAND_GUIDES.find((b) => b.slug === slug);
}
