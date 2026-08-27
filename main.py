/*
====================================================================
Assignment II: NDVI vs SAVI Analysis -- FULL APP VERSION
Includes: scene selection, index calculation, statistics, exports,
AND a polished map UI (title, info panel, legend, layer selector)
suitable for publishing as a GEE App.
====================================================================
*/

// ================================================================
// 1. AOI
// ================================================================
var aoi = ee.FeatureCollection('projects/ee2-iirs04nidhi/assets/project_areashp');
var aoiGeom = aoi.geometry();

Map.centerObject(aoiGeom, 15);
Map.setOptions('SATELLITE');

// ================================================================
// 2. Select the best (least cloudy) image FIRST, on the raw
//    collection, before any masking touches its properties.
// ================================================================
var rawCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoiGeom)
  .filterDate('2026-02-01', '2026-03-01')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
  .sort('CLOUDY_PIXEL_PERCENTAGE');

var selectedRaw = rawCollection.first();

print('Selected image date:', selectedRaw.date());
print('Selected image PRODUCT_ID:', selectedRaw.get('PRODUCT_ID'));
print('Selected image CLOUDY_PIXEL_PERCENTAGE:', selectedRaw.get('CLOUDY_PIXEL_PERCENTAGE'));

// ================================================================
// 3. Scale to 0-1 reflectance and cloud-mask
// ================================================================
function maskAndScaleS2(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
              .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  var scaled = image.select(['B2', 'B3', 'B4', 'B8']).divide(10000);
  return ee.Image(scaled.updateMask(mask).copyProperties(image, image.propertyNames()));
}

var selectedImage = maskAndScaleS2(selectedRaw);

// ================================================================
// 4. Clip + lock in consistent projection/scale
// ================================================================
var multiband = selectedImage.clip(aoiGeom);
var targetProjection = multiband.select('B4').projection();
var targetScale = 10;
var crsCode = targetProjection.crs().getInfo();

multiband = multiband.reproject(targetProjection, null, targetScale);

// ================================================================
// 5. NDVI / SAVI
// ================================================================
var ndvi = multiband.normalizedDifference(['B8', 'B4']).rename('NDVI')
  .reproject(targetProjection, null, targetScale).clip(aoiGeom);

var L = 0.5;
var savi = multiband.expression(
  '((NIR - RED) / (NIR + RED + L)) * (1 + L)',
  {NIR: multiband.select('B8'), RED: multiband.select('B4'), L: L}
).rename('SAVI').reproject(targetProjection, null, targetScale).clip(aoiGeom);

var difference = ndvi.subtract(savi).rename('NDVI_minus_SAVI');

// ================================================================
// 6. Statistics (printed for report use)
// ================================================================
var statsReducer = ee.Reducer.mean()
  .combine({reducer2: ee.Reducer.minMax(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.stdDev(), sharedInputs: true});

print('NDVI statistics:', ndvi.reduceRegion({reducer: statsReducer, geometry: aoiGeom, scale: targetScale, maxPixels: 1e9}));
print('SAVI statistics:', savi.reduceRegion({reducer: statsReducer, geometry: aoiGeom, scale: targetScale, maxPixels: 1e9}));

// ================================================================
// 7. Visualization parameters
// ================================================================
var trueColorVis = {bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3, gamma: 1.4};
var indexVis = {
  min: -0.2, max: 0.9,
  palette: ['#a50026','#d73027','#f46d43','#fdae61','#fee08b',
            '#d9ef8b','#a6d96a','#66bd63','#1a9850','#006837']
};
var diffVis = {min: -0.3, max: 0.3, palette: ['#2166ac', '#f7f7f7', '#b2182b']};

// Boundary always visible
Map.addLayer(aoi.style({color: 'yellow', fillColor: '00000000', width: 2}), {}, 'AOI Boundary', true);

// Base layers -- start with only True Color on, others toggled by selector below
var layerTrueColor = ui.Map.Layer(multiband.visualize(trueColorVis), {}, 'True Color', true);
var layerNDVI = ui.Map.Layer(ndvi.visualize(indexVis), {}, 'NDVI', false);
var layerSAVI = ui.Map.Layer(savi.visualize(indexVis), {}, 'SAVI', false);
var layerDiff = ui.Map.Layer(difference.visualize(diffVis), {}, 'NDVI - SAVI Difference', false);

Map.layers().add(layerTrueColor);
Map.layers().add(layerNDVI);
Map.layers().add(layerSAVI);
Map.layers().add(layerDiff);

// ================================================================
// 8. APP UI -- Title panel (top-center)
// ================================================================
var titlePanel = ui.Panel({
  style: {position: 'top-center', padding: '8px 16px', backgroundColor: 'rgba(255,255,255,0.9)'}
});
titlePanel.add(ui.Label('NDVI vs SAVI Analysis Project \u2014  Banaskantha, Gujarat', {
  fontWeight: 'bold', fontSize: '18px', margin: '2px 0'
}));
titlePanel.add(ui.Label('Sentinel-2 | February 2026 | 59.66 ha', {
  fontSize: '12px', color: '555555', margin: '2px 0'
}));
Map.add(titlePanel);

// ================================================================
// 9. APP UI -- Info panel (top-right)
// ================================================================
var infoPanel = ui.Panel({
  style: {position: 'top-right', padding: '10px', width: '260px', backgroundColor: 'rgba(255,255,255,0.92)'}
});
infoPanel.add(ui.Label('About this map', {fontWeight: 'bold', fontSize: '14px'}));
infoPanel.add(ui.Label('Source: Sentinel-2 SR (COPERNICUS/S2_SR_HARMONIZED)', {fontSize: '11px'}));
infoPanel.add(ui.Label('Scene date: 15 Feb 2026 (cloud cover ~0.001%)', {fontSize: '11px'}));
infoPanel.add(ui.Label('Resolution: 10 m  |  CRS: ' + crsCode, {fontSize: '11px'}));
infoPanel.add(ui.Label('NDVI = (NIR-Red)/(NIR+Red)', {fontSize: '11px', color: '666666'}));
infoPanel.add(ui.Label('SAVI = [(NIR-Red)/(NIR+Red+L)]\u00d7(1+L), L=0.5', {fontSize: '11px', color: '666666'}));
Map.add(infoPanel);

// ================================================================
// 10. APP UI -- Layer selector (top-left): pick one layer to view
// ================================================================
var layerSelectPanel = ui.Panel({
  style: {position: 'top-left', padding: '8px 12px', backgroundColor: 'rgba(255,255,255,0.92)'}
});
layerSelectPanel.add(ui.Label('View Layer', {fontWeight: 'bold', fontSize: '13px'}));

var layerSelect = ui.Select({
  items: ['True Color', 'NDVI', 'SAVI', 'NDVI - SAVI Difference'],
  value: 'True Color',
  onChange: function(selected) {
    layerTrueColor.setShown(selected === 'True Color');
    layerNDVI.setShown(selected === 'NDVI');
    layerSAVI.setShown(selected === 'SAVI');
    layerDiff.setShown(selected === 'NDVI - SAVI Difference');
    legendPanel.clear();
    if (selected === 'NDVI' || selected === 'SAVI') {
      legendPanel.add(buildLegend(selected + ' Value', indexVis));
    } else if (selected === 'NDVI - SAVI Difference') {
      legendPanel.add(buildLegend('NDVI \u2212 SAVI', diffVis));
    } else {
      legendPanel.add(ui.Label('True color composite (no legend needed)', {fontSize: '11px', color: '888888'}));
    }
  }
});
layerSelectPanel.add(layerSelect);
Map.add(layerSelectPanel);

// ================================================================
// 11. APP UI -- Legend (bottom-left), rebuilt when layer changes
// ================================================================
function buildLegend(title, vis) {
  var panel = ui.Panel();
  panel.add(ui.Label(title, {fontWeight: 'bold', fontSize: '13px', margin: '0 0 4px 0'}));

  var lon = ee.Image.pixelLonLat().select('longitude');
  var gradient = lon.multiply((vis.max - vis.min) / 100.0).add(vis.min);
  var legendImage = gradient.visualize(vis);

  var thumb = ui.Thumbnail({
    image: legendImage,
    params: {bbox: [0, 0, 100, 10], dimensions: '220x18'},
    style: {stretch: 'horizontal', margin: '0px', maxHeight: '18px'}
  });
  panel.add(thumb);

  panel.add(ui.Panel({
    widgets: [
      ui.Label(vis.min.toString(), {margin: '2px 4px', fontSize: '11px'}),
      ui.Label('', {stretch: 'horizontal'}),
      ui.Label(((vis.min + vis.max) / 2).toFixed(2), {margin: '2px 4px', fontSize: '11px'}),
      ui.Label('', {stretch: 'horizontal'}),
      ui.Label(vis.max.toString(), {margin: '2px 4px', fontSize: '11px'})
    ],
    layout: ui.Panel.Layout.flow('horizontal')
  }));

  return panel;
}

var legendPanel = ui.Panel({
  style: {position: 'bottom-left', padding: '8px 15px', backgroundColor: 'rgba(255,255,255,0.92)'}
});
legendPanel.add(ui.Label('True color composite (no legend needed)', {fontSize: '11px', color: '888888'}));
Map.add(legendPanel);

// ================================================================
// 12. Sample points (for pixel-level report interpretation)
// ================================================================
var samplePoints = ndvi.addBands(savi).sample({
  region: aoiGeom, scale: targetScale, numPixels: 30, geometries: true
});
print('Sample points (NDVI & SAVI) for pixel-level interpretation:', samplePoints);

// ================================================================
// 13. Exports (GeoTIFF + PNG deliverables)
// ================================================================
Export.image.toDrive({
  image: multiband, description: 'Multiband_S2_Feb2026', folder: 'Equilibrium_Assignment_II',
  fileNamePrefix: 'multiband_raster', region: aoiGeom, scale: targetScale, crs: crsCode, maxPixels: 1e9
});
Export.image.toDrive({
  image: ndvi, description: 'NDVI_Feb2026', folder: 'Equilibrium_Assignment_II',
  fileNamePrefix: 'NDVI', region: aoiGeom, scale: targetScale, crs: crsCode, maxPixels: 1e9
});
Export.image.toDrive({
  image: savi, description: 'SAVI_Feb2026', folder: 'Equilibrium_Assignment_II',
  fileNamePrefix: 'SAVI', region: aoiGeom, scale: targetScale, crs: crsCode, maxPixels: 1e9
});
Export.image.toDrive({
  image: ndvi.visualize(indexVis), description: 'NDVI_Map_PNG', folder: 'Equilibrium_Assignment_II',
  fileNamePrefix: 'NDVI_map', region: aoiGeom, scale: targetScale, crs: crsCode, maxPixels: 1e9
});
Export.image.toDrive({
  image: savi.visualize(indexVis), description: 'SAVI_Map_PNG', folder: 'Equilibrium_Assignment_II',
  fileNamePrefix: 'SAVI_map', region: aoiGeom, scale: targetScale, crs: crsCode, maxPixels: 1e9
});

// ================================================================
// 14. Thumbnail links (console only, for your written report)
// ================================================================
print('=== THUMBNAIL PREVIEWS (for report use) ===');
print('True Color:', multiband.getThumbURL({bands: ['B4','B3','B2'], min: 0, max: 0.3, gamma: 1.4, dimensions: 800, region: aoiGeom, format: 'png'}));
print('NDVI:', ndvi.getThumbURL({min: indexVis.min, max: indexVis.max, palette: indexVis.palette, dimensions: 800, region: aoiGeom, format: 'png'}));
print('SAVI:', savi.getThumbURL({min: indexVis.min, max: indexVis.max, palette: indexVis.palette, dimensions: 800, region: aoiGeom, format: 'png'}));

// ================================================================
