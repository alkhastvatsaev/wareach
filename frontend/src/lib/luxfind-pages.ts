/** LuxFind FR — all SEO guide pages (intent + brand + model + buy). */

export type PageSection = { h2: string; body: string };

export type LuxfindPage = {
  slug: string;
  title: string;
  h1: string;
  description: string;
  intent: "howto" | "brand" | "model" | "buy";
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

  // ── Batch 4: Intention d'achat (lexical réplique / marques) ───────
  {
    slug: "acheter-louis-vuitton-replique",
    title: "Acheter Louis Vuitton réplique — guide France",
    h1: "Acheter une réplique Louis Vuitton en France",
    description:
      "Acheter Louis Vuitton réplique : Yupoo, WhatsApp vendeur, agent, QC et livraison France. Guide LuxFind FR.",
    intent: "buy",
    brands: ["louis_vuitton"],
    intro:
      "Vous cherchez où acheter une réplique Louis Vuitton depuis la France. Ce guide explique le parcours réel : catalogue Yupoo, contact vendeur ou agent, contrôle QC, puis livraison.",
    sections: [
      {
        h2: "Où les acheteurs FR passent commande",
        body: "Personne n’achète « sur » Yupoo comme sur une boutique. On choisit le modèle (Neverfull, Speedy, etc.), puis on commande via un agent (CNFans, Sugargoo, Kakobuy) ou en direct WhatsApp vendeur Chine. Le mot-clé acheter Louis Vuitton réplique mène surtout à ces deux chemins.",
      },
      {
        h2: "QC avant de valider",
        body: "Demandez des photos QC : monogram, coutures, hardware, embossing. Comparez plusieurs lots. Sans QC, vous achetez à l’aveugle — même si le prix est « pas cher ».",
      },
      {
        h2: "Livraison France",
        body: "Estimez le shipping avant le paiement final. Lignes tax-free / EU et last-mile Colissimo sont souvent discutées. Pour un contact discret et un parcours guidé, utilisez Telegram ou le formulaire ci-dessous.",
      },
    ],
    related: ["louis-vuitton", "comment-commander-yupoo", "sac-louis-vuitton-pas-cher"],
  },
  {
    slug: "acheter-hermes-replique",
    title: "Acheter Hermès réplique — Birkin Kelly France",
    h1: "Acheter une réplique Hermès (Birkin, Kelly)",
    description:
      "Acheter Hermès réplique en France : vendeur Yupoo, QC cuir/ferroir, agent ou WhatsApp. Guide discret.",
    intent: "buy",
    brands: ["hermes"],
    intro:
      "Acheter une réplique Hermès demande plus de rigueur QC que la moyenne : cuir, ferroir, couture. Voici le parcours utiliséé en France.",
    sections: [
      {
        h2: "Trouver un vendeur crédible",
        body: "Catalogue Yupoo + historique community. Méfiez-vous des offres Birkin « trop belles » sans photos atelier. Le contact WhatsApp doit rester cohérent avec le Yupoo.",
      },
      {
        h2: "QC Hermès",
        body: "Lumière naturelle, détails ferroir, poignées, grain. Une vidéo 360° aide. RL si défaut structurel.",
      },
      {
        h2: "Commander depuis la France",
        body: "Agent pour sécuriser le paiement, ou direct WA si vous assumez le risque. Contactez LuxFind pour un cadrage discret.",
      },
    ],
    related: ["hermes", "copie-hermes-birkin", "qc-checklist"],
  },
  {
    slug: "acheter-chanel-replique",
    title: "Acheter Chanel réplique — Classic Flap France",
    h1: "Acheter une réplique Chanel en France",
    description:
      "Acheter Chanel réplique : Classic Flap, matelassé, QC, Yupoo et livraison France.",
    intent: "buy",
    brands: ["chanel"],
    intro:
      "Pour acheter une réplique Chanel, le marché FR regarde surtout Classic Flap et 22. Le QC du matelassé et du hardware décide.",
    sections: [
      {
        h2: "Parcours d’achat",
        body: "W2C Yupoo / Weidian → agent ou WhatsApp → QC → shipping France. Évitez les sites « boutique réplique » opaques sans QC.",
      },
      {
        h2: "Points QC Chanel",
        body: "Alignement losanges, poids chaîne, logo CC, stickers. Demandez des zooms nets.",
      },
      {
        h2: "Aide",
        body: "Guides pratiques LuxFind + contact Telegram si vous voulez valider un vendeur avant de payer.",
      },
    ],
    related: ["chanel", "classic-flap", "yupoo-chanel"],
  },
  {
    slug: "acheter-dior-replique",
    title: "Acheter Dior réplique — Book Tote France",
    h1: "Acheter une réplique Dior en France",
    description:
      "Acheter Dior réplique : Book Tote, Saddle, broderie QC, agent et livraison FR.",
    intent: "buy",
    brands: ["dior"],
    intro:
      "Acheter une réplique Dior (Book Tote en tête) : la broderie se juge au zoom. Voici comment les acheteurs FR procèdent.",
    sections: [
      {
        h2: "Où commander",
        body: "Yupoo pour le lookbook, puis agent ou vendeur WhatsApp. Le mot acheter Dior réplique correspond à ce flux, pas à une marketplace classique.",
      },
      {
        h2: "QC Book Tote et autres",
        body: "Densité broderie, logo, lining. Saddle et Lady Dior : forme et hardware.",
      },
      {
        h2: "France",
        body: "Anticipez douane / shipping. Contact LuxFind pour le parcours pas à pas.",
      },
    ],
    related: ["dior", "book-tote", "agent-france"],
  },
  {
    slug: "acheter-gucci-replique",
    title: "Acheter Gucci réplique — Marmont France",
    h1: "Acheter une réplique Gucci en France",
    description:
      "Acheter Gucci réplique : GG Marmont, Dionysus, QC cuir et Double G. Guide France.",
    intent: "buy",
    brands: ["gucci"],
    intro:
      "Pour acheter une réplique Gucci, Marmont et Dionysus dominent les recherches. Symétrie monogram et cuir sont les filtres QC.",
    sections: [
      {
        h2: "Acheter sans se faire avoir",
        body: "Croisez Yupoo + retours community. Prix irréaliste + pas de QC = stop. Agent recommandé en première commande.",
      },
      {
        h2: "QC Gucci",
        body: "Double G, matelassé, teinte cuir, chaînes. Plusieurs angles obligatoires.",
      },
      {
        h2: "Contact",
        body: "Telegram ou formulaire pour être guidé avant paiement.",
      },
    ],
    related: ["gucci", "marmont", "eviter-arnaques-vendeurs"],
  },
  {
    slug: "acheter-cartier-replique",
    title: "Acheter Cartier réplique — Love bracelet France",
    h1: "Acheter une réplique Cartier en France",
    description:
      "Acheter Cartier réplique : Love, Juste un Clou, QC poids et gravures. Guide FR.",
    intent: "buy",
    brands: ["cartier"],
    intro:
      "Acheter une réplique Cartier (Love, Clou, Trinity) : le métal et les gravures se contrôlent en macro. Prudence maximale.",
    sections: [
      {
        h2: "Parcours",
        body: "Vendeur joaillerie Yupoo / WA, ou agent. Évitez les catalogues sneakers + bijoux mélangés sans preuves.",
      },
      {
        h2: "QC bijou",
        body: "Poids, gravure intérieure, finition vis. Vidéo 360° fortement conseillée.",
      },
      {
        h2: "Paiement",
        body: "Preuves écrites, montants raisonnables. Contact LuxFind si besoin d’un second regard.",
      },
    ],
    related: ["cartier", "love-bracelet", "paiement-securise"],
  },
  {
    slug: "acheter-rolex-replique",
    title: "Acheter Rolex réplique — guide France",
    h1: "Acheter une réplique Rolex en France",
    description:
      "Acheter Rolex réplique : QC poids, lunette, bracelet — parcours agent / vendeur FR.",
    intent: "buy",
    brands: ["rolex"],
    intro:
      "Les recherches « acheter Rolex réplique » sont fréquentes ; le risque d’arnaque aussi. QC strict et vendeur spécialisé uniquement.",
    sections: [
      {
        h2: "Réalité du marché",
        body: "Pas de site magique. Yupoo / WA + QC macro. Beaucoup d’offres scam : refusez l’urgence et la crypto seule.",
      },
      {
        h2: "QC montre",
        body: "Lunette, fond, fermoir, poids, finition bracelet. Comparez à des QC community récents.",
      },
      {
        h2: "France",
        body: "Agent + tracking. Contact discret via Telegram LuxFind.",
      },
    ],
    related: ["rolex", "eviter-arnaques-vendeurs", "agent-france"],
  },
  {
    slug: "acheter-saint-laurent-replique",
    title: "Acheter Saint Laurent réplique — YSL France",
    h1: "Acheter une réplique Saint Laurent (YSL)",
    description:
      "Acheter Saint Laurent réplique : Lou, Sac de Jour, QC embossing YSL. Guide France.",
    intent: "buy",
    brands: ["saint_laurent"],
    intro:
      "Acheter une réplique Saint Laurent : focus logo YSL, cuir et structure. Parcours Yupoo → QC → France.",
    sections: [
      {
        h2: "Comment acheter",
        body: "Trouvez le W2C, commandez via agent ou WhatsApp, validez le QC (embossing, coins, hardware).",
      },
      {
        h2: "Tailles",
        body: "Confirmez les cm : Mini / Small se ressemblent sur photo.",
      },
      {
        h2: "Aide LuxFind",
        body: "Contactez-nous pour cadrer vendeur et shipping FR.",
      },
    ],
    related: ["saint-laurent", "tailles-sacs-luxe", "comment-commander-yupoo"],
  },
  {
    slug: "acheter-bottega-replique",
    title: "Acheter Bottega réplique — Intrecciato France",
    h1: "Acheter une réplique Bottega Veneta",
    description:
      "Acheter Bottega réplique : Jodie, Cassette, QC tressage Intrecciato. Guide FR.",
    intent: "buy",
    brands: ["bottega_veneta"],
    intro:
      "Pour acheter une réplique Bottega, le tressage Intrecciato est le juge de paix. Sans zoom QC, ne validez pas.",
    sections: [
      {
        h2: "Achat",
        body: "Yupoo lookbook → agent / WA → QC tressage → shipping France.",
      },
      {
        h2: "QC",
        body: "Régularité, tension, teinte. Jodie : nœud. Cassette : matelassé et chaîne.",
      },
      {
        h2: "Contact",
        body: "Formulaire ou Telegram pour un avis avant GL.",
      },
    ],
    related: ["bottega-veneta", "photos-qc-lire", "qc-checklist"],
  },
  {
    slug: "acheter-fendi-replique",
    title: "Acheter Fendi réplique — Baguette France",
    h1: "Acheter une réplique Fendi en France",
    description:
      "Acheter Fendi réplique : Baguette, Peekaboo, QC motif FF. Guide LuxFind.",
    intent: "buy",
    brands: ["fendi"],
    intro:
      "Acheter une réplique Fendi : Baguette et Peekaboo mènent les recherches. Alignement FF et hardware au QC.",
    sections: [
      {
        h2: "Parcours",
        body: "Comme pour les autres maisons : Yupoo, vendeur crédible, QC daté, agent pour la France.",
      },
      {
        h2: "QC Fendi",
        body: "Motif FF, coutures, gravures, intérieur. Rejetez les photos floues.",
      },
      {
        h2: "Suite",
        body: "Contact LuxFind + guides pratiques livraison / douane.",
      },
    ],
    related: ["fendi", "w2c-guide", "douane-france"],
  },
  {
    slug: "acheter-celine-replique",
    title: "Acheter Celine réplique — Triomphe France",
    h1: "Acheter une réplique Celine en France",
    description:
      "Acheter Celine réplique : Triomphe, Luggage, QC logo et cuir. Guide France.",
    intent: "buy",
    brands: ["celine"],
    intro:
      "Acheter une réplique Celine : sobriété du logo Triomphe et qualité cuir. Parcours FR standard Yupoo / agent.",
    sections: [
      {
        h2: "Où acheter",
        body: "Catalogues Yupoo + agent. Évitez les boutiques anonymes sans QC.",
      },
      {
        h2: "QC",
        body: "Métal Triomphe, teinte, coins, fermetures. Confirmez taille Mini vs Small.",
      },
      {
        h2: "Contact",
        body: "Telegram LuxFind pour valider le prochain pas.",
      },
    ],
    related: ["celine", "tailles-sacs-luxe", "premiere-commande"],
  },
  {
    slug: "acheter-van-cleef-replique",
    title: "Acheter Van Cleef réplique — Alhambra France",
    h1: "Acheter une réplique Van Cleef (Alhambra)",
    description:
      "Acheter Van Cleef réplique : Alhambra, QC motif et fermoir. Guide France.",
    intent: "buy",
    brands: ["van_cleef_arpels"],
    intro:
      "Acheter une réplique Van Cleef & Arpels (Alhambra) : QC bijou minutieux, vendeur spécialisé.",
    sections: [
      {
        h2: "Achat prudent",
        body: "WA / Yupoo joaillerie, preuves écrites, pas d’urgence. Agent si première fois.",
      },
      {
        h2: "QC Alhambra",
        body: "Symétrie motif, chaîne, fermoir, finition contours. Macro obligatoire.",
      },
      {
        h2: "Aide",
        body: "Contactez LuxFind avant de payer un vendeur inconnu.",
      },
    ],
    related: ["van-cleef", "cartier", "eviter-arnaques-vendeurs"],
  },
  {
    slug: "ou-acheter-replique-france",
    title: "Où acheter réplique France — Yupoo agent WhatsApp",
    h1: "Où acheter une réplique en France ?",
    description:
      "Où acheter réplique France : pas de marketplace miracle — Yupoo, agent, WhatsApp vendeur Chine. Guide clair.",
    intent: "buy",
    intro:
      "La question « où acheter réplique France » a une réponse nette : pas sur Amazon. Les acheteurs passent par Yupoo + agent ou WhatsApp vendeur, puis shipping vers la France.",
    sections: [
      {
        h2: "Les 2 canaux réels",
        body: "1) Agent (CNFans, Sugargoo, Kakobuy…) avec lien Yupoo/Weidian. 2) Contact direct WhatsApp du vendeur. Les « meilleurs sites réplique » qui vendent en euro carte sans QC sont souvent des arnaques.",
      },
      {
        h2: "Ce que LuxFind fait",
        body: "On explique le parcours, les red flags, le QC et la livraison FR. Contact Telegram / email pour être accompagné.",
      },
      {
        h2: "Marques",
        body: "LV, Hermès, Chanel, Dior, Gucci… voir les pages « acheter [marque] réplique ».",
      },
    ],
    related: ["meilleur-site-replique-france", "acheter-louis-vuitton-replique", "agent-france"],
  },
  {
    slug: "meilleur-site-replique-france",
    title: "Meilleur site réplique France — ce qu’il faut savoir",
    h1: "Meilleur site réplique France : la vraie réponse",
    description:
      "Meilleur site réplique France : Yupoo n’est pas une boutique. Agents, vendeurs WA, QC — guide LuxFind.",
    intent: "buy",
    intro:
      "Chercher le « meilleur site réplique France » mène souvent à des landing pages douteuses. Le setup fiable reste catalogue + agent/vendeur + QC.",
    sections: [
      {
        h2: "Pourquoi les « shops » échouent",
        body: "Promesses 1:1, paiement immédiat, zéro QC public. À fuir. Préférez un flux transparent avec photos entrepôt.",
      },
      {
        h2: "Stack recommandé",
        body: "Yupoo (vitrine) + agent actuel + ligne shipping France. LuxFind centralise les guides pour ne pas naviguer à l’aveugle.",
      },
      {
        h2: "Passer à l’action",
        body: "Choisissez une marque, lisez le guide QC, contactez-nous si vous voulez un cadrage.",
      },
    ],
    related: ["ou-acheter-replique-france", "comment-commander-yupoo", "premiere-commande"],
  },
  {
    slug: "sac-louis-vuitton-pas-cher",
    title: "Sac Louis Vuitton pas cher — réplique guide FR",
    h1: "Sac Louis Vuitton pas cher : ce que ça veut dire vraiment",
    description:
      "Sac Louis Vuitton pas cher / réplique : prix réalistes, QC Neverfull Speedy, éviter les arnaques. France.",
    intent: "buy",
    brands: ["louis_vuitton"],
    intro:
      "« Sac Louis Vuitton pas cher » est l’une des requêtes les plus tapées. Traduction acheteur : réplique / alternative Yupoo avec QC, pas une promo boutique officielle.",
    sections: [
      {
        h2: "Prix vs qualité",
        body: "Un prix cassé sans QC = risque. Comparez batch, photos et retours. Neverfull et Speedy sont les entrées les plus fréquentes.",
      },
      {
        h2: "Comment procéder",
        body: "W2C → agent ou WA → QC monogram → shipping. Voir aussi acheter Louis Vuitton réplique.",
      },
      {
        h2: "Contact",
        body: "Telegram LuxFind pour cadrer un premier achat sans précipitation.",
      },
    ],
    related: ["acheter-louis-vuitton-replique", "neverfull", "speedy"],
  },
  {
    slug: "replique-sac-luxe-qualite",
    title: "Réplique sac luxe qualité — QC et vendeurs",
    h1: "Réplique sac luxe : viser la qualité (QC)",
    description:
      "Réplique sac luxe qualité : checklist QC, vendeurs Yupoo, agent France. Guide LuxFind.",
    intent: "buy",
    intro:
      "« Réplique sac luxe qualité » / 1:1 / mirror : le ranking se joue au QC, pas au slogan vendeur.",
    sections: [
      {
        h2: "Qualité = preuves",
        body: "Photos macro, comparaison community, cohérence Yupoo/WA. Sans ça, « haute qualité » ne veut rien dire.",
      },
      {
        h2: "Parcours FR",
        body: "Agent + estimation shipping. Split de haul si besoin. Voir checklist QC.",
      },
      {
        h2: "Marques",
        body: "Pages acheter [marque] réplique pour LV, Chanel, Hermès, etc.",
      },
    ],
    related: ["qc-checklist", "ou-acheter-replique-france", "photos-qc-lire"],
  },
  {
    slug: "yupoo-louis-vuitton",
    title: "Yupoo Louis Vuitton — catalogues et commande FR",
    h1: "Yupoo Louis Vuitton : lire le catalogue et commander",
    description:
      "Yupoo Louis Vuitton : albums vendeurs, WhatsApp, agent, QC. Comment acheter depuis la France.",
    intent: "buy",
    brands: ["louis_vuitton"],
    intro:
      "Yupoo Louis Vuitton = vitrines photo de vendeurs. Pour acheter, il faut sortir de Yupoo (agent ou WhatsApp).",
    sections: [
      {
        h2: "Naviguer Yupoo",
        body: "Albums par modèle, onglet Contact, photos détail. Notez l’URL album exacte pour le W2C.",
      },
      {
        h2: "Passer commande",
        body: "Collez le lien dans l’agent ou écrivez au WA avec taille/couleur. QC avant shipping France.",
      },
      {
        h2: "LuxFind",
        body: "Guides + contact si vous voulez valider un vendeur LV.",
      },
    ],
    related: ["acheter-louis-vuitton-replique", "comment-commander-yupoo", "louis-vuitton"],
  },
  {
    slug: "yupoo-chanel",
    title: "Yupoo Chanel — catalogues Classic Flap FR",
    h1: "Yupoo Chanel : catalogues et achat France",
    description:
      "Yupoo Chanel : trouver Classic Flap, contacter vendeur, QC matelassé, livraison FR.",
    intent: "buy",
    brands: ["chanel"],
    intro:
      "Yupoo Chanel regroupe les lookbooks vendeurs. L’achat se fait ensuite via agent ou WhatsApp.",
    sections: [
      {
        h2: "Sur Yupoo",
        body: "Repérez Classic / 22, contact WA, photos chaîne et matelassé. Gardez le lien album.",
      },
      {
        h2: "QC et commande",
        body: "Même logique que acheter Chanel réplique : zooms, agent, shipping FR.",
      },
      {
        h2: "Contact",
        body: "Telegram ou formulaire LuxFind.",
      },
    ],
    related: ["acheter-chanel-replique", "chanel", "classic-flap"],
  },
  {
    slug: "replica-france-livraison",
    title: "Replica France livraison — délais et douane",
    h1: "Replica France : livraison et délais",
    description:
      "Replica France livraison : Colissimo, tax-free, délais Chine→FR, bonnes pratiques douane.",
    intent: "buy",
    intro:
      "Après l’achat réplique / replica, la livraison France est le sujet n°1 : délais, lignes, last-mile.",
    sections: [
      {
        h2: "Délais typiques",
        body: "QC + international + Colissimo : souvent 2–4 semaines. Pics saisonniers allongent.",
      },
      {
        h2: "Lignes",
        body: "Tax-free / tariffless vs éco. Estimez le poids avant de submit le haul.",
      },
      {
        h2: "Aide",
        body: "Guides douane + shipping LuxFind. Contact si votre colis stagne.",
      },
    ],
    related: ["shipping-france-delais", "douane-france", "livraison-colissimo-chine"],
  },
  {
    slug: "copie-hermes-birkin",
    title: "Copie Hermès Birkin — QC et achat France",
    h1: "Copie Hermès Birkin : comment les acheteurs FR procèdent",
    description:
      "Copie Hermès Birkin / réplique : Yupoo, QC ferroir cuir, agent WhatsApp, livraison France.",
    intent: "buy",
    brands: ["hermes"],
    intro:
      "« Copie Hermès Birkin » et « réplique Birkin » sont le même intent d’achat. Le succès dépend du QC, pas du mot utiliséé.",
    sections: [
      {
        h2: "Lexical = même parcours",
        body: "Copie, réplique, replica : Yupoo → vendeur/agent → QC → France. Voir aussi acheter Hermès réplique.",
      },
      {
        h2: "QC Birkin",
        body: "Ferroir, clous, poignées, grain. Taille 25/30/35 en cm réels.",
      },
      {
        h2: "Contact LuxFind",
        body: "Pour un cadrage avant paiement sur une Birkin.",
      },
    ],
    related: ["acheter-hermes-replique", "birkin", "hermes"],
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
