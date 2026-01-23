import Chart from 'chart.js/auto'

(async function() {

  const bgPattern = function() {
    let shape = document.createElement('canvas');
    shape.width = 2;
    shape.height = 2;
    let c = shape.getContext('2d');

    let b = c.createImageData(1,1);
    b.data[0] = 0;
    b.data[1] = 0;
    b.data[2] = 0;
    b.data[3] = 255;

    let w = c.createImageData(1,1);
    w.data[0] = 255;
    w.data[1] = 255;
    w.data[2] = 255;
    w.data[3] = 255;

    c.putImageData(b, 0, 0);
    c.putImageData(w, 1, 0);
    c.putImageData(w, 0, 1);
    c.putImageData(b, 1, 1);

    return c.createPattern(shape, 'repeat')
  }

  Chart.defaults.font.size = 14;
  Chart.defaults.font.family = 'Tahoma, sans-serif';
  Chart.defaults.color = '#000';

  const canvas = document.getElementById('graph-data');
  const canvas_parent = canvas.parentNode;
  // This does not handle resizing but should be fine
  const parent_styles = getComputedStyle(canvas_parent);
  const hz_padding = parseInt(parent_styles.paddingLeft) + parseInt(parent_styles.paddingRight);
  const vt_padding = parseInt(parent_styles.paddingTop) + parseInt(parent_styles.paddingBottom);
  const parent_width = canvas_parent.clientWidth - hz_padding;
  const parent_height = canvas_parent.clientHeight - vt_padding;
  canvas.width = parent_width;
  canvas.height = parent_height;

  new Chart(
    canvas,
    {
      type: 'bar',
      options: {
        devicePixelRatio: 1,
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: false
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              minRotation: 0,
              maxRotation: 0,
            },
            border: {
              color: '#000',
              width: 2
            }
          },
          yTemp: {
            position: 'left',
            grid: {
              display: false,
            },
            border: {
              display: false,
            },
            ticks: {
              callback: (v, i, t) => v.toFixed(0) + '°',
              count: 11,
              autoSkip: false,
            }
          },
          yPercent: {
            position: 'right',
            ticks: {
              callback: (v, i, t) => v.toFixed(0) + '%',
              stepSize: 10,
              autoSkip: false,
            },
            min: 0,
            max: 100,
            grid: {
              color: '#000',
              dash: [2],
              drawTicks: false,
            },
            border: {
              color: '#000',
              dash: [1, 3],
              width: 0,
            }
          }
        }
      },
      data: {
        labels: window.graph_data.map(row => row.label),
        datasets: [
          {
            type: 'line',
            label: 'Temperature',
            data: window.graph_data.map(row => row.temp),
            yAxisID: 'yTemp',
            pointStyle: false,
            borderColor: js_color('.openweather.graph.temperature', 'color'),
            borderWidth: 2,
            order: 1,
          },
          {
            type: 'bar',
            label: 'Precipitation',
            data: window.graph_data.map(row => row.precip * 100),
            yAxisID: 'yPercent',
            backgroundColor: js_color('.openweather.graph.precipitation', 'color', bgPattern()),
            order: 2,
          },
          {
            type: 'line',
            label: 'Humidity',
            data: window.graph_data.map(row => row.humid * 100),
            yAxisID: 'yPercent',
            showLine: false,
            pointBackgroundColor: js_color('.openweather.graph.humidity', 'background-color', '#fff'),
            pointBorderColor: js_color('.openweather.graph.humidity', 'color'),
            order: 0,
          },
        ]
      }
    }
  );
})();
