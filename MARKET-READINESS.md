# Terrain Environmental GIS — Market Readiness

## Working in the current free market preview

- Guided **Define → Analyze → Review → Report** workflow.
- Import GeoJSON, KML, KMZ, GPX, CSV, and zipped Shapefile data.
- Draw/edit points, lines, rectangles, and polygons in-browser.
- Automatic project acreage, perimeter, line-distance, and point counts.
- USGS topo, imagery, imagery+topo, and shaded-relief basemaps.
- Representative USGS elevation/slope/aspect screening.
- One-click project screening against public CAL FIRE/OSFM historical fire, Fire Hazard Severity Zone, State Responsibility Area, and USGS HUC10 watershed services.
- Plain-language findings with visible data provenance and limitations.
- Professional print/PDF-ready screening report with project-boundary schematic and source table.
- GeoJSON, KML, and GPX export.
- Read-only share links for projects small enough to encode safely in a URL; shared snapshots are compacted and do not include full agency geometries.
- Local browser autosave; no paid API key, account, or database required.
- Installable PWA shell and same-origin app-shell caching. This is not full offline map/data support.
- Public proof demo for external evaluation.

## Not yet represented as production-ready

The current static preview deliberately does **not** claim these features are working:

- User accounts, password recovery, SSO, or organization workspaces.
- Encrypted cloud project storage or cross-device sync.
- Role-based access control, audit logs, organization administration, or retention policies.
- Durable server-hosted project links for very large datasets.
- Full offline basemap/environmental-data packages.
- Geotagged photo/audio/video field attachments and conflict-aware sync.
- Survey-grade terrain analysis, full-resolution DEM/LiDAR processing, or acreage-by-slope-class calculations.
- Parcel/title/legal ownership determinations.
- Automated regulatory or environmental compliance determinations.
- Guaranteed uptime for third-party government GIS services.
- Enterprise security attestations, contractual SLA, or compliance certifications.

## Recommended production infrastructure phase

1. Add an authenticated backend and database/object storage for projects and attachments.
2. Add organization/workspace roles, invitations, audit history, and read-only/public share permissions.
3. Move shared projects from URL-encoded snapshots to short server-backed project IDs.
4. Bundle/pin critical front-end dependencies and add automated browser/integration tests.
5. Add error monitoring, service-health checks, dataset metadata refresh, and source-version alerts.
6. Add offline field packages and attachment sync without violating basemap/data-provider terms.
7. Add full DEM/LiDAR processing for slope/aspect/elevation statistics when an appropriate data-processing architecture is available.
8. Add professionally reviewed Privacy Policy, Terms, accessibility review, security controls, and agency/professional-use disclaimers before paid production launch.

## Product positioning

Do not market this as a replacement for ArcGIS. Position it as **environmental project intelligence that removes common GIS workflow friction**:

**Import or draw a project area → run screening → review plain-language findings → generate/share a professional project package.**
