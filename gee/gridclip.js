/********************************************************************
 * URBANIZATION–HEAT RESEARCH
 * PHASE 2.3: ESTABLISH THE SPATIAL GRID
 *
 * Cities: Delhi, Kolkata, Chennai, Bengaluru, Hyderabad
 * Grid: 300 m × 300 m in EPSG:6933 (World Cylindrical Equal Area)
 * Source boundaries: District + 5 km buffer (Phase 2.2 output)
 *
 * Output: 5 Shapefile exports (one per city) with fields:
 *   - city_id
 *   - grid_id (city_X_Y from projected centroid)
 *   - in_frac (fraction of cell inside study boundary)
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

// Create a projection object at 300 m scale.
var epsg6933Wkt =
  'PROJCS["WGS 84 / World Cylindrical Equal Area",' +
  'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],' +
  'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],' +
  'PROJECTION["Cylindrical_Equal_Area"],' +
  'PARAMETER["standard_parallel_1",30],' +
  'PARAMETER["central_meridian",0],' +
  'PARAMETER["false_easting",0],' +
  'PARAMETER["false_northing",0],' +
  'UNIT["m",1]]';

var projection = ee.Projection(epsg6933Wkt).atScale(300);

cities.forEach(function(city) {
  var boundaryFC = ee.FeatureCollection(city.asset);
  var boundary = boundaryFC.geometry();

  // Transform the boundary to the grid projection.
  boundary = boundary.transform(projection, 1);

  // Generate grid cells.
  var grid = boundary.coveringGrid(projection);

  var result = grid.map(function(cell) {
    var geom = cell.geometry();

    var totalArea = geom.area(1, projection);

    var clipped = geom.intersection(
      boundary,
      ee.ErrorMargin(1),
      projection
    );

    var insideArea = clipped.area(1, projection);

    var fraction = insideArea.divide(totalArea)
      .max(0)
      .min(1);

    // Generate a reproducible ID from projected coordinates.
    var coords = geom.centroid(1, projection).coordinates();

    var x = ee.Number(coords.get(0)).round().format('%.0f');
    var y = ee.Number(coords.get(1)).round().format('%.0f');

    return cell.set({
      city_id: city.name,
      grid_id: ee.String(city.name).cat('_').cat(x).cat('_').cat(y),
      in_frac: fraction
    });
  }).filter(ee.Filter.gt('in_frac', 0));

  print(city.name + ' grid cell count:', result.size());
  print(city.name + ' sample cells:', result.limit(5));

  Export.table.toDrive({
    collection: result,
    description: city.name + '_Grid_300m',
    folder: 'GEE_Grid_Exports',
    fileNamePrefix: city.name + '_Grid_300m',
    fileFormat: 'SHP',
    selectors: ['city_id', 'grid_id', 'in_frac']
  });
});