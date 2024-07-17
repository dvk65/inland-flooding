# Report
This document includes the analysis and discussion about flood event data and satellite imagery data.

## Flood Event Data

### STN
The cleaned STN flood event dataset has 889 instances. Below is a summary of this dataset.
```
Number of Unique Values in Each Attribute:
 id           889
event          5
state          6
county        28
latitude     863
longitude    860
```

As we can see, there're five events. They're `2023 July MA NY VT Flood`, `2018 March Extratropical Cyclone`, `2018 January Extratropical Cyclone`, `2023 December East Coast Cyclone`, and `2021 Henri`. Below is the number of flood events in each category. `2023 July MA NY VT Flood` has the largest number of flood events.
```
Flood Events Group By event:
                                     total_count
event
2023 July MA NY VT Flood                    641
2018 March Extratropical Cyclone            115
2018 January Extratropical Cyclone           81
2023 December East Coast Cyclone             43
2021 Henri                                    9
```

The figure below illustrates the distribution of STN flood events. Vermont (2023 July MA NY VT Flood) has the largest number of flood events.
![STN Flood Event Distribution](./figs/stn_event_count.png)

### Gauge
In this project, I also collected the gauge water level data. Combining this dataset with STN dataset might help us better analyze and understand the flood events. Below is an overview of the cleaned dataset.
```
Number of Unique Values in Each Attribute:
 id           262
event         33
event_day    108
state          6
county        36
latitude      75
longitude     75
```

### STN and Gauge Overlap
I checked on the flood events documented by both sources. They are:
```
['2018-01' '2021-08' '2023-07' '2023-12']
```

The figure below illustrates the distribution of gauge flood events. Vermont (2023-07) has the largest number of flood events.
![Gauge Flood Event Distribution](./figs/gauge_event_count.png)

To understand the locations of flood events, I created a map for each state. Below is the flood events in Vermont.
![Vermont Flood Event Map](./figs/VT_flood_event_map.png)

## Satellite Imagery Data (Sentinel 2)