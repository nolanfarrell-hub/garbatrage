/**
 * Garbatrage — URL redirect Worker.
 *
 * Sits on the garbatrage.com zone and returns real 301s for the slug-rename map.
 * Every other request falls through to the origin (GitHub Pages) untouched.
 *
 * SAFETY RULES (keep forever):
 *  - EXACT path match only. No prefixes, no wildcards, no query matching.
 *  - Query string is preserved on the Location.
 *  - Everything unmatched MUST end in `return fetch(request)` — a Worker on the
 *    zone intercepts every request, so a bad fall-through breaks the whole site
 *    including /media/ and the live tape.
 *
 * The redirect map is GENERATED at deploy time from static/_redirects (single
 * source of truth) by scripts/gen_redirect_worker.sh — do not hand-edit REDIRECTS.
 */
const REDIRECTS = __REDIRECTS__;

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Exact-path match against the rename map.
    if (REDIRECTS.has(url.pathname)) {
      const target = REDIRECTS.get(url.pathname) + url.search; // preserve query
      return new Response(null, {
        status: 301,
        headers: {
          Location: target,
          "cache-control": "public, max-age=3600",
        },
      });
    }

    // Everything else: let the origin answer. This MUST stay unconditional.
    return fetch(request);
  },
};
