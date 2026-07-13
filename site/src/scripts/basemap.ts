// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Whiten the positron basemap at load (Franck 2026-07-13): its grey-beige
// mid-tones compete with the grade dots. Near-white land, faded landcover,
// pale water — roads and labels keep their discreet grey. Paint-property
// overrides only, guarded by layer inspection: a style update upstream
// degrades to the stock look, never breaks the map.
export function whitenBasemap(map: any): void {
  const apply = () => {
    for (const layer of map.getStyle().layers ?? []) {
      try {
        if (layer.type === "background") {
          map.setPaintProperty(layer.id, "background-color", "#fcfcfb");
        } else if (layer.type === "fill" && /landcover|landuse|park|wood|grass|residential|sand|glacier/.test(layer.id)) {
          map.setPaintProperty(layer.id, "fill-opacity", 0.22);
        } else if (layer.type === "fill" && /water/.test(layer.id)) {
          map.setPaintProperty(layer.id, "fill-color", "#e9f1f7");
        }
      } catch { /* unknown layer/property — leave it as designed */ }
    }
  };
  if (map.isStyleLoaded()) apply();
  else map.once("load", apply);
}
