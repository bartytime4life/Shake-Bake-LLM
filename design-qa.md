# Workbench design QA

final result: passed

Selected target: the third displayed design chosen by the owner (November 4, 2026). Source visual: `/home/user/.codex/generated_images/01a1aa18-5744-7d43-86b0-2ce6efc72a49/exec-e5e4e955-8247-4fa9-a89e-f06b0f798e1e.png`; retained copy `.local/design/selected.png`.

Implementation: authenticated Chrome preview at numeric loopback, with synthetic source only. Desktop CSS viewport 1487 × 1058, reported DPR 1; source pixels 1487 × 1058, final native capture 1472 × 1047. The final comparison normalizes that near-identical pixel ratio to the reference dimensions. Intermediate captures taken during viewport transitions were discarded; a stretched capture was not used to judge fidelity. Completed evidence-only state, Local AI off, two exact source files, details closed.

## Comparison evidence and history

- `.local/design/comparison-first.png`: initial full comparison. P2 findings: undersized UI text/weak type hierarchy, recent-request text escaping the rail, and too much persistent notification/detail space above the evidence. The source-state comparison initially also included three discovery results rather than the reference's two selected files.
- Fixes: increased readable UI/code sizes and heading hierarchy, constrained the recent list, made noncritical notices temporary, moved source ranges into Model details and collapsed request/routing details. The comparison task explicitly selected the two real synthetic files in reference order; the default scanner was not altered to fake that result.
- `.local/design/comparison-final.png`: post-fix full-view comparison at the reference viewport, same task/completed state. `.local/design/comparison-composer.png` and `comparison-evidence.png` compare readable focused crops from both artifacts together.
- Phone CSS viewport 390 × 844, content width 375 with its scrollbar and no horizontal document overflow. `.local/design/mobile-final.png` records the responsive view. A P2 multi-line mode-summary squeeze was fixed by giving it a separate mobile row, then the phone view was reloaded and checked again.

## Required fidelity surfaces

- **Fonts/typography:** system serif headings/wordmark and sans-serif controls retain the chosen hierarchy; exact code uses readable monospace. No clipped essential labels. System font metrics differ slightly from the generated target (P3).
- **Spacing/layout:** dark project/history rail, broad task composer, amber primary action, pinned result bar and paired source columns follow the selected structure. Mobile uses a top navigation, two-column task choices and stacked source panels. Original-request disclosure and source identity footers intentionally add useful inspection space.
- **Colors/tokens:** graphite surfaces, warm text, muted secondary copy, amber selection/action and visible keyboard outlines. The implementation uses flat surfaces instead of the mock's subtle texture/elevation (P3).
- **Assets/image quality:** original MIT Heroicons outline assets are bundled locally with their notice. Wordmark is editable text, as in the target; there are no raster content assets to approximate or stretch. Icon shapes differ slightly from the generated mock (P3).
- **Copy/content:** real saved jobs replace invented recent activities. Current date advances to November 5 while the selected mock is dated November 4; fixture logs remain explicitly historical/synthetic. Evidence is the actual captured fixture text with exact hashes and horizontal source scrolling. Model notes remain separate and unverified; no fabricated accuracy/usage/savings is shown. Plain code lacks decorative syntax highlighting (P3).

## Interaction evidence

Actual browser checks: authenticated launch, evidence-only preparation, installed inventory refresh, explicit candidate selection/acknowledgement, a real bounded local-model attempt, visible timeout/abstention, successful unverified notes, retained model choice after service restart, Local AI off, pinned result/request identity, copy, JSON export and recent-history navigation. The actual downloaded JSON was read back and matched its pinned job/source. The browser download-event wait itself timed out after the file had been created; file readback, not that wait, is the export evidence.

Native keyboard arrows changed task selection; Tab moved from the task group to the request field. Phone history/Workspace navigation and responsive controls worked. Final browser warning/error log was empty. Backend negative tests cover authorization, scope, cancellation, response validation and connection bounds separately; they are not accessibility or model-accuracy certification.

No actionable P0/P1/P2 visual issues remain in the tested states. Follow-up P3s: optional syntax highlighting, closer system-font metrics and small icon/surface polish. Formal assistive-technology audit, wider devices and actual host qualification remain separate work.
