/********************************************************************
 * URBANIZATION–HEAT RESEARCH
 * PHASE 2.2: DEFINE URBAN BOUNDARIES
 *
 * Cities: Delhi, Kolkata, Chennai, Bengaluru, Hyderabad
 * Source: FAO GAUL 2015 level-2 (district boundaries)
 * Method: District polygon + 5 km buffer
 *
 * Output: 5 assets in projects/testing-503015/assets/
 *   {City}_District_Buffer (FeatureCollection)
 * Visualization only — no exports. Run once to create assets.
 ********************************************************************/

var districts = ee.FeatureCollection('FAO/GAUL/2015/level2');

var cities = [
  {name: 'Delhi', state: 'Delhi', district: 'New Delhi'},
  {name: 'Kolkata', state: 'West Bengal', district: 'Kolkata'},
  {name: 'Chennai', state: 'Tamil Nadu', district: 'Chennai'},
  {name: 'Bengaluru', state: 'Karnataka', district: 'Bangalore Urban'},
  {name: 'Hyderabad', state: 'Telangana', district: 'Hyderabad'}
];

var india = districts.filter(
  ee.Filter.eq('ADM0_NAME', 'India')
);

cities.forEach(function(city) {
  var district = india
    .filter(ee.Filter.eq('ADM1_NAME', city.state))
    .filter(ee.Filter.eq('ADM2_NAME', city.district));

  print(city.name + ' district:', district);

  var buffer = district.geometry().buffer(5000);

  Map.addLayer(
    district.style({
      color: 'red',
      fillColor: '00000000',
      width: 2
    }),
    {},
    city.name + ' district'
  );

  Map.addLayer(
    ee.FeatureCollection([ee.Feature(buffer)]).style({
      color: 'blue',
      fillColor: '00000000',
      width: 2
    }),
    {},
    city.name + ' + 5 km buffer'
  );
});

Map.centerObject(india, 5);