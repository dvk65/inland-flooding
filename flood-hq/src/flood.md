---
theme: dashboard
toc: false
title: Flood data
---
<!-- to make the plot span length of the window -->

# Flood data

```js
const flood = FileAttachment("./data/preprocessed.csv").csv();
```

```js
function floodPlot(data, {width} = {}) {

  const stateNames = {
    "NH" : "New Hampshire",
    "VT" : "Vermont",
    "MA" : "Massachusetts",
    "CT" : "Connecticut",
  };

  const sumfloodclusters = Array.from(
    d3.rollup(
      data,
      (v) => d3.sum(v, (d) => d.flooded_cluster_default),
      (d) => d.state
    ),
    ([state, totalClusters]) => ({ state, totalClusters })
  );

  return Plot.plot({
    title: "Flood clusters by state",
    width,
    x: {type: "band", domain: sumfloodclusters.map(d => d.state), label: "State" },
    y: {grid: true, inset: 10, label: "Total Flood Clusters"},
    marks: [
      Plot.barY(sumfloodclusters, {
        x: "state",
        y: "totalClusters",
        fill: "steelblue",
        title: (d) => `${stateNames[d.state] || d.state} : ${d.totalClusters} clusters`
        }
          )
        ]
      })
  };
```

<!-- ```js
display(floodPlot(flood));
``` -->

<!-- grid makes plots resizable -->
<div class="grid grid-cols-1">
  <div class="card">${resize((width) => floodPlot(flood, {width}))}</div>
</div>