
/********************************************************************
 * URBANIZATION–HEAT RESEARCH
 * PHASE 3: DATA COLLECTION — ALTERNATIVE RASTER WORKFLOW
 *
 * Cities: Delhi, Kolkata, Chennai, Bengaluru, Hyderabad
 * Years: 2015–2025
 * Seasons: March–May (primary), March–June (robustness)
 * Min observations per pixel: 3
 * Resolution: 30 m (Landsat native)
 * Source boundaries: District + 5 km buffer (Phase 2.2 output)
 *
 * Exports: 10 GeoTIFF tasks (2 seasons × 5 cities)
 * Each GeoTIFF: 44 bands (11 years × [LST_C, NDVI, NDBI, OBS])
 ********************************************************************/

var cities = [
  {
    name: 'Delhi',
    asset: 'projects/testing-503015/assets/Delhi_District_Buffer'
  },
  {
    name: 'Kolkata',
    asset: 'projects/testing-503015/assets/Kolkata_District_Buffer'
  },
  {
    name: 'Chennai',
    asset: 'projects/testing-503015/assets/Chennai_District_Buffer'
  },
  {
    name: 'Bengaluru',
    asset: 'projects/testing-503015/assets/Bengaluru_District_Buffer'
  },
  {
    name: 'Hyderabad',
    asset: 'projects/testing-503015/assets/Hyderabad_District_Buffer'
  }
];

var startYear = 2015;
var endYear = 2025;
var minObservations = 3;

// Landsat 8 and Landsat 9, Collection 2 Level 2.
var landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'));

// Cloud masking and calculation of LST, NDVI and NDBI.
function prepareImage(image) {
  var qa = image.select('QA_PIXEL');

  var mask = qa.bitwiseAnd(1 << 0).eq(0)  // Fill
    .and(qa.bitwiseAnd(1 << 1).eq(0))     // Dilated cloud
    .and(qa.bitwiseAnd(1 << 2).eq(0))     // Cirrus
    .and(qa.bitwiseAnd(1 << 3).eq(0))     // Cloud
    .and(qa.bitwiseAnd(1 << 4).eq(0))     // Cloud shadow
    .and(qa.bitwiseAnd(1 << 5).eq(0))     // Snow
    .and(image.select('QA_RADSAT').eq(0));

  // Convert surface reflectance to physical values.
  var optical = image.select(['SR_B4', 'SR_B5', 'SR_B6'])
    .multiply(0.0000275)
    .add(-0.2);

  var ndvi = optical.normalizedDifference(
    ['SR_B5', 'SR_B4']
  ).rename('NDVI');

  var ndbi = optical.normalizedDifference(
    ['SR_B6', 'SR_B5']
  ).rename('NDBI');

  // Convert surface temperature to degrees Celsius.
  var lst = image.select('ST_B10')
    .multiply(0.00341802)
    .add(149.0)
    .subtract(273.15)
    .rename('LST_C');

  return ee.Image.cat([lst, ndvi, ndbi])
    .updateMask(mask)
    .copyProperties(image, ['system:time_start']);
}


// Generate an annual multi-band stack for one city and period.
function exportAnnualStack(city, boundary, periodName, endMonth) {
  var stack = ee.Image([]);

  for (var year = startYear; year <= endYear; year++) {
    var startDate = year + '-03-01';
    var endDate = year + '-' + endMonth + '-01';

    var collection = landsat
      .filterBounds(boundary)
      .filterDate(startDate, endDate)
      .map(prepareImage);

    var median = collection.median();

    // Use the native projection of an actual Landsat image.
    var nativeProjection = ee.Image(collection.first())
      .select('LST_C')
      .projection();

    median = median.setDefaultProjection(nativeProjection);

    // Number of valid observations at each pixel.
    var observationCount = collection
      .select('LST_C')
      .count()
      .setDefaultProjection(nativeProjection);

    var enoughObservations = observationCount.gte(minObservations);

    // Mask measurements where fewer than 3 observations exist.
    var lst = median.select('LST_C')
      .updateMask(enoughObservations)
      .rename('LST_C_' + year);

    var ndvi = median.select('NDVI')
      .updateMask(enoughObservations)
      .rename('NDVI_' + year);

    var ndbi = median.select('NDBI')
      .updateMask(enoughObservations)
      .rename('NDBI_' + year);

    // Keep observation counts unmasked for quality assessment.
    var countBand = observationCount
      .rename('OBS_' + year);

    var annualBands = ee.Image.cat([
      lst, ndvi, ndbi, countBand
    ]);

    stack = stack.addBands(annualBands);
  }

  stack = stack.toFloat().clip(boundary);

  print(
    city.name + ' ' + periodName + ' output bands:',
    stack.bandNames()
  );

  Export.image.toDrive({
    image: stack,
    description: city.name + '_' + periodName + '_2015_2025',
    folder: 'GEE_Temporal_Exports',
    fileNamePrefix: city.name + '_' + periodName + '_2015_2025',
    region: boundary,
    scale: 30,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
}


// Process all five cities.
cities.forEach(function(city) {
  var boundary = ee.FeatureCollection(city.asset).geometry();

  // Primary analysis: March-May.
  exportAnnualStack(city, boundary, 'Mar_May', '06');

  // Robustness analysis: March-June.
  exportAnnualStack(city, boundary, 'Mar_Jun', '07');
});