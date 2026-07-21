[out:json][timeout:90];
(
  way["railway"="subway"](43.054916388,141.349592632,43.070980841,141.356913521);
  way["railway"]["tunnel"](43.054916388,141.349592632,43.070980841,141.356913521);
  nw["railway"="subway_entrance"](43.054916388,141.349592632,43.070980841,141.356913521);
  nw["railway"="station"]["station"="subway"](43.054916388,141.349592632,43.070980841,141.356913521);
  nw["public_transport"="platform"]["subway"="yes"](43.054916388,141.349592632,43.070980841,141.356913521);
  way["highway"~"^(footway|pedestrian|corridor|steps)$"]["tunnel"](43.054916388,141.349592632,43.070980841,141.356913521);
  way["highway"~"^(footway|pedestrian|corridor|steps)$"]["indoor"](43.054916388,141.349592632,43.070980841,141.356913521);
  way["highway"~"^(footway|pedestrian|corridor|steps)$"]["level"](43.054916388,141.349592632,43.070980841,141.356913521);
  way["highway"~"^(footway|pedestrian|corridor|steps)$"]["layer"~"^-"](43.054916388,141.349592632,43.070980841,141.356913521);
);
out meta geom;
