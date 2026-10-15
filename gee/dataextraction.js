
/********************************************************************
 * URBANIZATION–HEAT RESEARCH
 * PHASE 3: DATA COLLECTION, PREPROCESSING AND VALIDATION
 *
 * Cities: Delhi, Kolkata, Chennai, Bengaluru, Hyderabad
 * Years: 2015–2025
 * Season: March 1 – June 30
 * Grid: Existing 300 m FeatureCollections
 *
 * Exports: 15 CSV tasks (3 batches x 5 cities)
 * No raster exports.
 ********************************************************************/


// ================================================================
// 1. CONFIGURATION
// ================================================================

var BASE = 'projects/testing-503015/assets/';

var CITIES = [
  'Delhi',
  // 'Kolkata',
  // 'Chennai',
  // 'Bengaluru',
  // 'Hyderabad'
];

// Three export batches.
var YEAR_BATCHES = [
  [2015, 2018],
  [2019, 2022],
  [2023, 2025]
];

// March 1 inclusive; July 1 exclusive.
var START_MONTH = 3;
var END_MONTH = 7;

// Nominal processing scales.
var THERMAL_SCALE = 100;
var REFLECTANCE_SCALE = 30;

var EXPORT_FOLDER = 'UrbanHeat_Phase3';

var L8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2');
var L9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2');


// ================================================================
// 2. LANDSAT PREPROCESSING
// ================================================================

function preprocess(image) {
  var qa = image.select('QA_PIXEL');
  var saturation = image.select('QA_RADSAT');

  // Mask fill, dilated cloud, cirrus, cloud,
  // cloud shadow and snow.
  var qaMask = qa.bitwiseAnd(1 << 0).eq(0)
    .and(qa.bitwiseAnd(1 << 1).eq(0))
    .and(qa.bitwiseAnd(1 << 2).eq(0))
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  // Conservative saturation mask.
  var saturationMask = saturation.eq(0);

  // Landsat Collection 2 Level-2 surface reflectance.
  var red = image.select('SR_B4')
    .multiply(0.0000275)
    .add(-0.2);

  var nir = image.select('SR_B5')
    .multiply(0.0000275)
    .add(-0.2);

  var swir1 = image.select('SR_B6')
    .multiply(0.0000275)
    .add(-0.2);

  // NDVI.
  var ndviDenominator = nir.add(red);

  var ndvi = nir.subtract(red)
    .divide(ndviDenominator)
    .rename('NDVI')
    .updateMask(ndviDenominator.abs().gt(0.001));

  // NDBI.
  var ndbiDenominator = swir1.add(nir);

  var ndbi = swir1.subtract(nir)
    .divide(ndbiDenominator)
    .rename('NDBI')
    .updateMask(ndbiDenominator.abs().gt(0.001));

  // Landsat surface temperature:
  // Kelvin = ST_B10 * 0.00341802 + 149.
  // Convert to Celsius.
  var lstC = image.select('ST_B10')
    .multiply(0.00341802)
    .add(149.0)
    .subtract(273.15)
    .rename('LST_C');

  // Common validity mask for comparable observations.
  var commonMask = qaMask
    .and(saturationMask)
    .and(ndvi.mask())
    .and(ndbi.mask())
    .and(lstC.mask());

  var output = lstC
    .addBands(ndvi)
    .addBands(ndbi)
    .updateMask(commonMask);

  return output.copyProperties(image, [
    'system:time_start',
    'SPACECRAFT_ID',
    'LANDSAT_PRODUCT_ID'
  ]);
}


// ================================================================
// 3. PROCESS ONE CITY AND YEAR
// ================================================================

function processCityYear(city, year, grid, geometry) {
  var start = ee.Date.fromYMD(year, START_MONTH, 1);
  var end = ee.Date.fromYMD(year, END_MONTH, 1);

  var l8 = L8
    .filterBounds(geometry)
    .filterDate(start, end);

  var l9 = L9
    .filterBounds(geometry)
    .filterDate(start, end);

  var nL8 = l8.size();
  var nL9 = l9.size();

  var raw = l8.merge(l9);
  var processed = raw.map(preprocess);

  // Seasonal pixel-wise median.
  var composite = processed
    .select(['LST_C', 'NDVI', 'NDBI'])
    .median();

  // Number of jointly valid observations per pixel.
  var nObs = processed
    .select('LST_C')
    .count()
    .rename('n_obs');

  // --------------------------------------------------------------
  // 3A. Thermal summary and observation counts.
  // --------------------------------------------------------------

  var thermalStack = composite
    .select('LST_C')
    .addBands(nObs);

  var thermalStats = thermalStack.reduceRegions({
    collection: grid,
    reducer: ee.Reducer.mean(),
    scale: THERMAL_SCALE,
    tileScale: 4
  });

  // --------------------------------------------------------------
  // 3B. NDVI and NDBI summaries.
  // --------------------------------------------------------------

  var indexStats = composite
    .select(['NDVI', 'NDBI'])
    .reduceRegions({
      collection: grid,
      reducer: ee.Reducer.mean(),
      scale: REFLECTANCE_SCALE,
      tileScale: 4
    });

  // --------------------------------------------------------------
  // 3C. Join the two summaries using grid_id.
  // --------------------------------------------------------------

  var joinCondition = ee.Filter.equals({
    leftField: 'grid_id',
    rightField: 'grid_id'
  });

  var joined = ee.FeatureCollection(
    ee.Join.saveFirst('index_feature').apply({
      primary: thermalStats,
      secondary: indexStats,
      condition: joinCondition
    })
  );

  // Preserve one output row per grid cell, including missing values.
  var output = joined.map(function(feature) {
    var indexFeature = ee.Feature(
      feature.get('index_feature')
    );

    return ee.Feature(null, {
      grid_id: feature.get('grid_id'),
      city_id: feature.get('city_id'),
      city: city,
      year: year,

      lst_c: feature.get('LST_C'),
      ndvi: indexFeature.get('NDVI'),
      ndbi: indexFeature.get('NDBI'),

      n_obs_mean: feature.get('n_obs'),

      // Scene counts are before pixel-level masking.
      l8_scenes: nL8,
      l9_scenes: nL9,

      sensor_mix: ee.Algorithms.If(
        nL9.gt(0),
        'Landsat 8 + Landsat 9',
        ee.Algorithms.If(
          nL8.gt(0),
          'Landsat 8',
          'No scenes'
        )
      )
    });
  });

  return output;
}


// ================================================================
// 4. CREATE BATCHED CSV EXPORTS
// ================================================================

CITIES.forEach(function(city) {
  var region = ee.FeatureCollection(
    BASE + 'district_buffer/' +
    city + '_District_Buffer'
  );

  var grid = ee.FeatureCollection(
    BASE + 'grid/' +
    city + '_Grid_300m'
  );

  var geometry = region.geometry();

  print(city + ' grid cell count:', grid.size());

  YEAR_BATCHES.forEach(function(batch) {
    var firstYear = batch[0];
    var lastYear = batch[1];

    var annualTables = [];

    for (
      var year = firstYear;
      year <= lastYear;
      year++
    ) {
      annualTables.push(
        processCityYear(city, year, grid, geometry)
      );
    }

    var batchTable = ee.FeatureCollection(
      annualTables[0]
    );

    for (var i = 1; i < annualTables.length; i++) {
      batchTable = batchTable.merge(annualTables[i]);
    }

    var batchName = firstYear + '_' + lastYear;

    print(
      city + ' ' + batchName + ' row count:',
      batchTable.size()
    );

    Export.table.toDrive({
      collection: batchTable,
      description: 'UrbanHeat_' + city + '_' + batchName,
      folder: EXPORT_FOLDER,
      fileNamePrefix: city + '_cell_year_' + batchName,
      fileFormat: 'CSV',
      selectors: [
        'grid_id',
        'city_id',
        'city',
        'year',
        'lst_c',
        'ndvi',
        'ndbi',
        'n_obs_mean',
        'l8_scenes',
        'l9_scenes',
        'sensor_mix'
      ]
    });
  });
});


// ================================================================
// 5. VALIDATION: DELHI, 2015
// ================================================================

var validationRegion = ee.FeatureCollection(
  BASE + 'district_buffer/Delhi_District_Buffer'
);

var validationGeometry = validationRegion.geometry();

var validationStart = ee.Date.fromYMD(2015, 3, 1);
var validationEnd = ee.Date.fromYMD(2015, 7, 1);

var validationRaw = L8
  .filterBounds(validationGeometry)
  .filterDate(validationStart, validationEnd)
  .merge(
    L9.filterBounds(validationGeometry)
      .filterDate(validationStart, validationEnd)
  );

var validationProcessed = validationRaw.map(preprocess);

var validationComposite = validationProcessed
  .select(['LST_C', 'NDVI', 'NDBI'])
  .median()
  .clip(validationGeometry);

var validationObs = validationProcessed
  .select('LST_C')
  .count()
  .rename('n_obs')
  .clip(validationGeometry);

print('Validation city:', 'Delhi');
print('Validation year:', 2015);
print('Validation scene count:', validationRaw.size());

print(
  'Delhi 2015 LST statistics (°C):',
  validationComposite.select('LST_C').reduceRegion({
    reducer: ee.Reducer.minMax()
      .combine(ee.Reducer.mean(), '', true),
    geometry: validationGeometry,
    scale: THERMAL_SCALE,
    maxPixels: 1e8,
    tileScale: 4
  })
);

print(
  'Delhi 2015 NDVI statistics:',
  validationComposite.select('NDVI').reduceRegion({
    reducer: ee.Reducer.minMax()
      .combine(ee.Reducer.mean(), '', true),
    geometry: validationGeometry,
    scale: REFLECTANCE_SCALE,
    maxPixels: 1e8,
    tileScale: 4
  })
);

print(
  'Delhi 2015 NDBI statistics:',
  validationComposite.select('NDBI').reduceRegion({
    reducer: ee.Reducer.minMax()
      .combine(ee.Reducer.mean(), '', true),
    geometry: validationGeometry,
    scale: REFLECTANCE_SCALE,
    maxPixels: 1e8,
    tileScale: 4
  })
);

Map.centerObject(validationRegion, 9);

Map.addLayer(
  validationComposite.select('LST_C'),
  {
    min: 20,
    max: 50,
    palette: [
      '313695', '74add1', 'ffffbf',
      'f46d43', 'a50026'
    ]
  },
  'Delhi 2015 LST Celsius'
);

Map.addLayer(
  validationComposite.select('NDVI'),
  {
    min: -0.2,
    max: 0.8,
    palette: ['brown', 'yellow', 'green']
  },
  'Delhi 2015 NDVI',
  false
);

Map.addLayer(
  validationComposite.select('NDBI'),
  {
    min: -0.5,
    max: 0.5,
    palette: ['2166ac', 'f7f7f7', 'b2182b']
  },
  'Delhi 2015 NDBI',
  false
);

Map.addLayer(
  validationObs,
  {
    min: 0,
    max: 20,
    palette: ['red', 'yellow', 'green']
  },
  'Delhi 2015 valid observations',
  false
);

print('Script configured. Review the 15 export tasks before starting.');
