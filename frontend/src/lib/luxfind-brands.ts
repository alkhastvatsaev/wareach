/** @deprecated Prefer @/lib/luxfind-pages — kept for compatibility. */
export {
  BRAND_GUIDES,
  getBrand,
  LUXFIND_PAGES,
  getPage,
  pagesByIntent,
  relatedPages,
} from "./luxfind-pages";

export type { LuxfindPage, PageSection } from "./luxfind-pages";

export type BrandGuide = {
  slug: string;
  name: string;
  headline: string;
  intro: string;
  tips: string[];
};
